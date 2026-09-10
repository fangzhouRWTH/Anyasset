# Anygine local development asset library

`layout_version`: **1** (see `_manifest/layout-version`)

This directory is **not** in the Anygine git repository. Register this root in the clone:

```text
Config/LocalPaths.local  →  local_asset_library=/home/fangzhou/Assets
```

Full policy: `Anygine/Doc/Architecture/AssetStoragePolicy.md` in the engine repository.

## Layout

```text
Assets/
├── _manifest/layout-version
├── Models/
│   ├── Sponza/          # New Sponza glTF + USD + textures/
│   └── ABeautifulGame/  # GLB / glTF smoke assets
├── Interchange/
│   ├── Primitives/
│   └── Materials/NormalMapSwatch/
├── Textures/
│   ├── PBR/
│   └── Reference/
└── Scenes/Debug/
```

## Validation

From the Anygine repo:

```bash
./Scripts/VerifyLocalPaths.sh
./Scripts/Run/asset-viewer-sponza.sh
./Scripts/Run/asset-viewer-sponza-usd.sh
```

## Current contents (this machine)

| Path | Status |
| --- | --- |
| `Models/Sponza/NewSponza_Main_glTF_003.gltf` | OK (+ `.bin`, USDA variants, `textures/`) |
| `Models/ABeautifulGame/ABeautifulGame.glb` | OK (glTF sidecar layout optional) |

## Populate / migrate

Re-run scaffold after policy updates:

```bash
./Scripts/SetupLocalAssetLibrary.sh --root /home/fangzhou/Assets
```
