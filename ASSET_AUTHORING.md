# Asset classification and authoring

This guide describes the implemented v0.1 workflow. There is no asset-add command, automatic folder indexing, tag search, or graphical catalog editor. Add files and edit catalog.json, then validate and commit. Write documentation, comments, metadata prose, and commit messages in English; communicate with the user in Chinese during AI-assisted development.

## Three classification layers

| Layer | Responsibility | Example |
| --- | --- | --- |
| Physical directory | Keep related files together and preserve relative file references | content/models/props/crate/ |
| Asset ID | Stable logical identity independent of machine-local absolute paths | models/props/crate |
| Collection | Reusable selection for a task, feature, or test suite | tests/model-import |

An asset ID represents one logical resource, which may require multiple files. Every asset declares one entry file; files lists its complete owned inputs, and depends lists other asset IDs. Collections list asset IDs, not filenames. The manager recursively includes dependencies, detects dependency cycles, and deduplicates shared file paths.

Changing collection membership changes the selected contents only when an engine explicitly updates its lock. Existing locked engines keep their original selection. Renaming an ID requires consumer changes; relocating files while preserving the ID still requires a new asset commit and lock update.

## Current catalog

| Asset ID | Entry | Collections |
| --- | --- | --- |
| defaults/checker | content/defaults/checker.png | defaults, smoke |
| tests/triangle | content/tests/triangle.obj | tests/model-import, smoke |

The checker is tracked with LFS; the small OBJ is ordinary Git text. Inspect catalog.json to see all available entries. assetctl status --project <engine-dir> reports only the currently selected asset_ids, including dependencies.

## Suggested categories

These are conventions, not a required pre-created directory tree:

| Directory / ID prefix | Intended contents |
| --- | --- |
| defaults/ | Minimal fallback resources needed for basic setup |
| models/ | Reusable model packages |
| textures/ | Shared textures and environment maps |
| materials/ | Material descriptions and their required inputs |
| scenes/ | Standard scenes and scene packages |
| audio/ | Audio inputs |
| tests/ | Small regression and edge-case fixtures |
| benchmarks/ | Large performance inputs, selected explicitly |

Use lowercase portable names. Collections should express usage such as defaults, tests/model-import, tests/animation, benchmarks/rendering, or smoke. A crate model can appear in both a demo and an importer test collection without storing duplicate source files. Do not add large optional inputs to defaults.

## Add an asset: complete workflow

### 1. Use an author checkout

Work in the asset repository or create a separate author checkout from an engine's lock:

```powershell
assetctl edit --project <engine-dir> --destination <new-author-directory>
```

In the new author directory, run git lfs pull before editing binary assets. The edit command creates an asset-edit branch. When using an existing clean author checkout, create your own feature branch:

```powershell
git switch -c add-crate-model
git lfs install --local
```

Never edit store/views or store/objects. They are shared consumer/cache data, not author workspaces.

### 2. Add files and configure LFS

For a self-contained model, place crate.glb under content/models/props/crate/. For a multi-file format, place the model, buffers, textures, and sidecars in a package directory that preserves relative references.

The repository already tracks common binary formats, including GLB, with LFS. For a new binary type, configure a scoped rule before git add:

```powershell
git lfs track "content/**/*.ktx2"
```

Commit .gitattributes together with the asset if rules changed. Adding a rule does not migrate old Git history. Ordinary Git blobs larger than 16 MiB are rejected during lock resolution.

### 3. Register the asset and collection

Add an entry under catalog.json's assets object. This is a JSON fragment; replace the license and origin placeholders with actual provenance before publishing:

```json
"models/props/crate": {
  "entry": "content/models/props/crate/crate.glb",
  "files": ["content/models/props/crate/crate.glb"],
  "depends": [],
  "license": "<actual-license>",
  "origin": "<actual-author-or-source-and-upstream-version>"
}
```

Append models/props/crate to a collection, preserving existing members:

```json
"tests/model-import": ["tests/triangle", "models/props/crate"]
```

For external textures, either list them in this asset's files or register a reusable texture asset and name it in depends. The texture asset must exist and declare its own files. Directory contents are not automatically included. The entry must belong to the asset's own files.

Keep units, coordinate conventions, color space, upstream revision, and license evidence with the asset when relevant. Include required metadata/license attachments in files if consumers need them. Do not substitute placeholder licenses for actual permissions.

### 4. Validate and publish

From the author checkout:

```powershell
python -m anyasset catalog-check --repo .
git add catalog.json .gitattributes content/models/props/crate
git diff --cached --check
git diff --cached --stat
git lfs ls-files
git commit -m "Add crate model to importer test assets"
git push -u origin HEAD
```

Use the installed tool environment if this author checkout does not provide an importable tool package. Run integration tests for manager/contract changes, and validate new assets with the relevant engine importer/test separately. catalog-check validates structure and file presence; it does not prove format support, licensing, or every format-specific external reference. update performs committed-file and LFS-pointer validation.

Merge the asset PR first if your workflow uses PRs. Use the final merged commit after squash/rebase. Ensure Git and LFS content are available remotely before publishing engine references.

### 5. Adopt the published revision in the engine

If the new asset is in an already requested collection, assets.toml needs no change. If it is in a new collection, add that collection to assets.toml first.

```powershell
assetctl update --project <engine-dir> --ref <published-full-commit>
assetctl sync --project <engine-dir> --locked
assetctl verify --project <engine-dir>
assetctl path --project <engine-dir> models/props/crate
```

Run the engine tests, review assets.lock.json, and commit it together with the engine changes and any declaration changes. Normal initialization remains sync --locked; it must not adopt main automatically.

When init configured --repo, the seed must contain the requested published commit. Fetch the merged branch into the seed first, or re-run init without --repo to use the remote source directly.

## Modify, retire, and reorganize

- Modify files under the same logical ID when the resource identity remains meaningful; publish a new commit and explicitly update consumers.
- Add required companion files/dependencies at the same time as the main file change.
- Before removing an ID or moving it between collections, identify affected consumers. Old locks remain valid only while the old Git/LFS data remains available.
- Never move a published release tag or overwrite a shared view to represent a new version.
- Multi-asset semantic versioning, automatic reference discovery, and asset registration commands are future extensions, not current behavior.
