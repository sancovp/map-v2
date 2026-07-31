from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import map_v2
from map_v2 import MapV2Lattice, PrologTargetCompiler, load_domain_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOY_MANIFEST = REPO_ROOT / "tests" / "fixtures" / "map_domains" / "toy" / "domain.json"


class IndependentMapV2Tests(unittest.TestCase):
    def test_map_package_has_no_gas_or_dd_imports(self) -> None:
        self.assertIn("/map_v2/", Path(map_v2.__file__).as_posix())
        for source in sorted((REPO_ROOT / "map_v2").glob("*.py")):
            text = source.read_text(encoding="utf-8")
            self.assertNotIn("ghost_story_bootstrap", text, source.name)
            self.assertNotIn("dharma_detectives", text, source.name)

    def test_non_dd_domain_reaches_soup_then_ont(self) -> None:
        compiler = PrologTargetCompiler(load_domain_manifest(TOY_MANIFEST))
        with tempfile.TemporaryDirectory(prefix="map_v2_toy_") as tempdir:
            lattice = MapV2Lattice(Path(tempdir) / "lattice", compiler=compiler)
            lattice.create("toy_probe", "claim")
            lattice.declare_kappa(
                "toy_probe",
                "toy_claims",
                {"grounded_claim": "the claim is explicitly grounded"},
            )
            compute = lattice.compute("toy_probe")
            self.assertEqual(compute["status"], "partial")
            lattice.fill("toy_probe", ["claim_fact(toy_probe,ungrounded_claim)."])
            soup = lattice.compile("toy_probe")
            self.assertEqual(soup["griess_phase"], "soup")
            self.assertEqual(lattice.show("toy_probe")["griess"]["phase"], "soup")

            lattice.retry("toy_probe")
            lattice.compute("toy_probe")
            lattice.revise("toy_probe", ["claim_fact(toy_probe,grounded_claim)."])
            ont = lattice.compile("toy_probe")
            self.assertEqual(ont["status"], "compiled")
            self.assertEqual(ont["griess_phase"], "ont")
            self.assertIn("toy_proof(toy_probe,grounded_claim).", ont["outputs"])


if __name__ == "__main__":
    unittest.main()
