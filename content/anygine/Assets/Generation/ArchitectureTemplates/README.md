# Frozen architectural input catalog

Eleven checked-in templates: seven local Site inputs and four complete road-block archives.
The local Site inputs provide a short loop for downstream architecture iteration. The application
loads these files; it never runs the authoring recipe. They carry the existing public
`BuildingGenerationContextView` and `SiteCirculationPlan` in full, including committed topology,
access terminals, constraint authority, diagnostics and provenance. They contain no building mesh.

| Template ID | Authored domain | Current debugging purpose |
| --- | --- | --- |
| `single_rectangle` | 40 x 30 m Site; one 28 x 18 m BuildSupport Cell | Small geometry/method fixture; minimum box/component loop |
| `courtyard` | 80 x 70 m Site; one 60 x 50 m Cell and forbidden landscape reserve | Existing B1a perimeter preview |
| `rotated_courtyard` | Courtyard input rotated 30 degrees, including access and constraints | Same B1a method in a rotated frame |
| `two_cells` | 80 x 60 m Site; two 22 x 30 m Cells and one circulation hub | Shared access; only committed connectors may traverse the access reserve |
| `skew_quadrilateral` | 80 x 70 m Site; a convex, slanted quadrilateral Cell | Existing B1a geometry capability beyond axis-aligned rectangles |
| `concave_region` | 80 x 70 m Site; L-shaped BuildSupport Cell | Valid concave input; method support remains to be added |
| `intentional_empty` | 40 x 40 m Site; 34 x 34 m OpenSpace Cell | Explicit non-building result, no invented access or fallback mass |

All domains use meters, +Z up, planar XY and a 3 m Site-to-buildable-envelope inset. Family labels
are input intent, not evidence that a building method is connected. In particular, `two_cells`
does not provide the legacy layout/massing inputs required by the existing parallel-bars adapter.
The concave test concerns a Cell within a rectangular Site; it is not a concave parcel example.

## Road-block archives

The `*.agblock.json` files freeze a real offline chain from a closed RoadGraph and canonical ROW
through Block, Parcel, Site/assembly, analysis, intent, Scaffold selection and Context/Circulation.
They preserve native stage identities and complete intermediate records, including candidate and
rejection evidence. Runtime loads these products and selects a Site for architectural consumption.

| ID | Parcels | Sites | Cells | Purpose |
| --- | ---: | ---: | ---: | --- |
| `block_courtyard` | 1 | 1 | 3 | Mixed-use courtyard / existing B1a entry |
| `block_street` | 8 | 8 | 13 | Subdivision, access and explicit open-space Sites |
| `block_skew` | 5 | 5 | 9 | Slanted geometry and varied family intent; B1a on Site 3 |
| `block_assembled` | 7 | 4 | 7 | Rotated block; three-Parcel and two-Parcel Site assemblies |

```bash
./Scripts/Run/architecture-generation.sh --template block_street
./Scripts/Run/architecture-generation.sh --template block_assembled --site 2 --input-layer sites
./Scripts/Run/architecture-generation.sh --template block_skew --site 3 --building-preview
```

**Template**, **Active Site** and **Input layer** control read-only views. The input-layer choices
are `roads`, `parcels`, `sites`, `scaffold`, `circulation`; source/design state is unchanged by layer
selection. All four examples use four surrounding roads and one bounded Block. These are synthetic
road cycles, not imported city districts or detailed road-marking assets.

See [RoadBlockTemplateInputs.md](../../../Doc/GenerationGeometry/BuildingGeneration/RoadBlockTemplateInputs.md)
for stage contracts, dimensions, namespace scope, full data ownership and implementation limits.
Both catalogs are prepared/verified by the same offline command below.

## Offline authoring and reproducibility

```bash
cmake --build build/debug --target AnyginePrepareArchitectureTemplates -j 6
# Explicit authoring operation: updates the checked-in catalog; review the resulting diff.
build/debug/Source/Tools/ArchitectureTemplates/AnyginePrepareArchitectureTemplates \
  --output Assets/Generation/ArchitectureTemplates
# Read-only check: reproduce in memory and compare against the frozen files.
build/debug/Source/Tools/ArchitectureTemplates/AnyginePrepareArchitectureTemplates \
  --verify Assets/Generation/ArchitectureTemplates
```

The local recipe is `Source/Tools/ArchitectureTemplates/Source/Main.cpp`; the complete Block
recipe is `Source/Tools/ArchitectureTemplates/Source/BlockTemplates.cpp`. The local recipe
authors a local Site, analysis, intent and committed Scaffold consumption record; then calls the existing context
builder and Scaffold-guided circulation producer **offline**. It does not run a road/parcel
search or use GenerationStudio private code. No generation command is attached to app startup,
normal app builds or runtime file loading. `--verify` is a separate offline CTest gate.

Each local `*.aginput.json` file declares schema/version, producer, template version, seed and authored provenance.
Source Site/Parcel/Cell identities belong to `template:<id>:`; derived IDs retain those references.
Road class is explicitly unspecified: local approach geometry does not fabricate public-road
ownership. Geometry and resolved parameters are frozen without timestamps or machine paths.

## Admission and consumption

Local schema `anygine.building_generation_input`, payload version 1, supports one authored local Site
per file (up to 4 MiB), meter scale and +Z up. It is a bounded fixture format, not a complete city
interchange format. Read rejects unsupported versions, changed content fingerprints, broken
references, invalid polygons/containment, lost topology reachability, inconsistent access and
constraint projections, and invalid clearance evidence. It does not repair or regenerate inputs.
Version 2 of the same consumer payload retains native upstream Site IDs under the archive ID
with `upstream_snapshot` provenance. Road-block archives use their own version-1 wrapper (32 MiB
limit). The FNV-1a content fingerprint is a reproducible revision identifier, not a security signature.

```bash
./Scripts/Run/architecture-generation.sh --template courtyard
./Scripts/Run/architecture-generation.sh --template courtyard --building-preview
```

The first command only loads and displays input. The second explicitly invokes the existing
downstream B1a adapter and debug compiler. The app also offers template selection, **Generate
building preview**, and **Return to input**. Unsupported method coverage is shown explicitly.
Loading another input clears the previous design/mesh products. `--no-template` selects lighting
fixtures, and `--empty` starts the original empty viewport. App load operations leave files intact.

See [the staged-output design](../../../Doc/GenerationGeometry/BuildingGeneration/StagedArchitectureProducts.md)
for independent stage invocation and the future scheduling/residency boundary.

The app now loads `block_assembled` by default. Template/Site/layer changes retain the camera;
Home/Top/Front explicitly reframe. The configurable [default method pool](../../../Doc/GenerationGeometry/BuildingGeneration/DefaultGenerationPolicy.md)
adds downstream L1 generation without modifying these frozen files.
