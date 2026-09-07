# Interface contracts v1

Tool version `0.2.0` supports schema 1 and schema 2. Schema 2 adds external libraries; old locks remain supported. Requires Python 3.11+. Successful CLI calls emit one UTF-8 JSON object to stdout and exit 0. Operational/file/data failures emit `{"code":"ASSET_ERROR","error":"..."}` to stderr and exit 2. Argparse usage failures print help and exit 2. Captured Git subprocess output does not contaminate successful JSON output. Progress messages may appear on stderr during successful fetch/clone operations; use the exit code to determine success.

## CLI

Project commands accept `--project <directory>` (default cwd) and `--store <directory>`. Without `--store`, the manager reads `.anyasset/config.json`. First-time init requires an explicit store. See EXTERNAL_LIBRARIES.md for library-index and library-bind commands. plan reports selected entries and missing cached bytes without downloads; doctor returns healthy/status or error/actions without repair. A doctor result with healthy=false still exits 0 as a completed diagnostic query.

| Command | Additional arguments | Effects | Main result fields |
| --- | --- | --- | --- |
| `init` | Optional `--source <url>` (default Anyasset SSH URL), `--repo <local-seed>` | Create declaration if absent; write local config; no lock update | project, store, source |
| `update` | Required `--ref <branch/tag/full-SHA>`; optional `--offline` | Write lock and cache Git metadata; no LFS content download | Full lock |
| `sync` | Required `--locked`; optional `--offline` | Prepare exact contents, verify, publish view and binding | schema, lock_digest, root, assets |
| `status` | None | Inspect under the store lock | current, commit, snapshot, root, asset_ids, verified=false |
| `verify` | None | Verify binding and hash all selected files | Same as status, verified=true |
| `path` | Positional `<asset_id>` | No mutation or network | asset_id, path |
| `edit` | Required `--destination <new-directory>` | Create separate author Git checkout | workspace, commit, next |
| `gc` | Required `--dry-run` | Preview only; no deletion | retained, unreferenced_snapshots, dry_run |
| `catalog-check` | `--repo <directory>`, default cwd | Check working catalog and referenced files | valid, assets, collections |

`status` with `current=false` is a successful query, not a ready-to-build assertion. Use `verify` or `path` failure codes to stop builds. `path` checks declaration/lock/binding consistency and entry existence, not all file hashes. There is no implicit latest resolution, automatic upgrade, asset-add command, or full-catalog query CLI; inspect catalog.json for all assets and status.asset_ids for the selected closure.

## Python API

```python
from anyasset import AssetManager, AssetError, resolve_asset

manager = AssetManager("D:/AssetStore/Anyasset")
manager.init("D:/engine", source="git@github.com:fangzhouRWTH/Anyasset.git")
lock = manager.update("D:/engine", ref="main")  # Explicit upgrades only.
binding = manager.sync("D:/engine", offline=False)
status = manager.status("D:/engine", verify=True)
path = resolve_asset("D:/engine", "defaults/checker")  # pathlib.Path
```

Public signatures:

```python
AssetManager(store: str | Path)
init(project, source=DEFAULT_SOURCE, repo=None) -> dict
update(project, ref, offline=False) -> dict
sync(project, offline=False) -> dict
status(project, verify=False) -> dict
edit(project, destination) -> dict
gc() -> dict
plan(project) -> dict
doctor(project) -> dict
resolve_asset(project, asset_id) -> Path
```

Underscore-prefixed methods are internal. Expected operational failures raise AssetError; Python hosts should also handle OSError for disk/permission failures. The API does not normalize every arbitrary malformed Python input; the CLI normalizes common input errors.

## Catalog

See [catalog.schema.json](schemas/catalog.schema.json) and [ASSET_AUTHORING.md](ASSET_AUTHORING.md).

Each stable asset ID maps to entry, files, optional depends, license, and origin. Entry must belong to the asset's own files. Dependencies expand recursively and must be acyclic. Collections list asset IDs. Include textures, sidecars, external buffers, required license attachments, and every other required input explicitly; directories are not implicitly included. Assets may share files, deduplicated by path.

Paths are POSIX relative paths under content/. Reject absolute paths, traversal, backslashes, Windows reserved names, trailing spaces/dots, case collisions, glob characters, and commas. Resolution rejects Git symlinks, submodules, and ordinary Git blobs larger than 16 MiB. Use LFS for large files. Only standard SHA-256 LFS pointers are supported; pointer extensions are unsupported.

## Engine requirements: assets.toml

```toml
schema = 1
source = "git@github.com:fangzhouRWTH/Anyasset.git"
collections = ["defaults", "tests/model-import"]
```

The source participates in version identity. Use a canonical portable URL; use init --repo for machine-local seeds. Every declaration field contributes to requirements_digest, so declaration changes require explicit update. Version ranges are unsupported; update receives the ref explicitly.

## Engine lock: assets.lock.json

See [lock.schema.json](schemas/lock.schema.json). Generated by the tool; do not hand-edit hashes to accept mismatched contents.

- commit: full 40-character SHA-1 source commit.
- requirements_digest: canonical SHA-256 of parsed requirements.
- collections: sorted unique collection names.
- files: sorted by path, with path, sha256, size, and lfs.
- assets: logical IDs in the dependency closure mapped to entry paths.

Canonical JSON is UTF-8 output of Python `json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False)`. lock_digest hashes the complete canonical lock. File hashes cover actual bytes for both Git and LFS contents. Materialization preserves Git blob bytes without newline conversion.

A lock provides consistency and reproducibility, not a signature or a replacement for trusted-source review and repository permissions.

## Machine-local data

`.anyasset/config.json`: schema, absolute store, optional absolute repo seed.

`.anyasset/resolved.json`: schema, lock_digest, absolute root, and logical IDs mapped to absolute asset paths. See [binding.schema.json](schemas/binding.schema.json). Consumers must reject stale lock digests; using the public API/CLI handles this check.

`bindings/<project-id>.json` retains all snapshots referenced by that project; `snapshot.json` stores the full lock. These are internal records and must not be edited directly.

## Runtime controls and external libraries

ANYASSET_GIT_TIMEOUT_SEC defaults to 300; ANYASSET_LOCK_TIMEOUT_SEC defaults to 30. Values must be positive and below 86400 seconds. Git timeouts stop the child process tree and preserve completed cached data. Locks still serialize store mutation; increase the lock wait for a deliberate large import. Hashing/copying are not bounded by the Git timeout.

Schema-2 external fields and APIs are documented in [EXTERNAL_LIBRARIES.md](EXTERNAL_LIBRARIES.md), with machine-readable contracts in schemas/external-index.schema.json and the extended requirements/lock/binding schemas. plan hashes cached objects when estimating missing content; it is not a constant-time query. Its missing_unique_bytes includes local-import and Git-object bytes, not just network download bytes.
