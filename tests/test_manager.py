import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from anyasset import AssetError, AssetManager, resolve_asset
from anyasset.cli import main
from anyasset.core import atomic_json, digest, file_hash, git, read_json, safe_path, select, store_lock


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="anyasset test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "source"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Anyasset Test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "commit.gpgsign", "false")
        git(self.repo, "config", "core.autocrlf", "false")
        (self.repo / "content").mkdir()
        (self.repo / "content/a.txt").write_bytes(b"version one\n")
        (self.repo / "content/b.txt").write_bytes(b"dependency\n")
        self.catalog = {"schema": 1, "assets": {
            "a": {"entry": "content/a.txt", "files": ["content/a.txt"], "depends": ["b"], "license": "CC0-1.0", "origin": "test"},
            "b": {"entry": "content/b.txt", "files": ["content/b.txt"], "license": "CC0-1.0", "origin": "test"}},
            "collections": {"defaults": ["a"], "only-b": ["b"]}}
        self.commit = self.save()
        self.manager = AssetManager(self.root / "shared store")
        self.project = self.root / "engine one"
        self.manager.init(self.project, str(self.repo))
        self.manager.update(self.project, "main")

    def save(self):
        atomic_json(self.repo / "catalog.json", self.catalog)
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "fixture")
        return git(self.repo, "rev-parse", "HEAD").stdout.decode().strip()

    def test_dependency_closure_and_offline(self):
        binding = self.manager.sync(self.project, offline=True)
        self.assertEqual(sorted(binding["assets"]), ["a", "b"])
        self.assertEqual(resolve_asset(self.project, "a").read_bytes(), b"version one\n")
        self.assertTrue(self.manager.status(self.project, verify=True)["verified"])
        # The exact prepared view works even if the source repository is unavailable.
        self.repo.rename(self.root / "unavailable-source")
        self.assertEqual(self.manager.sync(self.project, offline=True), binding)

    def test_two_projects_share_view_and_multiple_versions_coexist(self):
        first = self.manager.sync(self.project)
        other = self.root / "engine two"
        self.manager.init(other, str(self.repo))
        self.manager.update(other, self.commit)
        self.assertEqual(first["root"], self.manager.sync(other)["root"])
        (self.repo / "content/a.txt").write_bytes(b"version two\n")
        second_commit = self.save()
        self.manager.update(other, "main")
        second = self.manager.sync(other)
        self.assertNotEqual(first["root"], second["root"])
        self.assertEqual(resolve_asset(self.project, "a").read_bytes(), b"version one\n")
        self.assertEqual(resolve_asset(other, "a").read_bytes(), b"version two\n")
        self.assertEqual(self.manager.status(other)["commit"], second_commit)
        # Equal source bytes share a single content-addressed object.
        bsha = file_hash(self.repo / "content/b.txt")
        self.assertTrue(self.manager._object(bsha).exists())

    def test_branch_switch_stale_binding_and_rollback(self):
        old_lock = read_json(self.project / "assets.lock.json")
        first = self.manager.sync(self.project)
        (self.repo / "content/a.txt").write_bytes(b"new version\n")
        self.save()
        self.manager.update(self.project, "main")
        self.assertFalse(self.manager.status(self.project)["current"])
        with self.assertRaises(AssetError):
            resolve_asset(self.project, "a")
        self.manager.sync(self.project)
        atomic_json(self.project / "assets.lock.json", old_lock)
        self.assertEqual(self.manager.sync(self.project, offline=True)["root"], first["root"])
        self.assertEqual(len(self.manager.gc()["retained"]), 2)

    def test_changed_requirements_must_be_explicitly_updated(self):
        with (self.project / "assets.toml").open("a") as stream:
            stream.write('note = "changed"\n')
        with self.assertRaises(AssetError):
            self.manager.sync(self.project)

    def test_tampered_lock_is_rejected_before_publication(self):
        lock = read_json(self.project / "assets.lock.json")
        lock["files"][0]["sha256"] = "0" * 64
        atomic_json(self.project / "assets.lock.json", lock)
        with self.assertRaises(AssetError):
            self.manager.sync(self.project)
        self.assertFalse((self.project / ".anyasset/resolved.json").exists())

    def test_corrupted_snapshot_does_not_modify_objects_or_other_project(self):
        binding = self.manager.sync(self.project)
        path = resolve_asset(self.project, "a")
        original = file_hash(path)
        path.write_bytes(b"bad edit")
        self.assertEqual(file_hash(self.manager._object(original)), original)
        with self.assertRaises(AssetError):
            self.manager.status(self.project, verify=True)
        with self.assertRaises(AssetError):
            self.manager.sync(self.project)
        self.assertTrue(Path(binding["root"]).is_dir())

    def test_corrupt_normal_object_rebuilt_from_git(self):
        self.manager.sync(self.project)
        sha = file_hash(self.repo / "content/a.txt")
        self.manager._object(sha).write_bytes(b"damaged")
        req = self.project / "assets.toml"
        req.write_text(req.read_text().replace('["defaults"]', '["defaults", "only-b"]'))
        self.manager.update(self.project, self.commit, offline=True)
        self.manager.sync(self.project, offline=True)
        self.assertEqual(file_hash(self.manager._object(sha)), sha)

    def test_missing_file_fails_update_without_replacing_lock(self):
        old = (self.project / "assets.lock.json").read_bytes()
        self.catalog["assets"]["a"]["files"].append("content/missing.txt")
        self.save()
        with self.assertRaises(AssetError):
            self.manager.update(self.project, "main")
        self.assertEqual((self.project / "assets.lock.json").read_bytes(), old)

    def test_unknown_collection(self):
        with self.assertRaises(AssetError):
            select(self.catalog, ["missing"])

    def test_dependency_cycle(self):
        self.catalog["assets"]["b"]["depends"] = ["a"]
        with self.assertRaises(AssetError):
            select(self.catalog, ["defaults"])

    def test_cross_platform_unsafe_paths(self):
        for path in ("../bad", "content/../bad", "content/A:B", "content/NUL.txt", "content/a,b", "content/a[1]", "content/x/", "content/a\\b"):
            with self.subTest(path=path), self.assertRaises(AssetError):
                safe_path(path)

    def test_case_collision(self):
        self.catalog["assets"]["b"]["files"].append("content/A.txt")
        with self.assertRaises(AssetError):
            select(self.catalog, ["defaults"])

    def test_gc_preview_keeps_historical_bindings(self):
        self.manager.sync(self.project)
        result = self.manager.gc()
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["unreferenced_snapshots"], [])

    def test_cli_contract_and_error_code(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["sync", "--locked", "--project", str(self.project)]), 0)
        self.assertIn("root", json.loads(output.getvalue()))
        with contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(["path", "--project", str(self.project), "absent"]), 2)
        self.assertEqual(json.loads(error.getvalue())["code"], "ASSET_ERROR")

    def test_parallel_processes_publish_one_snapshot(self):
        command = [os.sys.executable, "-m", "anyasset", "sync", "--locked", "--project", str(self.project)]
        procs = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        results = []
        for proc in procs:
            out, err = proc.communicate(timeout=30)
            self.assertEqual(proc.returncode, 0, err.decode())
            results.append(json.loads(out))
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(list((self.manager.store / "views").iterdir())), 1)

    def test_lock_timeout(self):
        with store_lock(self.manager.store):
            with self.assertRaises(AssetError):
                with store_lock(self.manager.store, timeout=0.1):
                    pass

    def test_edit_workspace_does_not_change_binding(self):
        before = self.manager.sync(self.project)
        dest = self.root / "edit workspace"
        self.manager.edit(self.project, dest)
        (dest / "content/a.txt").write_bytes(b"authoring")
        self.assertEqual(self.manager.sync(self.project), before)
        self.assertEqual(resolve_asset(self.project, "a").read_bytes(), b"version one\n")

    def test_lfs_seed_download_reuse_and_offline_missing(self):
        git(self.repo, "lfs", "install", "--local")
        git(self.repo, "lfs", "track", "*.bin")
        (self.repo / "content/test.bin").write_bytes(b"lfs-test-data\x00" * 100)
        self.catalog["assets"]["a"]["files"].append("content/test.bin")
        self.save()
        self.manager.init(self.project, str(self.repo), repo=self.repo)
        lock = self.manager.update(self.project, "main")
        self.assertTrue(next(f for f in lock["files"] if f["path"].endswith(".bin"))["lfs"])
        with self.assertRaises(AssetError):
            self.manager.sync(self.project, offline=True)
        binding = self.manager.sync(self.project)
        self.assertEqual((Path(binding["root"]) / "content/test.bin").read_bytes(), (self.repo / "content/test.bin").read_bytes())
        self.assertEqual(self.manager.sync(self.project, offline=True), binding)

    def test_lfs_fetch_without_seed_and_unselected_content_not_downloaded(self):
        git(self.repo, "lfs", "install", "--local")
        git(self.repo, "lfs", "track", "*.bin")
        (self.repo / "content/needed.bin").write_bytes(b"needed\x00" * 100)
        (self.repo / "content/unused.bin").write_bytes(b"unused\x00" * 100)
        self.catalog["assets"]["a"]["files"].append("content/needed.bin")
        self.save()
        self.manager.update(self.project, "main")
        binding = self.manager.sync(self.project)
        self.assertEqual((Path(binding["root"]) / "content/needed.bin").read_bytes(), (self.repo / "content/needed.bin").read_bytes())
        self.assertFalse(self.manager._object(file_hash(self.repo / "content/unused.bin")).exists())
        self.assertEqual(self.manager.sync(self.project, offline=True), binding)

    def test_unsupported_schema(self):
        lock = read_json(self.project / "assets.lock.json")
        lock["schema"] = 99
        atomic_json(self.project / "assets.lock.json", lock)
        with self.assertRaises(AssetError):
            self.manager.sync(self.project)

    def test_offline_unknown_commit_does_not_publish_binding(self):
        with self.assertRaises(AssetError):
            self.manager.update(self.project, "a" * 40, offline=True)
        self.assertFalse((self.project / ".anyasset/resolved.json").exists())

    def test_interrupted_materialization_never_publishes_partial_view(self):
        with patch("anyasset.core.shutil.copyfile", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError):
                self.manager.sync(self.project)
        self.assertFalse((self.project / ".anyasset/resolved.json").exists())
        self.assertEqual(list((self.manager.store / "views").iterdir()), [])
        self.manager.sync(self.project, offline=True)
        self.assertTrue(self.manager.status(self.project, verify=True)["verified"])


if __name__ == "__main__":
    unittest.main()
