# Anygine development inputs: first adoption

The 2026-09-08 catalog adopts existing engine inputs without replacing the native asset system.
Anygine's `asset_animation` branch provides the optional development resolver and real consumer
tests. Existing engine source files remain available as independent fixtures and migration oracles.
The original `defaults`, `tests/model-import` and `smoke` collections retain their membership.

## Standard Git/LFS collections

| Collection | Contents |
| --- | --- |
| `anygine/core` | Original glTF Triangle and TransparentSwatch closures, two small USDA fixtures, engine checker PNG, renderer LTC lookup/manifest/license |
| `anygine/terrain` | Eight Poly Haven 1K PBR kits, the engine terrain manifest, authorship and CC0 source record |

Together with the original two sample assets the standard catalog contains 17 logical assets,
61 files and 61,705,529 source bytes. Source paths below `content/anygine/Assets/` preserve the
engine's relative references. The LTC license and binary tables preserve the exact manifest hashes.
Engine-authored fixtures with no declared general asset license are recorded as `NOASSERTION`;
publishing them here does not assign CC0 or replace their owner's terms. Terrain kits retain their
recorded CC0 terms. Third-party lookup terms and paper attribution remain in the original files.

Useful entry IDs include `tests/anygine/test-triangle`, `tests/anygine/transparent-swatch`,
`textures/anygine/checker`, `textures/terrain/library`, `textures/terrain/forest-ground-05`,
and `renderer/anygine/ltc-ggx`. Successful distribution does not establish USDA/OBJ/EXR runtime
support; engine format/profile gates remain separate.

## Indexed external libraries

All following indexes have library version `2026-09-08-v1`. Only metadata is published here.

| Library ID | Assets / files / source bytes | Contents |
| --- | --- | --- |
| `anygine-engine` | 3 / 11 / 13,781,385 | Existing Blender vegetation/rock sources and an additional checker texture with incomplete local license records |
| `anygine-local` | 24 / 272 / 8,168,174,296 | Existing local model/scenes, Chess, Watch, Sponza variants/textures, skyboxes and Rover sidecar/visuals |
| `anygine-robots` | 36 / 456 / 414,416,906 | Four Menagerie robots, TITA/TITATIT models, policy packages and the existing engine preset catalog |

Index paths are `external-indexes/<library-id>/2026-09-08-v1.json`. Each has an `all` collection.
`anygine-local` additionally has focused `benchmarks` and `robots` selections; `anygine-robots`
has `menagerie` and `direct-drive`. Dependencies retain complete package files including license,
source and configuration records. Some entries intentionally retain additional authoring variants.

Examples:

- `anygine-local::models/abeautifulgame/abeautifulgame.glb`
- `anygine-local::models/sponza/newsponza_main_gltf_003.gltf`
- `anygine-local::bots/demo/demo_rover.robot.json`
- `anygine-robots::catalog/presets`
- `anygine-robots::robot.menagerie.unitree_go2.scene`
- `anygine-robots::robot.direct_drive.tita.mjcf`
- `anygine-robots::policy.direct_drive.tita.onnx`

Source licenses are preserved per package. In particular, deployment robot/policy metadata does
not infer MIT from separate training repositories, and unspecified local asset rights are recorded
explicitly. Payloads with these restrictions are not added to Git/LFS. The index itself is not a
download service: another machine must obtain matching authorized files or reuse prepared objects.
SDK binaries, build outputs and upstream training/source workspaces are excluded from this release.

## Prepare and consume

Declare required collections in a schema-2 project, resolve a published exact commit with explicit
`update`, and bind retained catalog-compatible local libraries. `library-bind` receives their local
root, with `catalog.json` and `content/engine`, `content/local` or `content/robot-data` underneath.
The Anygine `stage-development-library.py` helper can reconstruct these trees from exact indexed
bytes without moving the original sources. Its plan output reports file/byte requirements first.

```sh
assetctl library-bind --store <store> --id anygine-local \
  --library-version 2026-09-08-v1 --root <retained-local-release>
assetctl sync --project <engine-selection-project> --locked
assetctl verify --project <engine-selection-project>
assetctl path --project <engine-selection-project> \
  anygine-local::models/abeautifulgame/abeautifulgame.glb
```

Use the engine's separate benchmark/robot/complete selection projects for larger sets. Native
Manager, project-file import, generated documents and hermetic tests do not require these tools.
The engine's fixture adapter preserves its independently pinned fixture identity and hashes;
source synchronization and hash verification are outside parse/decode/performance timing.

## Maintenance

Publish a new index version when an external source changes, retain the matching actual bytes,
and review the engine lock change. Never overwrite a bound version to represent new content.
Additional libraries and assets remain normal catalog/index additions; no engine-specific logic
was added to the Anyasset manager. Run the full Anyasset suite and `catalog-check` after changes,
then run the engine's actual image/model/preset/robot consumer gates before claiming compatibility.
