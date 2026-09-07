"""Versioned manifests, managed Git/LFS cache, immutable snapshot bindings.

Public mutations serialize through an OS file lock. No checkout of an author's
repository, no hard links, no remote code execution, no automatic upgrades.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time
import tomllib
import sys

DEFAULT_SOURCE = "git@github.com:fangzhouRWTH/Anyasset.git"
HEX = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
NAME = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")


class AssetError(RuntimeError):
    """Expected operational or data-contract failure; CLI exits with code 2."""


def require(condition, message):
    if not condition:
        raise AssetError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AssetError(f"Cannot read JSON {path}: {exc}") from exc


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def safe_path(value):
    require(isinstance(value, str) and value.startswith("content/"), "Asset paths must start with content/")
    require("\\" not in value and not any(c in value for c in ':*?"<>|[],\x00\r\n'), f"Unsafe path: {value!r}")
    parts = value.split("/")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    require(all(p not in ("", ".", "..") and not p.endswith((" ", ".")) and p.split(".")[0].upper() not in reserved for p in parts), f"Nonportable path: {value}")
    return value


def git(repo, *args, check=True):
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1", GIT_TERMINAL_PROMPT="0")
    env.setdefault("GIT_SSH_COMMAND", "ssh -oBatchMode=yes -oConnectTimeout=15")
    timeout = positive_env("ANYASSET_GIT_TIMEOUT_SEC", 300)
    if args[0] in ("fetch", "clone") or args[:2] == ("lfs", "fetch"):
        print(f"Anyasset: {args[0]} in progress (timeout {timeout:g}s)", file=sys.stderr)
    child = subprocess.Popen(["git", "-C", str(repo), *args], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env, start_new_session=os.name != "nt")
    try:
        stdout, stderr = child.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], capture_output=True, timeout=10)
        else:
            os.killpg(child.pid, signal.SIGKILL)
        child.kill()
        child.communicate()
        raise AssetError(f"Git operation timed out after {timeout:g}s; cached completed data is retained")
    proc = subprocess.CompletedProcess(child.args, child.returncode, stdout, stderr)
    if check and proc.returncode:
        raise AssetError(f"git {args[0]} failed: {proc.stderr.decode('utf-8', errors='replace').strip()}")
    return proc


def positive_env(name, default):
    value = float(os.environ.get(name, default))
    require(0 < value < 86400, f"{name} must be between 0 and 86400 seconds")
    return value


@contextlib.contextmanager
def store_lock(root, timeout=None):
    """OS locks release on crash; the lock file itself deliberately persists."""
    timeout = positive_env("ANYASSET_LOCK_TIMEOUT_SEC", 30) if timeout is None else timeout
    root.mkdir(parents=True, exist_ok=True)
    with (root / "manager.lock").open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise AssetError("Asset store busy; retry when the current operation finishes")
                time.sleep(0.1)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def validate_catalog(catalog):
    require(isinstance(catalog, dict) and catalog.get("schema") == 1, "Unsupported catalog schema")
    assets, collections = catalog.get("assets"), catalog.get("collections")
    require(isinstance(assets, dict) and isinstance(collections, dict), "Catalog needs assets and collections objects")
    paths = {}
    for name, item in assets.items():
        require(NAME.fullmatch(name) is not None and isinstance(item, dict), f"Invalid asset ID: {name}")
        require(isinstance(item.get("files"), list) and item["files"], f"Asset {name} has no files")
        require(item.get("entry") in item["files"], f"Entry missing from files: {name}")
        require(isinstance(item.get("license"), str) and item["license"], f"Missing license: {name}")
        require(isinstance(item.get("origin"), str) and item["origin"], f"Missing origin: {name}")
        for path in item["files"]:
            safe_path(path)
            require(path.casefold() not in paths or paths[path.casefold()] == path, "Case-colliding asset paths")
            paths[path.casefold()] = path
        deps = item.get("depends", [])
        require(isinstance(deps, list) and all(isinstance(d, str) and d in assets for d in deps), f"Unknown dependencies: {name}")
    for name, members in collections.items():
        require(NAME.fullmatch(name) is not None and isinstance(members, list) and all(isinstance(a, str) and a in assets for a in members), f"Invalid collection: {name}")
    # Validate the entire graph, including assets not reachable from a collection.
    done, active = set(), set()
    def visit(name):
        require(name not in active, f"Dependency cycle at {name}")
        if name in done:
            return
        active.add(name)
        for dep in assets[name].get("depends", []):
            visit(dep)
        active.remove(name)
        done.add(name)
    for name in assets:
        visit(name)
    return catalog


def select(catalog, collections):
    validate_catalog(catalog)
    require(isinstance(collections, list) and collections and all(isinstance(c, str) for c in collections), "Select at least one collection")
    selected, visiting = set(), set()

    def visit(name):
        require(name not in visiting, f"Dependency cycle at {name}")
        if name in selected:
            return
        visiting.add(name)
        for dep in catalog["assets"][name].get("depends", []):
            visit(dep)
        visiting.remove(name)
        selected.add(name)

    for collection in collections:
        require(collection in catalog["collections"], f"Unknown collection: {collection}")
        for name in catalog["collections"][collection]:
            visit(name)
    return {name: catalog["assets"][name] for name in sorted(selected)}


def requirements(project):
    try:
        value = tomllib.loads((project / "assets.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AssetError(f"Cannot read assets.toml: {exc}") from exc
    require(value.get("schema") in (1, 2) and isinstance(value.get("source"), str) and value["source"], "Invalid assets.toml")
    require(isinstance(value.get("collections"), list) and value["collections"] and all(isinstance(x, str) for x in value["collections"]), "collections must be a nonempty string array")
    from .libraries import validate_requests
    validate_requests(value.get("external", []))
    require(not value.get("external") or value["schema"] == 2, "External libraries require requirements schema 2")
    return value


def validate_lock(value):
    require(isinstance(value, dict) and value.get("schema") in (1, 2), "Unsupported lock schema")
    require(isinstance(value.get("source"), str) and COMMIT.fullmatch(value.get("commit", "")), "Invalid lock source/commit")
    require(HEX.fullmatch(value.get("requirements_digest", "")), "Invalid requirements digest")
    require(isinstance(value.get("files"), list) and isinstance(value.get("assets"), dict), "Invalid lock files/assets")
    paths = set()
    for item in value["files"]:
        require(isinstance(item, dict), "Invalid file record")
        path = safe_path(item.get("path"))
        require(path.casefold() not in paths, "Duplicate/case-colliding lock path")
        paths.add(path.casefold())
        require(HEX.fullmatch(item.get("sha256", "")) and type(item.get("size")) is int and item["size"] >= 0, "Invalid file hash/size")
        require(type(item.get("lfs")) is bool, "Invalid LFS flag")
    for name, path in value["assets"].items():
        require(NAME.fullmatch(name) and safe_path(path).casefold() in paths, "Invalid asset entry mapping")
    from .libraries import validate_locked
    validate_locked(value.get("external", []))
    require(not value.get("external") or value["schema"] == 2, "External libraries require lock schema 2")
    return value


def all_files(lock):
    files = list(lock["files"])
    for library in lock.get("external", []):
        files.extend(dict(item, path=f"libraries/{library['id']}/{item['path']}") for item in library["files"])
    return files


def all_entries(lock):
    entries = dict(lock["assets"])
    for library in lock.get("external", []):
        entries.update({f"{library['id']}::{name}": f"libraries/{library['id']}/{path}"
                        for name, path in library["assets"].items()})
    return entries


class AssetManager:
    """Public manager bound to an absolute shared store directory."""

    def __init__(self, store):
        self.store = Path(store).expanduser().resolve()

    def init(self, project, source=DEFAULT_SOURCE, repo=None):
        """Create declaration if absent; bind a local store (never upgrades)."""
        project = Path(project).resolve()
        project.mkdir(parents=True, exist_ok=True)
        with store_lock(self.store):
            declaration = project / "assets.toml"
            if not declaration.exists():
                declaration.write_text('schema = 1\nsource = ' + json.dumps(source) + '\ncollections = ["defaults"]\n', encoding="utf-8")
            req = requirements(project)
            cfg = {"schema": 1, "store": str(self.store)}
            if repo:
                cfg["repo"] = str(Path(repo).resolve())
                git(cfg["repo"], "rev-parse", "--git-dir")
            atomic_json(project / ".anyasset/config.json", cfg)
            return {"project": str(project), "store": str(self.store), "source": req["source"]}

    def _repo(self, source):
        path = self.store / "repos" / (digest(source) + ".git")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            staging = Path(tempfile.mkdtemp(prefix=".repo-", dir=path.parent))
            try:
                git(staging, "init", "--bare")
                git(staging, "remote", "add", "origin", source)
                git(staging, "config", "lfs.storage", str(self.store))
                os.replace(staging, path)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
        else:
            require(git(path, "rev-parse", "--is-bare-repository", check=False).stdout.strip() == b"true",
                    "Managed repository is incomplete; use doctor and a new store if Git metadata is damaged")
            remote = git(path, "remote", "get-url", "origin", check=False)
            if remote.returncode:
                git(path, "remote", "add", "origin", source)
            else:
                require(remote.stdout.decode().strip() == source, "Managed repository source mismatch")
            git(path, "config", "lfs.storage", str(self.store))
        return path

    def _commit(self, project, repo, ref, offline=False):
        require(isinstance(ref, str) and ref and not ref.startswith("-") and not any(c.isspace() for c in ref), "Invalid ref")
        local = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
        if offline:
            require(local.returncode == 0, f"Commit not cached offline: {ref}")
            return local.stdout.decode().strip()
        # SHA locks reuse local Git objects without contacting the network.
        if COMMIT.fullmatch(ref) and local.returncode == 0:
            return local.stdout.decode().strip()
        config = read_json(project / ".anyasset/config.json")
        git(repo, "fetch", "--no-tags", "--", config.get("repo", "origin"), ref)
        commit = git(repo, "rev-parse", "FETCH_HEAD^{commit}").stdout.decode().strip()
        require(COMMIT.fullmatch(commit), "Only SHA-1 Git repositories are supported in schema 1")
        git(repo, "update-ref", "refs/anyasset/retained/" + commit, commit)
        return commit

    def _selection(self, repo, commit, collections):
        raw = git(repo, "show", f"{commit}:catalog.json").stdout
        try:
            catalog = json.loads(raw)
        except ValueError as exc:
            raise AssetError("Invalid catalog.json at selected commit") from exc
        selected = select(catalog, collections)
        tree = {}
        for record in git(repo, "ls-tree", "-r", "-z", commit).stdout.split(b"\0"):
            if record:
                meta, path = record.split(b"\t", 1)
                mode, kind, oid = meta.decode().split()
                tree[path.decode("utf-8")] = (mode, kind, oid)
        files = []
        for path in sorted({p for a in selected.values() for p in a["files"]}):
            require(path in tree and tree[path][0] in ("100644", "100755") and tree[path][1] == "blob", f"Missing or nonregular asset: {path}")
            oid = tree[path][2]
            size = int(git(repo, "cat-file", "-s", oid).stdout)
            # Ordinary Git assets are limited so accidental large binaries fail early.
            require(size <= 16 * 1024 * 1024, f"Use Git LFS for file larger than 16 MiB: {path}")
            data = git(repo, "cat-file", "blob", oid).stdout
            lfs = data.startswith(b"version https://git-lfs.github.com/spec/v1\n")
            if lfs:
                match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n?", data)
                require(match is not None, f"Unsupported LFS pointer (extensions unsupported): {path}")
                sha, size = match[1].decode(), int(match[2])
            else:
                sha = hashlib.sha256(data).hexdigest()
            files.append({"path": path, "sha256": sha, "size": size, "lfs": lfs})
        return files, {name: item["entry"] for name, item in selected.items()}

    def update(self, project, ref, offline=False):
        """Explicitly resolve a ref into assets.lock.json. Does not bind or download."""
        project = Path(project).resolve()
        with store_lock(self.store):
            req = requirements(project)
            repo = self._repo(req["source"])
            commit = self._commit(project, repo, ref, offline)
            files, entries = self._selection(repo, commit, req["collections"])
            lock = {"schema": req["schema"], "source": req["source"], "commit": commit,
                    "requirements_digest": digest(req), "collections": sorted(set(req["collections"])),
                    "files": files, "assets": entries}
            if req.get("external"):
                from .libraries import resolve_indexes
                lock["external"] = resolve_indexes(repo, commit, req["external"])
            atomic_json(project / "assets.lock.json", lock)
            return lock

    def _lock(self, project):
        value = validate_lock(read_json(project / "assets.lock.json"))
        req = requirements(project)
        require(value["requirements_digest"] == digest(req) and value["source"] == req["source"], "Requirements changed; run explicit update and review the new lock")
        require(value.get("collections") == sorted(set(req["collections"])), "Lock collections mismatch")
        from .libraries import validate_requests
        require(validate_requests(req.get("external", [])) == [
            {"id": lib["id"], "index": lib["index"], "collections": lib["collections"]}
            for lib in value.get("external", [])], "External lock requests mismatch")
        return value

    def _object(self, sha):
        return self.store / "objects" / sha[:2] / sha[2:4] / sha

    def _valid(self, path, item):
        return path.is_file() and not path.is_symlink() and path.stat().st_size == item["size"] and file_hash(path) == item["sha256"]

    def _verify_view(self, root, lock):
        require(root.is_dir() and not root.is_symlink(), "Snapshot missing or symlinked")
        require(read_json(root / "snapshot.json") == lock, "Snapshot metadata mismatch")
        for item in all_files(lock):
            path = root / item["path"]
            require(path.resolve().is_relative_to(root.resolve()) and self._valid(path, item), f"Snapshot corrupted: {item['path']}")

    def sync(self, project, offline=False):
        """Prepare exact locked files, verify hashes and atomically publish a binding."""
        project = Path(project).resolve()
        with store_lock(self.store):
            lock = self._lock(project)
            snapshot = digest(lock)
            root = self.store / "views" / snapshot
            if root.exists():
                self._verify_view(root, lock)
            else:
                repo = self._repo(lock["source"])
                commit = self._commit(project, repo, lock["commit"], offline)
                files, entries = self._selection(repo, commit, lock["collections"])
                require(files == lock["files"] and entries == lock["assets"], "Lock does not match committed catalog/content")
                if lock.get("external"):
                    from .libraries import resolve_indexes
                    require(resolve_indexes(repo, commit, requirements(project)["external"]) == lock["external"],
                            "External lock does not match committed indexes")
                missing = [f for f in files if not self._valid(self._object(f["sha256"]), f)]
                lfs_missing = [f for f in missing if f["lfs"]]
                require(not (offline and lfs_missing), "LFS content missing/corrupt offline: " + ", ".join(f["path"] for f in lfs_missing))
                if lfs_missing:
                    # Include patterns must not contain commas; rejected during catalog validation below.
                    config = read_json(project / ".anyasset/config.json")
                    # A local author repo is a seed, never a checkout target.
                    if config.get("repo"):
                        media = git(config["repo"], "lfs", "env").stdout.decode()
                        line = next((x for x in media.splitlines() if x.startswith("LocalMediaDir=")), None)
                        require(line, "Cannot locate seed LFS cache")
                        seed = Path(line.split("=", 1)[1])
                        for item in lfs_missing:
                            sha = item["sha256"]
                            source = seed / sha[:2] / sha[2:4] / sha
                            if self._valid(source, item):
                                self._copy_object(source, self._object(sha))
                    still_missing = [f for f in lfs_missing if not self._valid(self._object(f["sha256"]), f)]
                    for item in still_missing:
                        target = self._object(item["sha256"])
                        if target.exists():
                            target.unlink()  # invalid private cache object, never author content
                    # Bound command length for Windows while amortizing network startup.
                    batch, length = [], 0
                    for item in still_missing:
                        if batch and length + len(item["path"]) > 6000:
                            git(repo, "lfs", "fetch", "--include=" + ",".join(batch), "--exclude=", "origin", commit)
                            batch, length = [], 0
                        batch.append(item["path"])
                        length += len(item["path"]) + 1
                    if batch:
                        git(repo, "lfs", "fetch", "--include=" + ",".join(batch), "--exclude=", "origin", commit)
                for item in missing:
                    target = self._object(item["sha256"])
                    if not item["lfs"]:
                        data = git(repo, "show", f"{commit}:{item['path']}").stdout
                        target.parent.mkdir(parents=True, exist_ok=True)
                        fd, name = tempfile.mkstemp(dir=target.parent)
                        with os.fdopen(fd, "wb") as stream:
                            stream.write(data)
                        os.replace(name, target)
                    require(self._valid(target, item), f"Object verification failed: {item['path']}")
                from .libraries import import_objects
                import_objects(self, lock.get("external", []))
                root.parent.mkdir(parents=True, exist_ok=True)
                staging = Path(tempfile.mkdtemp(prefix=".prepare-", dir=root.parent))
                try:
                    for item in all_files(lock):
                        dest = staging / item["path"]
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(self._object(item["sha256"]), dest)
                    atomic_json(staging / "snapshot.json", lock)
                    self._verify_view(staging, lock)
                    os.replace(staging, root)
                finally:
                    if staging.exists():
                        shutil.rmtree(staging)
            binding = {"schema": lock["schema"], "lock_digest": snapshot, "root": str(root),
                       "assets": {name: str(root / path) for name, path in all_entries(lock).items()}}
            # Register retention before exposing a binding to the consumer.
            atomic_json(self.store / "bindings" / (digest(str(project)) + ".json"),
                        {"project": str(project), "snapshots": self._retained(project, snapshot)})
            atomic_json(project / ".anyasset/resolved.json", binding)
            return binding

    def _copy_object(self, source, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=target.parent)
        os.close(fd)
        try:
            shutil.copyfile(source, name)
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _retained(self, project, snapshot):
        record = self.store / "bindings" / (digest(str(project)) + ".json")
        old = read_json(record)["snapshots"] if record.exists() else []
        return sorted(set(old + [snapshot]))

    def status(self, project, verify=False):
        project = Path(project).resolve()
        with store_lock(self.store):
            lock = self._lock(project)
            binding_path = project / ".anyasset/resolved.json"
            binding = read_json(binding_path) if binding_path.exists() else {}
            current = binding.get("lock_digest") == digest(lock)
            expected = self.store / "views" / digest(lock)
            current = current and binding.get("root") == str(expected) and expected.exists()
            if verify:
                require(current, "Binding stale or absent; run sync --locked")
                self._verify_view(expected, lock)
            return {"current": bool(current), "commit": lock["commit"], "snapshot": digest(lock),
                    "root": str(expected), "asset_ids": sorted(all_entries(lock)), "verified": verify}

    def doctor(self, project):
        """Report binding/content problems without deleting or repairing data."""
        try:
            result = self.status(project, verify=True)
            return {"healthy": True, "status": result, "actions": []}
        except (AssetError, OSError, ValueError, KeyError, TypeError) as exc:
            return {"healthy": False, "error": str(exc), "actions": [
                "Check local library bindings and source availability; run sync --locked",
                "For a damaged published view, stop consumers and quarantine it before rebuilding",
                "Never edit the lock to bypass content verification"]}

    def plan(self, project):
        """Inspect the locked selection and missing cached bytes without downloading."""
        project = Path(project).resolve()
        with store_lock(self.store):
            lock = self._lock(project)
            unique = {f["sha256"]: f for f in all_files(lock)}
            missing = [f for f in unique.values() if not self._valid(self._object(f["sha256"]), f)]
            return {"snapshot": digest(lock), "assets": all_entries(lock),
                    "selected_bytes": sum(f["size"] for f in all_files(lock)),
                    "missing_unique_bytes": sum(f["size"] for f in missing),
                    "missing_objects": len(missing), "external_libraries": [
                        {"id": x["id"], "version": x["version"], "revision": x["revision"]}
                        for x in lock.get("external", [])]}

    def edit(self, project, destination):
        """Create a separate author checkout from the locked commit; no binding override."""
        project, destination = Path(project).resolve(), Path(destination).resolve()
        with store_lock(self.store):
            lock = self._lock(project)
            require(not destination.exists(), "Edit destination already exists")
            repo = self._repo(lock["source"])
            self._commit(project, repo, lock["commit"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            git(destination.parent, "clone", "--no-checkout", "--no-hardlinks", str(repo), str(destination))
            git(destination, "remote", "set-url", "origin", lock["source"])
            git(destination, "checkout", "-b", "asset-edit", lock["commit"])
            git(destination, "lfs", "install", "--local")
            return {"workspace": str(destination), "commit": lock["commit"],
                    "next": "Run git lfs pull in this workspace before editing LFS assets; consumption bindings are unchanged"}

    def gc(self):
        """Conservative preview only. Never removes snapshots, LFS objects or refs."""
        with store_lock(self.store):
            retained = set()
            for record in (self.store / "bindings").glob("*.json"):
                retained.update(read_json(record)["snapshots"])
            candidates = [p.name for p in (self.store / "views").glob("*") if HEX.fullmatch(p.name) and p.name not in retained]
            return {"dry_run": True, "retained": sorted(retained), "unreferenced_snapshots": sorted(candidates),
                    "note": "Preview only in v0.1; historical bindings retained until explicit future release policy"}


def resolve_asset(project, asset_id):
    """Resolve one logical ID from a fresh binding; no network or mutation."""
    project = Path(project).resolve()
    lock = validate_lock(read_json(project / "assets.lock.json"))
    require(lock["requirements_digest"] == digest(requirements(project)), "Requirements changed; update lock")
    binding = read_json(project / ".anyasset/resolved.json")
    require(binding.get("schema") == lock["schema"] and binding.get("lock_digest") == digest(lock), "Stale asset binding; run sync --locked")
    entries = all_entries(lock)
    require(asset_id in entries, f"Asset not selected: {asset_id}")
    root = Path(binding["root"]).resolve()
    path = (root / entries[asset_id]).resolve()
    require(path.is_relative_to(root) and path.is_file(), "Resolved asset missing or outside snapshot")
    return path
