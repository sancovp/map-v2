from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from map_v2 import MapV2Lattice, PrologTargetCompiler, load_domain_manifest
from tests.fixtures.pattern_coherence_adapter import (
    CategoricalRingConstructionAdapter,
    CategoricalRingObservationAdapter,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_MANIFEST = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "map_domains"
    / "pattern_coherence"
    / "domain.json"
)
PATTERN_SHA256 = "c" * 64
EXTRACTOR_SHA256 = "e" * 64
CONFIG_SHA256 = "f" * 64


def proposal(*candidates: str) -> dict:
    return {
        "kind": "categorical_ring_proposal",
        "subject": "audit_probe",
        "proposal_id": "audit_ring_occurrence",
        "pattern": {
            "pattern_id": "categorical_ring",
            "version": "1.0.0",
            "semantic_sha256": PATTERN_SHA256,
        },
        "ring_candidates": list(candidates or ("audit_ring",)),
    }


def observed_entity(
    entity_id: str,
    *,
    declared: tuple[str, ...] = ("store", "provenance"),
    accesses: tuple[tuple[str, int, str], ...] = (("store", 17, "access_store"),),
    coverage: str = "complete",
) -> dict:
    return {
        "entity_id": entity_id,
        "declared_capabilities": list(declared),
        "accesses": [
            {"capability": capability, "line": line, "evidence_id": evidence}
            for capability, line, evidence in accesses
        ],
        "direct_access_coverage": coverage,
        "kind_evidence_id": f"kind_{entity_id}",
    }


def snapshot(*entities: dict) -> dict:
    return {
        "kind": "categorical_ring_observation",
        "subject": "audit_probe",
        "snapshot_id": "snapshot_one",
        "extractor_id": "direct_ring_scanner",
        "extractor_implementation_sha256": EXTRACTOR_SHA256,
        "extractor_configuration_sha256": CONFIG_SHA256,
        "entities": list(entities or (observed_entity("audit_ring"),)),
    }


class PatternCoherenceVerticalSliceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(prefix="map_pattern_test_")
        self.state_dir = Path(self.tempdir.name) / "lattice"
        self.compiler = PrologTargetCompiler(load_domain_manifest(DOMAIN_MANIFEST))
        self.construction_adapter = CategoricalRingConstructionAdapter()
        self.observation_adapter = CategoricalRingObservationAdapter()
        self.lattice = MapV2Lattice(
            self.state_dir,
            compiler=self.compiler,
            construction_adapter=self.construction_adapter,
            observation_adapter=self.observation_adapter,
        )
        self.lattice.create("audit_probe", "pattern_occurrence")
        self.lattice.declare_kappa(
            "audit_probe",
            "pattern_coherence",
            {
                "independent_observation": "candidate and source authorities are separate",
                "closed_world_coverage": "absence is scoped by observer completeness",
            },
        )
        self.lattice.compute("audit_probe")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def fill_and_observe(self, proposal_payload: dict, snapshot_payload: dict) -> None:
        self.lattice.fill_construction("audit_probe", proposal_payload)
        self.lattice.attach_observation("audit_probe", snapshot_payload)

    def test_clean_ring_reaches_ont_with_observation_bound_certificate(self) -> None:
        source = snapshot()
        self.fill_and_observe(proposal("audit_ring"), source)

        packet = self.lattice.compile("audit_probe")

        self.assertEqual(packet["status"], "compiled")
        self.assertEqual(packet["griess_phase"], "ont")
        self.assertIn(
            "pattern_occurrence_proof(audit_probe,audit_ring_occurrence,"
            "categorical_ring,ring_class(audit_ring),snapshot_one).",
            packet["outputs"],
        )
        certificate = self.lattice.export_certificate("audit_probe")
        self.assertEqual(
            certificate["certificate"]["observation_schema_id"],
            "map.fixture.categorical_ring_observation.v1",
        )
        self.assertEqual(
            certificate["proof_context"]["observation"]["payload"], source
        )
        workspace = self.lattice.workspace_path.read_text(encoding="utf-8")
        self.assertIn("candidate_role_binding", workspace)
        self.assertIn("source_accessed_capability", workspace)
        self.assertNotIn("pattern_occurrence_proof", workspace)

    def test_direct_undeclared_access_is_exact_contradiction(self) -> None:
        source = snapshot(
            observed_entity(
                "audit_ring",
                declared=("store",),
                accesses=(
                    ("store", 17, "access_store"),
                    ("cache", 29, "access_cache"),
                ),
            )
        )
        self.fill_and_observe(proposal("audit_ring"), source)

        packet = self.lattice.compile("audit_probe")

        self.assertEqual(packet["status"], "contradicted")
        self.assertEqual(packet["griess_phase"], "soup")
        self.assertIn(
            "pattern_constraint_contradicted(audit_probe,audit_ring_occurrence,"
            "ring_alphabet_closed,accessed_capability(cache),"
            "missing_declaration(cache),line(29),evidence(access_cache)).",
            packet["blocked"],
        )
        self.assertFalse(
            any(term.startswith("pattern_occurrence_proof(") for term in packet["outputs"])
        )

    def test_partial_observer_cannot_prove_closed_world_absence(self) -> None:
        source = snapshot(
            observed_entity("audit_ring", coverage="partial")
        )
        self.fill_and_observe(proposal("audit_ring"), source)

        packet = self.lattice.compile("audit_probe")

        self.assertEqual(packet["status"], "partial")
        self.assertEqual(packet["griess_phase"], "soup")
        self.assertIn(
            "incomplete_closed_world_scope(audit_probe,ring_alphabet_closed,"
            "audit_ring,direct_self_attribute).",
            packet["frontier"],
        )
        self.assertFalse(
            any(term.startswith("pattern_occurrence_proof(") for term in packet["outputs"])
        )

    def test_multiple_complete_role_maps_remain_ambiguous_soup(self) -> None:
        source = snapshot(
            observed_entity("audit_ring"),
            observed_entity("shadow_ring"),
        )
        self.fill_and_observe(
            proposal("audit_ring", "shadow_ring"),
            source,
        )

        packet = self.lattice.compile("audit_probe")

        self.assertEqual(packet["status"], "partial")
        self.assertEqual(packet["griess_phase"], "soup")
        self.assertIn(
            "pattern_ambiguous_binding(audit_probe,audit_ring_occurrence,"
            "ring_class,[audit_ring,shadow_ring]).",
            packet["frontier"],
        )
        self.assertFalse(
            any(term.startswith("pattern_occurrence_proof(") for term in packet["outputs"])
        )


if __name__ == "__main__":
    unittest.main()
