# Maintenance and releases

## Asset changes

Follow [ASSET_AUTHORING.md](ASSET_AUTHORING.md) for the complete classification and add/publish/adopt workflow. Keep metadata, documentation, and comments in English. Use the actual license and source attribution; preserve mandatory third-party attribution verbatim when necessary.

Do not add large benchmark suites to defaults. Declare external references explicitly. Configure LFS before adding matching files; tracking new patterns does not migrate existing Git history. Ordinary Git blobs larger than 16 MiB are rejected by the resolver.

## Tool releases

1. Keep pyproject version, __version__, and CLI version consistent.
2. Preserve schema compatibility; assign a new schema for breaking changes and document migration.
3. Run integration tests and Windows/Linux CI. Verify the installed CLI as well as source execution.
4. Commit and push, then create an immutable release tag, such as v0.1.0.
5. Consumers install a fixed tag or full commit. Asset-only changes do not require a new tool version.

Documentation-only changes can be pushed to main without moving existing release tags or updating engine asset locks. Historical releases retain their original contents.

Update does not upload assets. Publish both the asset commit and its LFS objects before publishing an engine lock that references them. Do not force-push away published history. Write commit messages and release notes in English.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Stale binding | Check the engine branch and run sync --locked |
| Changed requirements | If intentional, run update, review the lock, then sync |
| Missing LFS content offline | Complete sync with a remote/local seed first; never bypass by changing hashes |
| Private repository fetch failure | Check Git/SSH/LFS read access; interactive Git credential prompts are disabled |
| Corrupt snapshot | Stop consumers, quarantine the view, then rebuild with sync |
| Store busy | Wait for the active operation, then retry; do not delete the lock file |
| Windows path errors | Use a short store root and portable relative paths without case collisions |
| Ordinary Git file over 16 MiB | Track with LFS and commit correctly; plan historical migration separately |
| Pointer files in an edit checkout | Run git lfs pull there before editing or importing |

## Storage and cleanup

`assetctl gc --store <path> --dry-run` previews only. Historical bindings deliberately remain retained; there is no automatic destructive collection. Do not run prune, checkout, reset, or LFS prune inside managed repositories.

To rebuild a cache, stop consumers and tools, ensure sources are backed up, and initialize a new store. Deleting an old store is a separate maintenance action after confirming its exact scope. Content that exists only in the old store must not be assumed reconstructible.

## Backups

- Preserve required Git refs and LFS contents. A Git bundle or bare mirror alone is incomplete.
- `git lfs fetch --all` downloads historical data and consumes bandwidth; use it for dedicated backups, not normal initialization.
- Periodically restore historical engine locks from a clean machine without the author checkout.
- Never delete remote content still referenced by published engine revisions.

## Tests

```powershell
python -m unittest discover -s tests -v
python -m anyasset catalog-check
```

Tests use temporary local Git/LFS repositories without GitHub network access. Add behavior-level tests for new capabilities, especially multi-project, offline, corruption, interruption, and concurrency. Never use tests to clean production data. Data-distribution tests do not establish engine format compatibility.

## 0.2 reliability and external-library operations

Use assetctl doctor --project <engine-dir> for actionable diagnostics and assetctl plan --project <engine-dir> for selected entries, unique missing cached bytes, and external revisions. Both are observational; doctor does not repair views or delete data.

For slow networks set ANYASSET_GIT_TIMEOUT_SEC deliberately. Set ANYASSET_LOCK_TIMEOUT_SEC when concurrent consumers need to wait longer for large imports. Batch fetching reduces process/network startup overhead, but full hash verification and snapshot copies still scale with selected bytes.

External library publication shares only reviewed index metadata. Keep payloads and their version backups outside the Anyasset checkout. Refer to EXTERNAL_LIBRARIES.md before registering libraries or rotating external directories. Never replace a version's indexed contents in place without preserving the old bytes.
