from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from map_v2 import (
    MapConstructionError,
    MapV2Error,
    MapV2Lattice,
    PrologTargetCompiler,
    load_domain_manifest,
    main,
)
from tests.fixtures.typed_chain_adapter import (
    ChangedTypedChainAdapter,
    ConjoinedCandidateAdapter,
    ForgedDerivedAdapter,
    TypedChainAdapter,
    VariableCandidateAdapter,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CHAIN_MANIFEST = (
    REPO_ROOT / "tests" / "fixtures" / "map_domains" / "typed_chain" / "domain.json"
)


def construction_payload(*, complete: bool = True) -> dict:
    steps = [
        {
            "kind": "step",
            "id": "first_step",
            "source": "alpha",
            "target": "beta",
            "how": {"kind": "human_witness", "source": "report_one"},
        }
    ]
    if complete:
        steps.append(
            {
                "kind": "step",
                "id": "second_step",
                "source": "beta",
                "target": "omega",
                "how": {"kind": "human_witness", "source": "report_two"},
            }
        )
    return {
        "kind": "typed_chain",
        "subject": "chain_probe",
        "start": "alpha",
        "goal": "omega",
        "steps": steps,
    }


class TypedConstructionMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="map_psc_test_")
        self.state_dir = Path(self.tempdir.name) / "lattice"
        self.adapter = TypedChainAdapter()
        self.compiler = PrologTargetCompiler(load_domain_manifest(CHAIN_MANIFEST))
        self.lattice = MapV2Lattice(
            self.state_dir,
            compiler=self.compiler,
            construction_adapter=self.adapter,
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def prepare(self) -> None:
        self.lattice.create("chain_probe", "typed_chain")
        self.lattice.declare_kappa(
            "chain_probe",
            "typed_relations",
            {"relational_closure": "the witnessed steps recursively reach the goal"},
        )
        self.lattice.compute("chain_probe")

    def test_psc_construction_reaches_ont_through_recursive_map_derivation(self) -> None:
        self.prepare()
        filled = self.lattice.fill_construction(
            "chain_probe", construction_payload()
        )
        self.assertEqual(filled["construction"]["schema_id"], "map.fixture.typed_chain.v1")

        workspace = self.lattice.workspace_path.read_text(encoding="utf-8")
        self.assertIn("candidate_step(chain_probe,first_step,alpha,beta).", workspace)
        self.assertIn("candidate_step(chain_probe,second_step,beta,omega).", workspace)
        self.assertNotIn("derived_reachable", workspace)
        self.assertNotIn("typed_chain_proof", workspace)

        packet = self.lattice.compile("chain_probe")

        self.assertEqual(packet["status"], "compiled")
        self.assertEqual(packet["griess_phase"], "ont")
        self.assertIn(
            "typed_chain_proof(chain_probe,alpha,omega,relational_closure).",
            packet["outputs"],
        )
        self.assertIn(
            "typed_chain_derived_reachable(chain_probe,alpha,omega).",
            packet["domain_terms"],
        )
        self.assertEqual(
            packet["construction_payload_sha256"],
            filled["construction"]["payload_sha256"],
        )

        envelope = self.lattice.export_certificate("chain_probe")
        certificate = envelope["certificate"]
        self.assertEqual(
            certificate["construction_schema_id"], "map.fixture.typed_chain.v1"
        )
        self.assertEqual(
            envelope["proof_context"]["construction"]["payload"],
            construction_payload(),
        )

    def test_valid_typed_value_can_remain_soup_when_relational_goal_is_open(self) -> None:
        self.prepare()
        self.lattice.fill_construction(
            "chain_probe", construction_payload(complete=False)
        )

        packet = self.lattice.compile("chain_probe")

        self.assertEqual(packet["status"], "partial")
        self.assertEqual(packet["griess_phase"], "soup")
        self.assertIn(
            "typed_chain_missing_reachable_goal(chain_probe,alpha,omega).",
            packet["frontier"],
        )

    def test_naked_or_malformed_how_fails_before_prolog(self) -> None:
        self.prepare()
        payload = construction_payload()
        del payload["steps"][0]["how"]

        with self.assertRaisesRegex(
            MapConstructionError,
            "typed_construction_validation_failed.*steps.*0.*how",
        ):
            self.lattice.fill_construction("chain_probe", payload)

        node = self.lattice.show("chain_probe")
        self.assertEqual(node["status"], "open")
        self.assertEqual(node["griess"]["phase"], "compute")
        self.assertEqual(node["facts"], [])

    def test_lowerer_cannot_author_a_derived_predicate(self) -> None:
        self.prepare()
        with self.assertRaisesRegex(
            MapConstructionError, "is not candidate-authorable"
        ):
            self.lattice.fill_construction(
                "chain_probe",
                construction_payload(),
                adapter=ForgedDerivedAdapter(),
            )

    def test_lowerer_cannot_smuggle_a_universal_candidate_with_a_variable(self) -> None:
        self.prepare()
        with self.assertRaisesRegex(MapConstructionError, "not variables"):
            self.lattice.fill_construction(
                "chain_probe",
                construction_payload(),
                adapter=VariableCandidateAdapter(),
            )

    def test_lowerer_cannot_append_a_derived_goal_to_a_candidate(self) -> None:
        self.prepare()
        with self.assertRaisesRegex(MapConstructionError, "one predicate fact"):
            self.lattice.fill_construction(
                "chain_probe",
                construction_payload(),
                adapter=ConjoinedCandidateAdapter(),
            )

    def test_explicit_model_payload_round_trips_without_generic_metastack_loss(self) -> None:
        self.prepare()
        payload = construction_payload()
        self.lattice.fill_construction("chain_probe", payload)

        reopened = MapV2Lattice(
            self.state_dir,
            compiler=self.compiler,
            construction_adapter=self.adapter,
        )
        construction = reopened.show("chain_probe")["construction"]

        self.assertEqual(construction["payload"], payload)
        self.assertEqual(construction["payload"]["steps"][0]["kind"], "step")
        self.assertEqual(
            construction["payload"]["steps"][0]["how"]["kind"],
            "human_witness",
        )

    def test_adapter_change_stales_an_ont_certificate(self) -> None:
        self.prepare()
        self.lattice.fill_construction("chain_probe", construction_payload())
        self.lattice.compile("chain_probe")

        changed = MapV2Lattice(
            self.state_dir,
            compiler=self.compiler,
            construction_adapter=ChangedTypedChainAdapter(),
        )

        self.assertEqual(
            changed.queue(),
            [
                {
                    "name": "chain_probe",
                    "reason": "reopen_after_stale_construction_lowering_id",
                }
            ],
        )
        with self.assertRaisesRegex(
            MapV2Error, "stale_construction_lowering_id"
        ):
            changed.export_certificate("chain_probe")

    def test_typed_revision_preserves_prior_construction(self) -> None:
        self.prepare()
        original = construction_payload(complete=False)
        self.lattice.fill_construction("chain_probe", original)
        self.lattice.compile("chain_probe")
        self.lattice.retry("chain_probe")
        self.lattice.compute("chain_probe")

        revised = self.lattice.revise_construction(
            "chain_probe", construction_payload()
        )
        packet = self.lattice.compile("chain_probe")

        node = self.lattice.show("chain_probe")
        self.assertEqual(revised["revision_count"], 1)
        self.assertEqual(packet["status"], "compiled")
        self.assertEqual(node["revisions"][0]["construction"]["payload"], original)

    def test_cli_accepts_explicit_adapter_and_json_payload(self) -> None:
        adapter_ref = "tests.fixtures.typed_chain_adapter:TypedChainAdapter"
        commands = [
            ["new", "chain_probe", "typed_chain"],
            [
                "kappa",
                "chain_probe",
                "typed_relations",
                "relational_closure=the chain reaches its declared goal",
            ],
            ["compute", "chain_probe"],
            [
                "fill-construction",
                "chain_probe",
                json.dumps(construction_payload()),
            ],
            ["compile", "chain_probe"],
        ]
        last = None
        for command in commands:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main(
                    [
                        "--state",
                        str(self.state_dir),
                        "--domain-manifest",
                        str(CHAIN_MANIFEST),
                        "--construction-adapter",
                        adapter_ref,
                        *command,
                    ]
                )
            self.assertEqual(code, 0, command)
            last = json.loads(out.getvalue())
        self.assertEqual(last["result"]["status"], "compiled")
        self.assertEqual(last["result"]["griess_phase"], "ont")


if __name__ == "__main__":
    unittest.main()
