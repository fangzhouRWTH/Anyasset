# Assets

This directory stores **project asset roots** used by the engine.

**Full asset storage policy** (in-repo vs fetched data vs local library, path registry, layout, scripts):  
**[Doc/Policies/AssetStoragePolicy.md](../Doc/Policies/AssetStoragePolicy.md)**

## Quick reference

| Location | In git | Role |
| --- | --- | --- |
| `Assets/Interchange/`, `Assets/Textures/` | Yes | CI fixtures: `Interchange/TestTriangle.*`, `Textures/SandboxCheckerboard.png` |
| `Assets/Data/Catalog/` + `Assets/Data/README.md` | Yes | Preset index for optional fetched packs |
| `Assets/Data/Robots/`, `Policies/`, `_state/` | **No** | Downloaded Menagerie / policy payloads — `./Scripts/FetchExternalData.sh` |
| Local asset library | No | Large benchmarks (Sponza), debug sets — root in `Config/LocalPaths.local` |

Large datasets, generated assets, model weights, captures, and runtime outputs stay outside version control or in ignored directories (see `.gitignore`).

## Subdirectories

- `Interchange/` — tiny glTF/USDA fixtures; see [Interchange/README.md](Interchange/README.md)
- `Textures/` — small validation PNGs
- `Data/` — fetched project data packs + tracked catalog; see [Data/README.md](Data/README.md)

Setup local library: `cp Config/LocalPaths.example Config/LocalPaths.local` then `./Scripts/SetupLocalAssetLibrary.sh`

Fetch optional robot/policy data:

```bash
./Scripts/FetchExternalData.sh list
./Scripts/FetchExternalData.sh fetch --pack menagerie
./Scripts/FetchExternalData.sh status
```
