# Anyasset — Development assets for Anygine

Anyasset manages standard resources, test inputs, and shared reference data for engine development. Engines commit declarations and exact locks; a local manager provides versioned snapshots shared by multiple projects. This is separate from the engine's runtime AssetManager and does not use submodules.

**Status: tool v0.2.0, schemas 1 and 2. Requires Python 3.11+, Git, and Git LFS.** There are no third-party Python runtime dependencies. External local libraries are supported through metadata-only indexes; see [EXTERNAL_LIBRARIES.md](EXTERNAL_LIBRARIES.md). The catalog now includes the original PNG checker/OBJ triangle plus existing Anygine test inputs, terrain textures and lookup data. The default-source release also publishes the adopted engine, local and robot inputs through Git/LFS; historical metadata-only indexes remain available to old locks. See [the Anygine library](ANYGINE_LIBRARY.md) for exact scope and entry IDs. Distribution tests do not establish engine importer compatibility.

## Quick start

```powershell
git clone git@github.com:fangzhouRWTH/Anyasset.git Anyasset
cd Anyasset
git lfs install --local
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .

# Bind an engine checkout to a shared local store.
.\.venv\Scripts\assetctl.exe init --project D:/projects/Anygine/Anygine_main --store D:/AssetStore/Anyasset

# Run update only for initial resolution or an intentional dependency upgrade.
.\.venv\Scripts\assetctl.exe update --project D:/projects/Anygine/Anygine_main --ref main
.\.venv\Scripts\assetctl.exe sync --project D:/projects/Anygine/Anygine_main --locked
.\.venv\Scripts\assetctl.exe verify --project D:/projects/Anygine/Anygine_main
.\.venv\Scripts\assetctl.exe path --project D:/projects/Anygine/Anygine_main defaults/checker
```

On Linux/macOS use `.venv/bin/assetctl`. Contributors may install with `python -m pip install -e .`; consumers should install a pinned, non-editable tool version so changing an author checkout does not change their tools. `python scripts/assetctl.py ...` is also available but executes the current source checkout.

Commit `assets.toml` and `assets.lock.json` to the engine. Ignore `.anyasset/` and the local author repository directory. Do not commit caches, resolved absolute paths, or nested Git repositories. A new machine with an existing engine lock runs `init` and `sync --locked`, not `update`.

## Asset classification

Classification has three independent layers:

| Layer | Example | Purpose |
| --- | --- | --- |
| Physical files | `content/tests/triangle.obj` | Organize source files by purpose and preserve relative references |
| Stable asset ID | `tests/triangle` | Identify a logical asset, its entry, files, and dependencies |
| Collection | `tests/model-import` | Select a reusable group of assets for a development task |

An asset may appear in several collections. Collection membership does not copy files. The manager expands dependencies and deduplicates file paths. IDs and collections are maintained explicitly in `catalog.json`; there is no automatic directory scanning, tagging UI, or `assetctl add` command in v0.1.

Current collections:

| Collection | Members |
| --- | --- |
| `defaults` | `defaults/checker` |
| `tests/model-import` | `tests/triangle` |
| `smoke` | Both initial assets |
| `anygine/core` | Engine fixtures, checker and LTC lookup |
| `anygine/terrain` | Eight PBR kits and the engine terrain manifest |

See [ASSET_AUTHORING.md](ASSET_AUTHORING.md) for category conventions and a complete add/publish/adopt example.

## Core contracts

1. Locks identify the source, full commit, selected collections, complete dependency closure, file SHA-256/size/LFS status, and logical entry mappings.
2. All projects using one store reuse its verified content objects. Additional consumers do not re-download cached bytes.
3. `views/<lock-digest>/` is never upgraded in place. Equal locks share a view; different locks have distinct views.
4. Absolute local paths exist only in `.anyasset/resolved.json`. Production declarations use portable repository URLs.
5. `update` changes the lock; `sync --locked` restores it; `path` is read-only and performs no network access.
6. Views are read-only by contract, not protected by OS ACLs in v0.1. External edits are detected by `verify` and `sync`.
7. Store mutations use an OS lock with a 30-second acquisition timeout. Process exit releases the lock; retry after contention.

