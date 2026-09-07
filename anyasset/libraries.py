"""Metadata-only external library indexes and machine-local source bindings.

External providers are local directories, not executable plugins. Contents are
verified and copied into managed snapshots; no external payload is uploaded.
"""
from pathlib import Path
import json
import re

from .core import (HEX, atomic_json, digest, file_hash, git, read_json, require,
                   safe_path, select, store_lock, validate_catalog)

TOKEN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")


def token(value):
    require(isinstance(value, str) and TOKEN.fullmatch(value), "Library IDs/versions must use lowercase portable tokens (max 80 characters)")
    safe_path("content/" + value)
    return value


def index_path(value):
    require(isinstance(value, str) and value.startswith("external-indexes/") and value.endswith(".json"),
            "External index must be a JSON file under external-indexes/")
    safe_path("content/" + value.removeprefix("external-indexes/"))
    return value


def validate_requests(requests):
    require(isinstance(requests, list), "external must be an array of tables")
    result, ids = [], set()
    for item in requests:
        require(isinstance(item, dict) and set(item) == {"id", "index", "collections"}, "External requests require only id, index, collections")
        library = token(item["id"])
        require(library not in ids, "Duplicate external library ID")
        ids.add(library)
        groups = item["collections"]
        require(isinstance(groups, list) and groups and all(isinstance(x, str) for x in groups), "External collections must be a nonempty string array")
        result.append({"id": library, "index": index_path(item["index"]), "collections": sorted(set(groups))})
    return sorted(result, key=lambda x: x["id"])


def validate_records(files):
    require(isinstance(files, list), "External files must be an array")
    paths = set()
    for item in files:
        require(isinstance(item, dict) and set(item) == {"path", "sha256", "size", "lfs"}, "Invalid external file record")
        path = safe_path(item["path"])
        require(path.casefold() not in paths, "Duplicate external file path")
        paths.add(path.casefold())
        require(isinstance(item["sha256"], str) and HEX.fullmatch(item["sha256"]), "Invalid external file hash")
        require(type(item["size"]) is int and item["size"] >= 0 and item["lfs"] is False, "Invalid external size/provider")
    require(files == sorted(files, key=lambda x: x["path"]), "External records must be sorted by path")


def validate_index(index):
    require(isinstance(index, dict) and set(index) == {"schema", "id", "version", "revision", "catalog", "files"}, "Invalid external index fields")
    require(index["schema"] == 1, "Unsupported external index schema")
    token(index["id"])
    token(index["version"])
    validate_catalog(index["catalog"])
    validate_records(index["files"])
    expected = sorted({p for a in index["catalog"]["assets"].values() for p in a["files"]})
    require(expected == [f["path"] for f in index["files"]], "Index records do not cover the full catalog")
    require(index["revision"] == digest({k: v for k, v in index.items() if k != "revision"}), "External index revision mismatch")
    return index


def index_library(root, catalog, library_id, version, output):
    """Write an immutable metadata-only descriptor. Never stores root or payload."""
    root, output = Path(root).resolve(), Path(output).resolve()
    token(library_id)
    token(version)
    catalog = validate_catalog(read_json(catalog))
    records = []
    for name in sorted({p for a in catalog["assets"].values() for p in a["files"]}):
        path = root / name
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root), f"Missing/escaping external asset: {name}")
        before = path.stat()
        with path.open("rb") as stream:
            require(not stream.read(128).startswith(b"version https://git-lfs.github.com/spec/v1"), "External source contains LFS pointers; materialize it first")
        sha = file_hash(path)
        after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), f"External file changed while indexing: {name}")
        records.append({"path": name, "sha256": sha, "size": after.st_size, "lfs": False})
    result = {"schema": 1, "id": library_id, "version": version, "catalog": catalog, "files": records}
    result["revision"] = digest(result)
    with store_lock(output.parent / ".anyasset"):
        if output.exists():
            require(read_json(output) == result, "Index already exists with different content; publish a new version/path")
        else:
            atomic_json(output, result)
    return result


def bind_library(store, library_id, version, root):
    """Register only on this machine. Each library version has its own mapping."""
    store, root = Path(store).resolve(), Path(root).resolve()
    token(library_id)
    token(version)
    require(root.is_dir(), "External library directory does not exist")
    require(not root.is_relative_to(store) and not store.is_relative_to(root), "External source and managed store must not contain each other")
    result = {"id": library_id, "version": version, "root": str(root)}
    with store_lock(store):
        atomic_json(store / "libraries" / (digest([library_id, version]) + ".json"), result)
    return result


def resolve_indexes(repo, commit, requests):
    results = []
    for request in validate_requests(requests):
        path = request["index"]
        tree = git(repo, "ls-tree", commit, "--", path).stdout
        require(tree.startswith((b"100644 blob ", b"100755 blob ")), "External index must be a committed regular JSON file")
        size = int(git(repo, "cat-file", "-s", f"{commit}:{path}").stdout)
        require(size <= 16 * 1024 * 1024, "External index exceeds 16 MiB; split the library")
        index = validate_index(json.loads(git(repo, "show", f"{commit}:{path}").stdout))
        require(index["id"] == request["id"], "External index library ID mismatch")
        chosen = select(index["catalog"], request["collections"])
        paths = {p for a in chosen.values() for p in a["files"]}
        results.append(dict(request, version=index["version"], revision=index["revision"],
                            files=[f for f in index["files"] if f["path"] in paths],
                            assets={k: v["entry"] for k, v in chosen.items()}))
    return results


def validate_locked(libraries):
    require(isinstance(libraries, list), "Invalid external lock array")
    ids = []
    for item in libraries:
        require(isinstance(item, dict) and set(item) == {"id", "index", "collections", "version", "revision", "files", "assets"}, "Invalid external lock fields")
        token(item["id"])
        token(item["version"])
        index_path(item["index"])
        require(isinstance(item["revision"], str) and HEX.fullmatch(item["revision"]), "Invalid library revision")
        validate_requests([{k: item[k] for k in ("id", "index", "collections")}])
        validate_records(item["files"])
        require(isinstance(item["assets"], dict), "External assets must be an object")
        paths = {f["path"] for f in item["files"]}
        from .core import NAME
        for name, path in item["assets"].items():
            require(NAME.fullmatch(name) and path in paths, "Invalid external entry mapping")
        ids.append(item["id"])
    require(ids == sorted(set(ids)), "Duplicate or unsorted external library IDs")


def import_objects(manager, libraries):
    for library in libraries:
        missing = [f for f in library["files"] if not manager._valid(manager._object(f["sha256"]), f)]
        if not missing:
            continue
        record = manager.store / "libraries" / (digest([library["id"], library["version"]]) + ".json")
        require(record.exists(), f"External library not bound: {library['id']} version {library['version']}; run library-bind on this machine")
        binding = read_json(record)
        require(binding.get("id") == library["id"] and binding.get("version") == library["version"], "Library binding identity mismatch")
        root = Path(binding["root"]).resolve()
        for item in missing:
            source = root / item["path"]
            require(source.resolve().is_relative_to(root) and manager._valid(source, item),
                    f"External content missing or changed: {library['id']}::{item['path']} ({library['version']}); restore matching bytes or publish a new version")
            target = manager._object(item["sha256"])
            manager._copy_object(source, target)
            require(manager._valid(target, item), "External source changed during import; snapshot not published")
