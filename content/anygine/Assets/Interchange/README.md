# Interchange test assets

**Asset storage policy:** [Doc/Policies/AssetStoragePolicy.md](../../Doc/Policies/AssetStoragePolicy.md)

## In-repo fixtures

- `TestTriangle.gltf` — minimal triangle used by unit tests and quick import smoke.
- `TestTriangle.usda` — minimal USDA fixture for subset importer tests.
- `TestPreviewSurface.usda` — quad with UVs + UsdPreviewSurface normal map (OpenUSD path; MikkTSpace tangents).
- `Interchange/TransparentSwatch/` — SP-RAM-8 validation quad with opaque background + BLEND glass pane (in-repo).

### Transparent swatch (SP-RAM-8)

```bash
./Scripts/Run/asset-viewer-transparent-swatch.sh
ctest --preset linux-debug -R "transparent swatch"
```

## External reference: Sponza

Full-scene glTF/USD validation uses the **New Sponza** dataset (not vendored in git due to size).

Store under your **local asset library** at:

```text
Models/Sponza/NewSponza_Main_glTF_003.gltf
Models/Sponza/NewSponza_Main_USD_Yup_003.usda
Models/Sponza/NewSponza_Main_USD_Zup_003.usda   # optional
```

Register the library root in `Config/LocalPaths.local` — see [Asset Storage Policy §3–§5](../../Doc/Policies/AssetStoragePolicy.md).

### AssetViewer (glTF)

```bash
./Scripts/Run/asset-viewer-sponza.sh
# or explicit override:
SPONZA_GLTF=/path/to/NewSponza_Main_glTF_003.gltf ./Scripts/Run/asset-viewer-sponza.sh
```

### AssetViewer (USD)

```bash
./Scripts/Run/asset-viewer-sponza-usd.sh
# or
SPONZA_USD=/path/to/NewSponza_Main_USD_Yup_003.usda ./Scripts/Run/asset-viewer-sponza-usd.sh
```

Full-scene USDA currently uses the **ASCII subset importer** until OpenUSD (AP-0b) links.

### Unit tests

```bash
ctest --preset linux-debug -R Sponza
ANYGINE_SPONZA_GLTF=/path/to/NewSponza_Main_glTF_003.gltf ctest --preset linux-debug -R Sponza
ANYGINE_SPONZA_USD=/path/to/NewSponza_Main_USD_Yup_003.usda ctest --preset linux-debug -R Sponza
ANYGINE_USD_USDC=/path/to/scene.usdc ctest --preset linux-debug -R "USDC when"
```

Textures must live beside the interchange file under `textures/` (upstream package layout).

## External reference: A Beautiful Game (GLB)

Local library path: `Models/ABeautifulGame/ABeautifulGame.glb` (single-file GLB with embedded buffers/textures).

```bash
./Scripts/AI/abeautifulgame-glb-smoke.sh
# import only (skip AssetViewer):
ANYGINE_SKIP_VIEWER_SMOKE=1 ./Scripts/AI/abeautifulgame-glb-smoke.sh
# or explicit path:
ABEAUTIFULGAME_GLB=/path/to/ABeautifulGame.glb ./Scripts/AI/abeautifulgame-glb-smoke.sh
```

Interactive viewer (separate `.gltf` + sidecar files): `./Scripts/Run/asset-viewer-abeautifulgame.sh`

## External reference: Chronograph Watch (GLB)

Khronos glTF Sample Asset — PBR showcase with embedded textures (CC BY 4.0).

Local library path: `Models/ChronographWatch/ChronographWatch.glb`

Download:

https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/ChronographWatch/glTF-Binary/ChronographWatch.glb

```bash
./Scripts/AI/chronograph-watch-glb-smoke.sh
# import only (skip AssetViewer):
ANYGINE_SKIP_VIEWER_SMOKE=1 ./Scripts/AI/chronograph-watch-glb-smoke.sh
# or explicit path:
CHRONOGRAPH_WATCH_GLB=/path/to/ChronographWatch.glb ./Scripts/AI/chronograph-watch-glb-smoke.sh
```

Interactive viewer: `./Scripts/Run/asset-viewer-chronograph-watch.sh`