## Repository map

| Path | Responsibility |
| --- | --- |
| `catalog.json` | Asset definitions, dependencies, provenance, licenses, collections |
| `content/` | Versioned input files |
| `anyasset/` | Python API and CLI |
| `schemas/` | JSON Schema contracts, including the parsed TOML data model |
| `scripts/` | Source launcher, fixture generator, validation scripts |
| `examples/engine/` | Python/CMake integration and dependency declaration examples |
| `tests/` | Temporary local Git/LFS integration fixtures; no production credentials required |
| `.github/workflows/ci.yml` | Windows/Linux and Python 3.11/3.12 validation |

Documentation:

- [EXTERNAL_LIBRARIES.md](EXTERNAL_LIBRARIES.md): local task libraries with metadata-only sharing.
- [CHANGELOG.md](CHANGELOG.md): release changes.
- [ASSET_AUTHORING.md](ASSET_AUTHORING.md): classification and adding assets.
- [ANYGINE_INTEGRATION.md](ANYGINE_INTEGRATION.md): engine and AI workflows.
- [INTERFACES.md](INTERFACES.md): CLI, Python API, data formats, errors.
- [ARCHITECTURE.md](ARCHITECTURE.md): caching, concurrency, recovery, retention.
- [MAINTENANCE.md](MAINTENANCE.md): releases, backup, troubleshooting.
- [AGENTS.md](AGENTS.md): contributor and language policy.

## Routine operations

```powershell
assetctl sync --project <engine-dir> --locked
assetctl sync --project <engine-dir> --locked --offline
assetctl status --project <engine-dir>

# Intentional upgrade to an already published revision.
assetctl update --project <engine-dir> --ref <asset-tag-or-full-commit>
assetctl sync --project <engine-dir> --locked
assetctl verify --project <engine-dir>

# Separate authoring workspace; never edit shared views.
assetctl edit --project <engine-dir> --destination <new-author-directory>
assetctl gc --store <store-dir> --dry-run
```

Optional local seed: `init ... --repo <local-asset-repository>`. Git revisions are fetched from that repository; network-enabled sync can import verified seed LFS objects before fetching remaining objects remotely. Network-enabled means permitted, not required. Offline sync requires LFS content already in the shared store and does not import missing seed objects. Re-run init without `--repo` to remove the seed binding.

## Validation

```powershell
python -m unittest discover -s tests -v
python -m anyasset catalog-check
```

Tests cover multi-project reuse, multiple revisions, rollback, offline operation, LFS fetch/seed import, dependency closure, invalid locks and paths, corruption, concurrent processes, interrupted publication, and isolated editing.

## Initial scope and limits

- One engine lock selects one Git source commit plus optional indexed external libraries. There is no cross-library dependency solver or per-asset version-range resolution.
- Content objects are deduplicated; snapshot files are ordinary copies and can duplicate disk usage across revisions. No hard links.
- External glTF/USD/FBX references must be explicitly included through `files`/`depends`; no automatic format-specific reference discovery.
- No asset-provided build scripts/hooks are executed during consumption; no importer, baking pipeline, or derived cache is included.
- No automatic dirty-workspace override. Test edits in a separate workspace, publish, then update the lock.
- GC is preview-only. Historical project bindings and Git refs are retained conservatively.
- Stores must reside on a local disk. Network filesystem lock/atomicity semantics are not guaranteed.
- Local caching reduces repeated downloads but does not eliminate remote LFS historical storage costs.

## Language and licensing

Repository documentation, comments, docstrings, metadata prose, and commit messages are written in English. Communication with the user while collaborating with AI is in Chinese. Keep third-party source names and required attribution verbatim when necessary.

The two original catalog fixtures are provided under CC0-1.0. Record each third-party asset's actual license and origin; never label unknown content CC0. The repository owner has not selected an open-source license for the tool code. Public visibility alone does not grant one.
