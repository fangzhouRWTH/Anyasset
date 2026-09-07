"""Reliability regressions and metadata-only external-library integration."""
import json
from pathlib import Path
import subprocess
import time
import unittest
from unittest.mock import patch, Mock

import test_manager as fixtures
from anyasset import AssetError, AssetManager, resolve_asset
from anyasset.core import atomic_json, digest, git, read_json, validate_catalog
from anyasset.libraries import index_library, bind_library, validate_index


class ReliabilityTests(unittest.TestCase):
    def test_all_catalog_assets_checked_for_cycles(self):
        catalog = {"schema": 1, "collections": {"defaults": []}, "assets": {
            "a": {"entry": "content/a", "files": ["content/a"], "license": "test", "origin": "test", "depends": ["b"]},
            "b": {"entry": "content/b", "files": ["content/b"], "license": "test", "origin": "test", "depends": ["a"]}}}
        with self.assertRaises(AssetError):
            validate_catalog(catalog)

    def test_timeout_stops_process_and_reports_actionable_error(self):
        child = Mock(pid=123, args=["git"])
        child.communicate.side_effect = [subprocess.TimeoutExpired("git", 1), (b"", b"")]
        with patch("anyasset.core.subprocess.Popen", return_value=child), \
             patch("anyasset.core.subprocess.run"), patch("anyasset.core.os.killpg", create=True), \
             patch.dict("os.environ", {"ANYASSET_GIT_TIMEOUT_SEC": "1"}):
            with self.assertRaisesRegex(AssetError, "timed out"):
                git(Path.cwd(), "fetch", "origin")
        child.kill.assert_called_once()


