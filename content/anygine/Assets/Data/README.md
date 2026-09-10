# Assets/Data — Fetched Project Data Packs

This tree holds **optional, network-fetched** third-party data packs used by demos and tools (robot MJCF, policy packages, etc.).

It is **not** the same as:

| Location | Role |
| --- | --- |
| `Assets/Interchange/`, `Assets/Textures/` | Small **in-repo** CI fixtures (always cloned) |
| Local asset library (`LocalPaths.local`) | Large personal/benchmark assets **outside** the repo |
| `External/MuJoCo/` | MuJoCo **SDK** binaries (see `Scripts/FetchMuJoCo.sh`) |

## Layout

```text
Assets/Data/
├── README.md                 # this file (tracked)
├── Catalog/
│   └── PresetIndex.json      # logical preset → relative path (tracked)
├── Robots/
│   ├── Menagerie/           # fetched robot models (gitignored)
│   │   ├── unitree_go2/
│   │   ├── franka_emika_panda/
│   │   ├── aloha/
│   │   └── pal_tiago_dual/
│   ├── DirectDrive/         # fetched/prepared TITA and TITATIT URDF/STL (gitignored)
│   │   ├── Tita/
│   │   └── Titatit/
│   └── Custom/              # small Anygine-authored assembly frames (tracked)
│       └── dual_panda/       # tracked central frame; attaches two fetched Panda subtrees
├── Policies/                 # fetched policy packages (gitignored)
└── _state/                   # fetch pins / manifests (gitignored)
```

## Gitignore (important)

Tracked:

- `Assets/Data/README.md`
- `Assets/Data/Catalog/**` (preset index)
- `Assets/Data/Robots/Custom/**` (small Anygine-authored assembly frames)

Ignored (downloaded payloads — never commit):

- `Assets/Data/Robots/Menagerie/`
- `Assets/Data/Policies/`
- `Assets/Data/_state/`

See repository root `.gitignore` section **Assets/Data fetched payloads**.

## Fetch

```bash
./Scripts/FetchExternalData.sh list
./Scripts/FetchExternalData.sh fetch --pack menagerie
./Scripts/FetchExternalData.sh fetch --pack menagerie --select aloha
./Scripts/FetchExternalData.sh fetch --pack menagerie --select pal_tiago_dual
./Scripts/FetchExternalData.sh fetch --pack menagerie --select unitree_go2,franka_emika_panda,aloha,pal_tiago_dual
./Scripts/FetchExternalData.sh fetch --pack policies
./Scripts/FetchExternalData.sh fetch --pack policies --select go2_velocity_flat
./Scripts/FetchExternalData.sh fetch --pack direct_drive
./Scripts/FetchExternalData.sh fetch --pack direct_drive --select tita
./Scripts/FetchExternalData.sh fetch --pack direct_drive --select titatit
./Scripts/FetchExternalData.sh status
```

Override Menagerie git ref:

```bash
ANYGINE_MENAGERIE_REF=<commit-or-tag> ./Scripts/FetchExternalData.sh fetch --pack menagerie
```

Direct Drive sources are fixed to catalog commits by default. A single source can be overridden
for review with `ANYGINE_DIRECT_DRIVE_TITA_REF` or `ANYGINE_DIRECT_DRIVE_TITATIT_REF`. Each fetched
robot and policy directory retains the MIT `LICENSE` plus a `SOURCE.json` containing the resolved
commit and artifact hashes. Runtime payloads are not committed.

## Engine resolution

C++ apps resolve logical presets through `anygine::assets::DataPresetCatalog` (loads `Catalog/PresetIndex.json` via `ProjectPaths`).

Example id: `robot.menagerie.unitree_go2.scene` → `Assets/Data/Robots/Menagerie/unitree_go2/scene.xml`

Bimanual example: `robot.menagerie.pal_tiago_dual.position_scene` →
`Assets/Data/Robots/Menagerie/pal_tiago_dual/scene_position.xml`

Modular bimanual default: two namespaced copies of
`robot.menagerie.franka_emika_panda.model`. The authoritative central-frame topology is the
application-owned `Source/Apps/BimanualDemo/Config/dual_panda.bimanual.json`; it generates the
runtime MJCF, while `Robots/Custom/dual_panda/frame.xml` is retained as a reference snapshot. No
additional external asset pack is required.

Policy: `Doc/Policies/AssetStoragePolicy.md` §2.1. Demo path: `Doc/Modules/SceneSimulation/MuJoCoRobotDemoPath.md`.

Direct Drive customer-demo path:
`Doc/Modules/SceneSimulation/DirectDriveRobotDemo.md`.
