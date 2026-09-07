# Anygine and AI integration guide

The engine declares inputs; Anyasset provides local paths. Do not embed store paths in C++, use submodules for this system, or checkout versions inside shared views. All project text records and comments use English; user-facing AI development communication uses Chinese.

## Inspected engine context

Initial integration inspected Anygine's Engine branch at b3e32a32. The project uses CMake. Source/Anygine/Assets/Private/DataPresetCatalog.cpp accepts dataRoot and resolves relative paths; root CMake's AnygineRuntimeAssets handles generated shader directories.

The two initial fixtures do not replace existing engine Assets. Do not redirect all Assets/Data to this sample catalog. First register the required contents and preserve their directory contracts. This integration does not modify runtime AssetManager or shader pipelines and does not assume support for an ANYGINE_ASSET_ROOT environment variable.

## First-time setup

Install a fixed tool revision in a dedicated Python environment:

```powershell
python -m pip install "git+ssh://git@github.com/fangzhouRWTH/Anyasset.git@v0.2.0"
```

Alternatively install a local checkout non-editably. Copy examples/engine/assets.toml to the engine and ignore .anyasset/.

```powershell
assetctl init --project <engine-dir> --store <shared-store-dir>

# Only when no lock exists, or an intentional upgrade is requested.
assetctl update --project <engine-dir> --ref <published-asset-commit>

assetctl sync --project <engine-dir> --locked
assetctl verify --project <engine-dir>
```

Optional `--repo <local-asset-repo>` configures a local committed Git/LFS seed without changing its checkout. Uncommitted files cannot be referenced by a lock.

Commit requirements, lock, and caller scripts to the engine. New machines reuse them and run init/sync only. Installed tool revisions are independent of asset revisions.

## AI workflow before development

1. Confirm the engine checkout and Git status; do not modify other worktrees.
2. Read assets.toml and assets.lock.json. If necessary, init using the store supplied by the user/development environment.
3. Run sync --locked, adding --offline when needed. Report missing content instead of falling back to main or unrelated local files.
4. Run verify, then path <logical-id>. status.asset_ids lists the selected dependency closure; inspect catalog.json for the full catalog.
5. Write generated outputs to the build directory. Never modify store/views or store/objects and never run update during ordinary setup.
6. After switching engine branches, sync again; stale bindings are rejected.

```python
import json
import subprocess

result = subprocess.run(
    ["assetctl", "path", "--project", str(engine_root), "tests/triangle"],
    check=True, capture_output=True, text=True, encoding="utf-8")
mesh_path = json.loads(result.stdout)["path"]
# Pass mesh_path to an existing application file argument or configuration field.
```

For Python hosts sharing the installed environment:

```python
from anyasset import resolve_asset
mesh_path = resolve_asset(engine_root, "tests/triangle")
```

Resolution performs no network access or upgrade. For full verification, call AssetManager(...).status(project, verify=True) first.

## CMake integration

Copy examples/engine/Anyasset.cmake into the engine CMake module directory. Requires CMake >= 3.19 and a Python interpreter with anyasset installed.

```cmake
include(CMake/Anyasset.cmake)
anyasset_resolve("${CMAKE_SOURCE_DIR}" "tests/triangle" ANYASSET_TRIANGLE_PATH)
# Use configure_file to write build-local application configuration,
# or pass the result to an existing test command. Do not modify source paths.
```

The module watches requirements, lock, and resolved binding changes. It does not download assets. Run sync before configure; pass paths as argument arrays, including paths containing spaces.

## Multiple local checkouts

```powershell
assetctl init --project <engine-A> --store <same-store>
assetctl init --project <engine-B> --store <same-store>
assetctl sync --project <engine-A> --locked
assetctl sync --project <engine-B> --locked
```

Equal locks share a view; different locks coexist. There is no global current link. Running consumers may continue using older paths; v0.1 does not automatically remove historical views.

## Adding or changing assets

Follow [ASSET_AUTHORING.md](ASSET_AUTHORING.md). Create a separate edit workspace, run LFS pull, update content/catalog, validate, commit, and publish. Test dirty content using an explicit development configuration; automatic dirty binding overrides are not implemented. After asset PR merge, use its final commit for update, sync, verify, and real engine tests. Commit engine changes together with its updated lock. Review changed test baselines independently.

## CI

Install a pinned tool version and configure Git/SSH/LFS access:

```sh
assetctl init --project . --store "$RUNNER_TEMP/anyasset-store"
assetctl sync --project . --locked
assetctl verify --project .
```

Cache the store within the same OS when useful. Re-run init/sync after restoration to generate local paths; do not treat a cached project resolved.json as portable. Do not resolve main in CI or put credentials into requirements. Access to a separate private asset repository requires appropriate read credentials.

## Local engine integration files

Anygine_main contains Scripts/AI/anyasset.py, Scripts/AI/anyasset-requirements.txt, Doc/Development/Anyasset.md, and root requirements/lock files. These are a reviewable integration starting point, not an engine asset-system migration. Asset-tool changes are published to Anyasset; engine changes remain in their separate repository for review.