# Reuse fixture construction without inheriting/re-running the base test suite.
class ExtensionTests(unittest.TestCase):
    setUp = fixtures.IntegrationTests.setUp
    save = fixtures.IntegrationTests.save

    def setup_external(self, version="v1", body=b"external one"):
        root = self.root / ("private data " + version)
        (root / "content").mkdir(parents=True, exist_ok=True)
        (root / "content/input.bin").write_bytes(body)
        catalog = {"schema": 1, "assets": {"a": {
            "entry": "content/input.bin", "files": ["content/input.bin"],
            "license": "Proprietary", "origin": "Local test fixture"}},
            "collections": {"task": ["a"]}}
        atomic_json(root / "catalog.json", catalog)
        output = self.repo / f"external-indexes/task/{version}.json"
        index = index_library(root, root / "catalog.json", "task-data", version, output)
        self.save()
        self.project.joinpath("assets.toml").write_text(
            'schema = 2\nsource = ' + json.dumps(str(self.repo)) + '\ncollections = ["defaults"]\n'
            '[[external]]\nid = "task-data"\nindex = "external-indexes/task/' + version + '.json"\ncollections = ["task"]\n', encoding="utf-8")
        lock = self.manager.update(self.project, "main")
        return root, index, lock

    def test_partial_repo_configuration_repaired(self):
        repo = self.manager._repo(str(self.repo))
        git(repo, "remote", "remove", "origin")
        git(repo, "config", "--unset", "lfs.storage")
        repaired = self.manager._repo(str(self.repo))
        self.assertEqual(git(repaired, "remote", "get-url", "origin").stdout.decode().strip(), str(self.repo))
        self.assertEqual(git(repaired, "config", "lfs.storage").stdout.decode().strip(), str(self.manager.store))

    def test_actual_git_child_timeout_returns_promptly(self):
        start = time.monotonic()
        with patch.dict("os.environ", {"ANYASSET_GIT_TIMEOUT_SEC": "0.3"}):
            with self.assertRaisesRegex(AssetError, "timed out"):
                git(self.repo, "-c", 'alias.anyasset-wait=!python -c "import time; time.sleep(20)"', "anyasset-wait")
        self.assertLess(time.monotonic() - start, 10)

    def test_reserved_library_id_rejected(self):
        with self.assertRaises(AssetError):
            bind_library(self.manager.store, "con", "v1", self.repo)

    def test_new_repo_interruption_is_retryable(self):
        manager = AssetManager(self.root / "new store")
        real = git
        def broken(repo, *args, **kwargs):
            if args[:2] == ("remote", "add"):
                raise AssetError("interrupted remote configuration")
            return real(repo, *args, **kwargs)
        with patch("anyasset.core.git", side_effect=broken), self.assertRaises(AssetError):
            manager._repo(str(self.repo))
        self.assertEqual(list((manager.store / "repos").iterdir()), [])
        self.assertTrue(manager._repo(str(self.repo)).exists())

    def test_external_metadata_only_and_unified_resolution(self):
        root, index, lock = self.setup_external()
        self.assertNotIn(str(root), json.dumps(index))
        self.assertNotIn("external one", json.dumps(index))
        self.assertEqual(lock["schema"], 2)
        with self.assertRaisesRegex(AssetError, "not bound"):
            self.manager.sync(self.project)
        self.assertFalse((self.project / ".anyasset/resolved.json").exists())
        bind_library(self.manager.store, "task-data", "v1", root)
        self.manager.sync(self.project, offline=True)
        self.assertEqual(resolve_asset(self.project, "task-data::a").read_bytes(), b"external one")
        self.assertEqual(resolve_asset(self.project, "a").read_bytes(), b"version one\n")
        self.assertTrue(self.manager.status(self.project, verify=True)["verified"])
        self.assertEqual(self.manager.plan(self.project)["missing_unique_bytes"], 0)

    def test_external_versions_coexist_and_author_edits_do_not_change_views(self):
        root1, _, lock1 = self.setup_external()
        bind_library(self.manager.store, "task-data", "v1", root1)
        first = self.manager.sync(self.project)
        entry1 = resolve_asset(self.project, "task-data::a")
        root2, _, _ = self.setup_external("v2", b"external two")
        bind_library(self.manager.store, "task-data", "v2", root2)
        second = self.manager.sync(self.project)
        self.assertNotEqual(first["root"], second["root"])
        self.assertEqual(entry1.read_bytes(), b"external one")
        root1.joinpath("content/input.bin").write_bytes(b"dirty author data")
        self.assertEqual(entry1.read_bytes(), b"external one")
        atomic_json(self.project / "assets.lock.json", lock1)
        req = self.project / "assets.toml"
        req.write_text(req.read_text().replace("v2.json", "v1.json"))
        self.assertEqual(self.manager.sync(self.project, offline=True), first)

    def test_matching_library_can_be_bound_on_another_machine(self):
        root, _, _ = self.setup_external()
        other = AssetManager(self.root / "other machine store")
        other.init(self.project, str(self.repo))
        bind_library(other.store, "task-data", "v1", root)
        other.sync(self.project)
        self.assertEqual(resolve_asset(self.project, "task-data::a").read_bytes(), b"external one")

    def test_changed_source_bytes_fail_closed(self):
        root, _, _ = self.setup_external()
        bind_library(self.manager.store, "task-data", "v1", root)
        root.joinpath("content/input.bin").write_bytes(b"changed")
        with self.assertRaisesRegex(AssetError, "missing or changed"):
            self.manager.sync(self.project)

    def test_external_objects_allow_new_view_without_source(self):
        root, _, _ = self.setup_external()
        bind_library(self.manager.store, "task-data", "v1", root)
        self.manager.sync(self.project)
        root.rename(root.with_name("source unavailable"))
        requirements = self.project / "assets.toml"
        requirements.write_text(requirements.read_text().replace('["defaults"]', '["defaults", "only-b"]'))
        commit = git(self.repo, "rev-parse", "HEAD").stdout.decode().strip()
        self.manager.update(self.project, commit, offline=True)
        self.manager.sync(self.project, offline=True)
        self.assertEqual(resolve_asset(self.project, "task-data::a").read_bytes(), b"external one")

    def test_index_revision_tamper_and_overwrite_rejected(self):
        root, index, _ = self.setup_external()
        index["files"][0]["size"] += 1
        with self.assertRaises(AssetError):
            validate_index(index)
        root.joinpath("content/input.bin").write_bytes(b"new")
        with self.assertRaisesRegex(AssetError, "already exists"):
            index_library(root, root / "catalog.json", "task-data", "v1", self.repo / "external-indexes/task/v1.json")

    def test_doctor_reports_corruption_without_mutation(self):
        self.manager.sync(self.project)
        entry = resolve_asset(self.project, "a")
        entry.write_bytes(b"broken")
        self.assertFalse(self.manager.doctor(self.project)["healthy"])
        self.assertEqual(entry.read_bytes(), b"broken")

    def test_library_cannot_bind_inside_cache(self):
        target = self.manager.store / "fake-source"
        target.mkdir(parents=True)
        with self.assertRaises(AssetError):
            bind_library(self.manager.store, "task-data", "v1", target)

    def test_external_requires_explicit_new_schema(self):
        self.setup_external()
        req = self.project / "assets.toml"
        req.write_text(req.read_text().replace("schema = 2", "schema = 1"))
        with self.assertRaisesRegex(AssetError, "schema 2"):
            self.manager.sync(self.project)


if __name__ == "__main__":
    unittest.main()
