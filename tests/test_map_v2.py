from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from map_v2 import MapV2Error, MapV2Lattice, main


TOY_MANIFEST = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "map_domains"
    / "toy"
    / "domain.json"
)


class FakeCompiler:
    def __init__(self, status: str = "compiled") -> None:
        self.status = status
        self.calls: list[tuple[Path, str, str, dict | None]] = []

    def compile(
        self,
        workspace_path: Path,
        story: str,
        target: str,
        kappa: dict | None = None,
    ) -> dict:
        self.calls.append((workspace_path, story, target, kappa))
        return {
            "status": self.status,
            "frontier": [] if self.status == "compiled" else ["admissible(example_obligation)"],
            "blocked": [],
            "admissible": [] if self.status == "compiled" else ["example_obligation"],
            "outputs": ["compile_target_output(example)"],
            "reports": {"compile": f"compile_target_status({story},{target},{self.status}).\n"},
        }


class FailingCompiler:
    def compile(
        self,
        workspace_path: Path,
        story: str,
        target: str,
        kappa: dict | None = None,
    ) -> dict:
        raise RuntimeError("validator wire failed")


class MapV2LatticeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="gas_map_v2_test_")
        self.state_dir = Path(self.tempdir.name) / "lattice"
        self.lattice = MapV2Lattice(self.state_dir)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def prepare(self, name: str, domain: str = "probe") -> None:
        self.lattice.declare_kappa(
            name,
            domain,
            {"preserve_claim": "the selected MAP target must preserve the authored claim"},
        )
        self.lattice.compute(name, compiler=FakeCompiler(status="partial"))

    def test_create_expand_fill_persists_lattice_and_authored_prolog(self) -> None:
        created = self.lattice.create("map_probe", "world", root="COGNITION")
        self.assertEqual(created["selected"], "COGNITION")

        expanded = self.lattice.expand("COGNITION", ["CLAIM", "EVIDENCE"])
        self.assertEqual(expanded["children"], ["COGNITION.CLAIM", "COGNITION.EVIDENCE"])
        self.prepare("COGNITION.CLAIM")
        self.lattice.fill(
            "COGNITION.CLAIM",
            ["slot(map_probe, premise, map_claim).", "edge(map_claim, produces, map_question)."],
        )

        source = self.lattice.workspace_path.read_text(encoding="utf-8")
        self.assertIn("map_subject(world,map_probe).", source)
        self.assertIn("% map_v2_node: COGNITION.CLAIM", source)
        self.assertIn("slot(map_probe, premise, map_claim).", source)
        self.assertIn("edge(map_claim, produces, map_question).", source)

        reopened = MapV2Lattice(self.state_dir)
        self.assertEqual(reopened.show("COGNITION.CLAIM")["status"], "filled")
        self.assertEqual(reopened.show("COGNITION.CLAIM")["griess"]["phase"], "build")
        self.assertEqual(reopened.next()["name"], "COGNITION.CLAIM")
        self.assertEqual(reopened.next()["reason"], "compile")

    def test_fill_rejects_rules_and_does_not_treat_content_as_proven(self) -> None:
        self.lattice.create("map_probe", "world")
        self.prepare("map_probe")
        with self.assertRaisesRegex(MapV2Error, "facts, not directives or rules"):
            self.lattice.fill("map_probe", ["unsafe(X) :- call(X)."])

        self.lattice.fill("map_probe", ["slot(map_probe, premise, claim)."])
        node = self.lattice.show("map_probe")
        self.assertEqual(node["status"], "filled")
        self.assertIsNone(node["certificate"])
        self.assertEqual(node["griess"]["phase"], "build")
        self.assertEqual(self.lattice.queue(), [{"name": "map_probe", "reason": "compile"}])

    def test_create_refuses_to_overwrite_an_existing_workspace(self) -> None:
        self.state_dir.mkdir(parents=True)
        workspace = self.state_dir / "workspace.pl"
        workspace.write_text("story(user_owned).\n", encoding="utf-8")

        with self.assertRaisesRegex(MapV2Error, "lattice already exists"):
            self.lattice.create("map_probe", "world")

        self.assertEqual(workspace.read_text(encoding="utf-8"), "story(user_owned).\n")

    def test_compile_delegates_to_adapter_and_records_scoped_certificate(self) -> None:
        self.lattice.create("map_probe", "story")
        self.prepare("map_probe")
        self.lattice.fill("map_probe", ["slot(map_probe, premise, claim)."])
        compiler = FakeCompiler(status="partial")

        packet = self.lattice.compile(compiler=compiler)

        self.assertEqual(
            compiler.calls,
            [
                (
                    self.lattice.workspace_path,
                    "map_probe",
                    "story",
                    self.lattice.show("map_probe")["griess"]["kappa"],
                )
            ],
        )
        self.assertEqual(packet["status"], "partial")
        self.assertEqual(packet["node"], "map_probe")
        self.assertEqual(packet["subject"], "map_probe")
        self.assertEqual(packet["target"], "story")
        self.assertEqual(packet["workspace"], str(self.lattice.workspace_path))
        self.assertTrue(packet["workspace_sha256"])
        self.assertTrue(packet["kappa_sha256"])
        self.assertEqual(packet["kappa_binding"], "domain_obligations")
        self.assertEqual(packet["griess_phase"], "soup")
        node = self.lattice.show("map_probe")
        self.assertEqual(node["certificate"]["status"], "partial")
        self.assertEqual(node["certificate"]["kappa_binding"], "domain_obligations")
        self.assertNotIn("node", node["certificate"])
        self.assertEqual(node["griess"]["phase"], "soup")
        self.assertEqual(
            self.lattice.queue(),
            [{"name": "map_probe", "reason": "retry_from_compiler_residue"}],
        )

    def test_combine_requires_current_compiled_certificates(self) -> None:
        self.lattice.create("map_probe", "world", root="ROOT")
        self.lattice.expand("ROOT", ["A", "B"])
        self.prepare("ROOT.A")
        self.prepare("ROOT.B")
        self.lattice.fill("ROOT.A", ["slot(map_probe, premise, claim_a)."])
        self.lattice.fill("ROOT.B", ["slot(map_probe, theme, claim_b)."])

        with self.assertRaisesRegex(MapV2Error, "missing_compile_certificate"):
            self.lattice.combine("ROOT.AB", ["ROOT.A", "ROOT.B"])

        compiler = FakeCompiler(status="compiled")
        self.lattice.compile("ROOT.A", compiler=compiler)
        self.lattice.compile("ROOT.B", compiler=compiler)
        combined = self.lattice.combine("ROOT.AB", ["ROOT.A", "ROOT.B"])

        self.assertEqual(combined["status"], "pattern_unproven")
        self.assertEqual(combined["griess_phase"], "pattern")
        self.assertEqual(self.lattice.show("ROOT.AB")["sources"], ["ROOT.A", "ROOT.B"])
        self.assertIn({"name": "ROOT.AB", "reason": "promote_pattern"}, self.lattice.queue())
        with self.assertRaisesRegex(MapV2Error, "must be filled"):
            self.lattice.compile("ROOT.AB", compiler=compiler)

        promoted = self.lattice.promote("ROOT.AB")
        self.assertEqual(promoted["griess_phase"], "implement")
        reified = self.lattice.reify("ROOT.AB")
        self.assertEqual(reified["griess_phase"], "derive")
        self.assertEqual(reified["ses_depth"], 1)

    def test_later_authored_fact_stales_an_earlier_certificate(self) -> None:
        self.lattice.create("map_probe", "world", root="ROOT")
        self.lattice.expand("ROOT", ["A", "B"])
        self.prepare("ROOT.A")
        self.prepare("ROOT.B")
        self.lattice.fill("ROOT.A", ["slot(map_probe, premise, claim_a)."])
        self.lattice.compile("ROOT.A", compiler=FakeCompiler())
        self.lattice.fill("ROOT.B", ["slot(map_probe, theme, claim_b)."])

        queue = self.lattice.queue()
        self.assertIn({"name": "ROOT.A", "reason": "reopen_after_workspace_change"}, queue)
        with self.assertRaisesRegex(MapV2Error, "stale_workspace_certificate"):
            self.lattice.combine("ROOT.AB", ["ROOT.A", "ROOT.B"])

        reopened = self.lattice.retry("ROOT.A")
        self.assertEqual(reopened["griess_phase"], "derive")
        history = self.lattice.show("ROOT.A")["griess"]["history"]
        self.assertTrue(any("ont invalidated -> derive" in entry for entry in history))

    def test_phase_guards_require_kappa_compute_build_verify_order(self) -> None:
        self.lattice.create("map_probe", "world")
        self.assertEqual(
            self.lattice.queue(), [{"name": "map_probe", "reason": "declare_kappa"}]
        )
        with self.assertRaisesRegex(MapV2Error, "requires Griess compute"):
            self.lattice.fill("map_probe", ["slot(map_probe, premise, claim)."])

        declared = self.lattice.declare_kappa(
            "map_probe", "case", {"evidence": "evidence is grounded"}
        )
        self.assertEqual(declared["phase"], "derive")
        compiler = FakeCompiler("partial")
        computed = self.lattice.compute("map_probe", compiler=compiler)
        self.assertEqual(computed["purpose"], "compute_constraints")
        self.assertEqual(computed["griess_phase"], "compute")
        self.assertEqual(
            compiler.calls,
            [
                (
                    self.lattice.workspace_path,
                    "map_probe",
                    "world",
                    self.lattice.show("map_probe")["griess"]["kappa"],
                )
            ],
        )
        self.assertIsNone(self.lattice.show("map_probe")["certificate"])
        self.lattice.fill("map_probe", ["slot(map_probe, premise, claim)."])
        compiled = self.lattice.compile("map_probe", compiler=FakeCompiler("compiled"))
        self.assertEqual(compiled["griess_phase"], "ont")
        self.assertEqual(self.lattice.show("map_probe")["griess"]["phase"], "ont")

    def test_validator_failure_persists_verify_and_can_retry_without_false_outcome(self) -> None:
        self.lattice.create("map_probe", "world")
        self.prepare("map_probe")
        self.lattice.fill("map_probe", ["slot(map_probe, premise, claim)."])

        with self.assertRaisesRegex(RuntimeError, "validator wire failed"):
            self.lattice.compile("map_probe", compiler=FailingCompiler())

        reopened = MapV2Lattice(self.state_dir)
        node = reopened.show("map_probe")
        self.assertEqual(node["griess"]["phase"], "verify")
        self.assertIsNone(node["certificate"])
        packet = reopened.compile("map_probe", compiler=FakeCompiler("compiled"))
        self.assertEqual(packet["griess_phase"], "ont")

    def test_soup_retry_recompute_and_revision_preserve_prior_facts(self) -> None:
        self.lattice.create("map_probe", "world")
        self.prepare("map_probe")
        original = ["slot(map_probe, premise, rejected_claim)."]
        repaired = ["slot(map_probe, premise, repaired_claim)."]
        self.lattice.fill("map_probe", original)
        self.lattice.compile("map_probe", compiler=FakeCompiler("partial"))

        retry = self.lattice.retry("map_probe")
        self.assertEqual(retry["griess_phase"], "derive")
        self.lattice.compute("map_probe", compiler=FakeCompiler("partial"))
        revised = self.lattice.revise("map_probe", repaired)
        self.assertEqual(revised["revision_count"], 1)
        packet = self.lattice.compile("map_probe", compiler=FakeCompiler("compiled"))

        node = self.lattice.show("map_probe")
        self.assertEqual(packet["griess_phase"], "ont")
        self.assertEqual(node["facts"], repaired)
        self.assertEqual(node["revisions"][0]["facts"], original)

    def test_retry_kappa_change_clears_old_compile_receipt(self) -> None:
        self.lattice.create("map_probe", "world")
        self.prepare("map_probe")
        self.lattice.fill("map_probe", ["slot(map_probe, premise, claim)."])
        self.lattice.compile("map_probe", compiler=FakeCompiler("partial"))
        old_digest = self.lattice.show("map_probe")["certificate"]["kappa_sha256"]

        self.lattice.retry("map_probe")
        changed = self.lattice.declare_kappa(
            "map_probe", "probe", {"stronger_claim": "the repaired claim must close"}
        )
        node = self.lattice.show("map_probe")

        self.assertNotEqual(changed["kappa_sha256"], old_digest)
        self.assertIsNone(node["certificate"])

    def test_combine_rejects_different_kappa_contexts(self) -> None:
        self.lattice.create("map_probe", "world", root="ROOT")
        self.lattice.expand("ROOT", ["A", "B"])
        self.prepare("ROOT.A", domain="domain_a")
        self.prepare("ROOT.B", domain="domain_b")
        self.lattice.fill("ROOT.A", ["slot(map_probe, premise, claim_a)."])
        self.lattice.fill("ROOT.B", ["slot(map_probe, theme, claim_b)."])
        compiler = FakeCompiler("compiled")
        self.lattice.compile("ROOT.A", compiler=compiler)
        self.lattice.compile("ROOT.B", compiler=compiler)

        with self.assertRaisesRegex(MapV2Error, "incompatible_kappa"):
            self.lattice.combine("ROOT.AB", ["ROOT.A", "ROOT.B"])

    def test_version_one_state_migrates_without_losing_authored_source(self) -> None:
        self.lattice.create("map_probe", "world")
        state = json.loads(self.lattice.state_path.read_text(encoding="utf-8"))
        state["version"] = 1
        state["story"] = state.pop("subject")
        state["nodes"]["map_probe"].pop("griess")
        state["nodes"]["map_probe"].pop("revisions")
        self.lattice.state_path.write_text(json.dumps(state), encoding="utf-8")

        reopened = MapV2Lattice(self.state_dir)
        node = reopened.show("map_probe")

        self.assertEqual(node["griess"]["phase"], "derive")
        self.assertIn("migrated from MAP v2 state version 1", node["griess"]["history"])
        self.assertIn(
            "map_subject(world,map_probe).",
            reopened.workspace_path.read_text(encoding="utf-8"),
        )

    def test_cli_emits_machine_readable_json(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(
                [
                    "--state",
                    str(self.state_dir),
                    "--domain-manifest",
                    str(TOY_MANIFEST),
                    "new",
                    "map_probe",
                    "claim",
                    "--root",
                    "ROOT",
                ]
            )
        self.assertEqual(code, 0)
        body = json.loads(out.getvalue())
        self.assertTrue(body["ok"])
        self.assertEqual(body["result"]["root"], "ROOT")

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(
                [
                    "--state",
                    str(self.state_dir),
                    "--domain-manifest",
                    str(TOY_MANIFEST),
                    "kappa",
                    "ROOT",
                    "case_domain",
                    "grounded_evidence=evidence has provenance",
                ]
            )
        self.assertEqual(code, 0)
        body = json.loads(out.getvalue())
        self.assertEqual(body["result"]["phase"], "derive")
        self.assertEqual(
            body["result"]["kappa"]["invariants"]["grounded_evidence"],
            "evidence has provenance",
        )

    def test_cli_errors_are_machine_readable_and_nonzero(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = main(
                [
                    "--state",
                    str(self.state_dir),
                    "--domain-manifest",
                    str(TOY_MANIFEST),
                    "show",
                ]
            )
        self.assertEqual(code, 2)
        body = json.loads(err.getvalue())
        self.assertFalse(body["ok"])
        self.assertIn("run 'new' first", body["error"])


if __name__ == "__main__":
    unittest.main()
