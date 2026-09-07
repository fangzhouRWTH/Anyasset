# Architecture and reliability

## Data flow

```text
assets.toml --explicit update(ref)--> assets.lock.json
                                          |
                                     sync --locked
                                          |
             managed bare Git repo -> selected file records
                                          |
                   shared SHA-256 objects (Git/LFS)
                                          |
                         staging directory + verification
                                          |
                              views/<lock-digest>
                                          |
                    per-project .anyasset/resolved.json
```

## Why consumer snapshots are not worktrees

The implementation reads committed Git blobs and LFS pointers and materializes selected files, rather than checking out a complete consumer worktree. It exposes declared content only, avoids automatic smudge downloads of every LFS file, and never switches a shared consumer HEAD or executes author scripts. The edit command creates a real separate author checkout.

## Store layout

```text
store/
  manager.lock               Persistent file; lock ownership is held by the OS
  repos/<source-digest>.git   Managed bare repository
  objects/aa/bb/<sha256>      Shared Git/LFS content address space
  views/<lock-digest>/        Published snapshot, immutable by contract
    snapshot.json
    content/...
  views/.prepare-*/           Unpublished staging directories
  bindings/<project-id>.json
```

Managed repositories set lfs.storage to the store root. LFS and ordinary asset objects use the same SHA-256 directory layout. Author repository LFS configuration is not changed. Never run independent git lfs prune against this store: LFS does not know all cross-project/source references.

## Restore algorithm

1. Acquire the store OS lock and check requirements/lock consistency.
2. For an existing view, verify metadata and selected file hashes before refreshing the binding.
3. Otherwise obtain the exact commit, resolve its catalog, and compare the result to the lock.
4. Reuse verified objects; retrieve ordinary files from Git and LFS contents from a seed or remote.
5. Fetch only missing selected LFS paths. Initial implementation uses one fetch per missing file; batching is a future optimization.
6. Copy to staging, verify size/hash, and publish using a same-filesystem rename.
7. Save retention references before atomically replacing the project binding.

Repeated calls are idempotent. An unchanged lock never queries main for upgrades. A complete view works offline without the source repository. Cached Git metadata alone is insufficient when LFS contents are missing.

## Concurrency and isolation

Mutations use a global store lock, including Git/LFS retrieval, materialization, registration, and GC preview. Different versions do not download concurrently in v0.1; acquisition timeout errors can be retried. OS lock release does not depend on deleting a PID file.

Snapshots use copies, not hard links. Editing one view cannot corrupt its cached source object or another view. Projects with the same lock do share one view, so an external edit affects those consumers. Edit only separate author workspaces. Views have no enforced OS read-only ACL in v0.1.

Store/config files are trusted local state, not a sandbox against hostile processes running as the same user. Catalog validation rejects escaping paths, nonregular Git entries, and nonportable names. Consumption does not execute repository-provided code. Ordinary Git blobs are capped at 16 MiB.

## Crashes and corruption

Cached complete objects survive interruption. Incomplete staging directories never become bindings. After stopping all tools, maintainers may inspect/remove abandoned .prepare-* directories; published views are separate.

Corrupted views fail verification and are not repaired in place. Stop processes using the view, quarantine the corrupted directory, then sync again. Do not replace files under a running consumer. Hash verification is not a guarantee of whole-store transactional durability across power loss; verify and rebuild after storage failures.

## Retention and backup

All historical project bindings are retained to protect old processes after a branch switch. GC only reports unreferenced snapshots; it does not delete. refs/anyasset/retained/<commit> retains cached Git commits. Do not rewrite published history referenced by engines.

A local cache is not a backup. Remote backup must include required Git refs and actual LFS objects. Git pointers alone cannot restore assets. Prepare target versions before going offline. Separate machines have separate caches and each needs its initial download.

## Extension points

Future changes may add HTTP/S3 object retrieval, reflink materialization, finer object/view locks, explicit pins, process leases, and retention policies. Incompatible schema changes need a new version. Derived caches need separate keys including source hashes, importer revision, settings, and target platform.
