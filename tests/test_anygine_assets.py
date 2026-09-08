"""Checked common-content contracts; external payloads are never required by this suite."""

import hashlib
import json
from pathlib import Path
import unittest

from anyasset.core import select, validate_catalog
from anyasset.libraries import validate_index

ROOT = Path(__file__).resolve().parents[1]


class AnygineContentTests(unittest.TestCase):
    def test_native_triangle_keeps_its_original_source_bytes(self):
        catalog = validate_catalog(json.loads((ROOT / "catalog.json").read_text()))
        item = catalog["assets"]["tests/anygine/test-triangle"]
        self.assertEqual(hashlib.sha256((ROOT / item["entry"]).read_bytes()).hexdigest(),
                         "6bf6e767a21418ddbf1b9aa0ad692001b0e28a58dd944b965e02f3888ab27d33")
        self.assertIn("content/anygine/Assets/Interchange/TestTriangle.bin", item["files"])

    def test_terrain_manifest_references_are_in_the_selected_closure(self):
        catalog = validate_catalog(json.loads((ROOT / "catalog.json").read_text()))
        selected = select(catalog, ["anygine/terrain"])
        manifest = json.loads((ROOT / catalog["assets"]["textures/terrain/library"]["entry"]).read_text())
        files = {path for name in selected for path in catalog["assets"][name]["files"]}
        self.assertEqual(len(manifest["sets"]), 8)
        for kit in manifest["sets"]:
            for channel in ("base_color", "normal_gl", "roughness", "height"):
                self.assertIn("content/anygine/Assets/" + kit[channel], files)

    def test_ltc_license_and_lookup_hashes_remain_exact(self):
        root = ROOT / "content/anygine/Assets/Textures/LtcGgx"
        manifest = json.loads((root / "manifest.json").read_text())
        for item in [manifest["source"]["license"], manifest["storage"]["matrix"], manifest["storage"]["amplitude"]]:
            self.assertEqual(hashlib.sha256((root / item["file"]).read_bytes()).hexdigest(), item["sha256"])

    def test_external_indexes_are_metadata_only_with_unique_versions(self):
        seen = set()
        for path in (ROOT / "external-indexes").rglob("*.json"):
            index = validate_index(json.loads(path.read_text()))
            identity = (index["id"], index["version"])
            self.assertNotIn(identity, seen)
            seen.add(identity)
            self.assertNotIn("/home/", path.read_text())
            self.assertNotIn("root", index)
            self.assertTrue(all(item["lfs"] is False for item in index["files"]))
        self.assertTrue({"anygine-engine", "anygine-local", "anygine-robots"}.issubset({x[0] for x in seen}))


if __name__ == "__main__":
    unittest.main()
