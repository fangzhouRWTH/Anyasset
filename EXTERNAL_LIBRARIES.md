# External libraries: metadata in Git, payloads outside Git

Available in Anyasset 0.2.0. Existing schema-1 engines remain supported. External libraries use requirements/lock/binding schema 2 and external-index schema 1.

## Purpose and boundaries

Use an external library for large, frequently changing, task-specific inputs that should not be uploaded with Anyasset. A library can be an ordinary local directory; it does not need Git or LFS. Anyasset tracks its logical ID, version, catalog, file sizes, and content hashes. The source directory and payload never enter the generated index.

This is a local-directory provider, not a plugin execution system. The tool never runs scripts supplied by an external library. It never uploads external payloads, automatically discovers private libraries, or copies them into the author Git checkout.

For another machine to consume the same revision, separately deliver the matching files using an approved disk/NAS/file service and bind its local path. An index is not a download service or backup. Private asset names and provenance can also be sensitive: review metadata before committing an index to a shared/public repository.

## Model

```text
External author directory        Anyasset Git repository
  catalog.json                     external-indexes/<id>/<version>.json
  content/... (large files)  -->    metadata only: IDs, catalog, hashes, sizes
                                           |
                                    Engine schema-2 lock
                                           |
Machine-local library-bind --> Verified shared objects --> Versioned view
                                                           |
                                              path <library-id>::<asset-id>
```

The engine and index contain no source machine's absolute root. A machine-local binding maps (library ID, version) to a directory. A content-derived revision fingerprint additionally identifies the complete index; a version label alone cannot silently substitute different bytes.

Consumers use verified copies in immutable-by-contract views, not live author directories. Source edits therefore do not change already prepared branches. Selected bytes are cached once as objects and copied into each distinct combined view. This trades disk space for reproducibility; v0.2 does not offer zero-copy live mounts or reflinks. Large frequently changing libraries should be split into focused collections and indexed only at meaningful checkpoints.

## 1. Prepare an external directory

Use the same catalog schema as standard assets. The root contains content/ and a catalog file:

```text
D:/TaskData/robot-lab/
  catalog.json
  content/robots/robot-a/model.glb
```

Example catalog (replace provenance and license with real values):

```json
{
  "schema": 1,
  "assets": {
    "robots/robot-a": {
      "entry": "content/robots/robot-a/model.glb",
      "files": ["content/robots/robot-a/model.glb"],
      "depends": [],
      "license": "<actual-license>",
      "origin": "<actual-source>"
    }
  },
  "collections": {"robot-tests": ["robots/robot-a"]}
}
```

The first provider uses portable content/-relative catalog paths; existing differently structured data needs a catalog-compatible layout. External references must be listed explicitly. External files may exceed the ordinary Git 16 MiB limit because payloads never enter Git. A source containing LFS pointer text must be materialized before indexing.

## 2. Generate and publish an index

From the Anyasset author repository, using the installed 0.2.0 environment:

```powershell
assetctl library-index --id robot-lab --library-version v1 --root D:/TaskData/robot-lab --catalog D:/TaskData/robot-lab/catalog.json --output external-indexes/robot-lab/v1.json
python -m anyasset catalog-check --repo .
git add external-indexes/robot-lab/v1.json
git commit -m "Index robot-lab v1 external assets"
git push
```

Only the JSON index is added. Indexing reads and hashes all declared files; it does not copy or upload them. Re-indexing the same output with identical metadata is idempotent. Different content requires a new version/output. Catalog validation rejects conflicting checked-in indexes with the same ID/version.

Do not index actively changing files. The indexer detects ordinary size/mtime changes while hashing, and import verifies the resulting bytes again. For a reproducible external release, retain the actual indexed files outside Git using your backup/version retention policy.

## 3. Declare the engine dependency

```toml
schema = 2
source = "git@github.com:fangzhouRWTH/Anyasset.git"
collections = ["defaults"]

[[external]]
id = "robot-lab"
index = "external-indexes/robot-lab/v1.json"
collections = ["robot-tests"]
```

Add additional [[external]] tables for other libraries, each with a unique ID. Indexes are resolved from the same exact Anyasset commit as standard assets; they are not read from whatever happens to be in a local author checkout.

```powershell
assetctl update --project <engine-dir> --ref <published-index-commit>
```

Update resolves metadata without requiring the external payload or a local binding. Commit the resulting assets.toml and assets.lock.json to the engine. The lock contains each selected external file's hash/size, entry mapping, index path, library version, and index revision.

## 4. Bind on each machine and consume

```powershell
assetctl library-bind --store D:/AssetStore/Anyasset --id robot-lab --library-version v1 --root D:/TaskData/robot-lab
assetctl plan --project <engine-dir>
assetctl sync --project <engine-dir> --locked
assetctl verify --project <engine-dir>
assetctl path --project <engine-dir> robot-lab::robots/robot-a
```

The bind command only records local configuration; actual file/hash validation occurs during sync. Missing or mismatched source bytes fail explicitly without publishing a partial binding. Bind multiple versions to distinct retained directories when both are needed. On another machine --root can be entirely different while id/version and file bytes remain the same.

Standard IDs remain unchanged, e.g. defaults/checker. External IDs use library-id::asset-id, preventing collisions between standard and external libraries or between two external libraries. Python resolve_asset and the CMake adapter accept the same namespaced IDs.

## Offline, updates, and recovery

- Offline means no network. External local imports are allowed offline when Git/index metadata is cached; the indexed source can be read from its local binding.
- Once objects are cached, new views can be prepared without the external source. Complete views do not require a library binding to resolve paths.
- Changed author files never update a published view. Generate a new index/version, publish metadata, explicitly update the engine lock, and sync.
- Rolling back the engine lock restores its original exact selection if the view, objects, or matching external files are retained.
- If indexed bytes were changed and no matching cache/backup remains, the old version cannot be reconstructed from hashes. Report the missing version; never substitute current files.
- doctor reports failures without mutation. Automatic repair/deletion remains outside this release.

## Public extension API

```python
from anyasset.libraries import index_library, bind_library
from anyasset import AssetManager, resolve_asset

index_library(root, catalog_path, library_id, version, output_path)
bind_library(store, library_id, version, root)
AssetManager(store).sync(engine_project, offline=True)
path = resolve_asset(engine_project, "robot-lab::robots/robot-a")
```

IDs and versions use lowercase alphanumeric/dot/underscore/hyphen tokens of at most 80 characters. Cross-library dependency references and version-range solving are not implemented: each library expands its own catalog closure, and the engine explicitly lists the libraries it needs. Remote providers can later implement object retrieval while preserving these index/lock contracts.
