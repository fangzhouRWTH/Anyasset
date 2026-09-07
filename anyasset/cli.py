"""Machine-readable CLI: one JSON object on stdout, failures on stderr."""
import argparse
import json
from pathlib import Path
import sys

from .core import (AssetError, AssetManager, DEFAULT_SOURCE, read_json,
                   resolve_asset, select, validate_catalog)


def parser():
    p = argparse.ArgumentParser(prog="assetctl", description="Anyasset shared development asset manager")
    p.add_argument("--version", action="version", version="anyasset 0.2.0")
    commands = p.add_subparsers(dest="command", required=True)
    for name in ("init", "update", "sync", "status", "verify", "path", "edit", "gc", "doctor", "plan"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--project", type=Path, default=Path.cwd())
        cmd.add_argument("--store", type=Path)
        if name == "init":
            cmd.add_argument("--source", default=DEFAULT_SOURCE)
            cmd.add_argument("--repo", type=Path, help="Optional local committed Git/LFS seed")
        if name == "update":
            cmd.add_argument("--ref", required=True)
            cmd.add_argument("--offline", action="store_true")
        if name == "sync":
            cmd.add_argument("--locked", action="store_true", required=True)
            cmd.add_argument("--offline", action="store_true")
        if name == "path":
            cmd.add_argument("asset_id")
        if name == "edit":
            cmd.add_argument("--destination", type=Path, required=True)
        if name == "gc":
            cmd.add_argument("--dry-run", action="store_true", required=True)
    cat = commands.add_parser("catalog-check")
    cat.add_argument("--repo", type=Path, default=Path.cwd())
    index = commands.add_parser("library-index")
    index.add_argument("--root", type=Path, required=True)
    index.add_argument("--catalog", type=Path, required=True)
    index.add_argument("--id", required=True)
    index.add_argument("--library-version", required=True)
    index.add_argument("--output", type=Path, required=True)
    bind = commands.add_parser("library-bind")
    bind.add_argument("--store", type=Path, required=True)
    bind.add_argument("--root", type=Path, required=True)
    bind.add_argument("--id", required=True)
    bind.add_argument("--library-version", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "library-index":
            from .libraries import index_library
            result = index_library(args.root, args.catalog, args.id, args.library_version, args.output)
        elif args.command == "library-bind":
            from .libraries import bind_library
            result = bind_library(args.store, args.id, args.library_version, args.root)
        elif args.command == "catalog-check":
            catalog = validate_catalog(read_json(args.repo / "catalog.json"))
            select(catalog, list(catalog["collections"]))
            for item in catalog["assets"].values():
                for name in item["files"]:
                    path = args.repo / name
                    if not path.is_file() or not path.resolve().is_relative_to(args.repo.resolve()):
                        raise AssetError(f"Missing or escaping catalog file: {name}")
            from .libraries import validate_index
            indexes = {}
            for path in (args.repo / "external-indexes").rglob("*.json"):
                if path.is_symlink() or not path.resolve().is_relative_to(args.repo.resolve()):
                    raise AssetError("External index escapes repository")
                index = validate_index(read_json(path))
                key = (index["id"], index["version"])
                if key in indexes and indexes[key] != index["revision"]:
                    raise AssetError("Conflicting external indexes for the same library/version")
                indexes[key] = index["revision"]
            result = {"valid": True, "assets": len(catalog["assets"]), "collections": sorted(catalog["collections"]), "external_indexes": len(indexes)}
        elif args.command == "path":
            result = {"asset_id": args.asset_id, "path": str(resolve_asset(args.project, args.asset_id))}
        else:
            store = args.store
            if store is None:
                config = read_json(args.project / ".anyasset/config.json")
                store = config["store"]
            manager = AssetManager(store)
            if args.command == "init":
                result = manager.init(args.project, args.source, args.repo)
            elif args.command == "update":
                result = manager.update(args.project, args.ref, args.offline)
            elif args.command == "sync":
                result = manager.sync(args.project, args.offline)
            elif args.command in ("status", "verify"):
                result = manager.status(args.project, verify=args.command == "verify")
            elif args.command == "edit":
                result = manager.edit(args.project, args.destination)
            elif args.command == "doctor":
                result = manager.doctor(args.project)
            elif args.command == "plan":
                result = manager.plan(args.project)
            else:
                result = manager.gc()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (AssetError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc), "code": "ASSET_ERROR"}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
