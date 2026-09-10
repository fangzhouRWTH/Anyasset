# Go2JoystickPolicy

Tracked **Policy Package** for MuJoCo Go2 locomotion Demo (M5–M8).

Observation/action layouts match Menagerie `unitree_go2` (12 motors). Inference is still
**stub / demo pose-delta** until a real checkpoint lands under `policy/`.

## Layout

| Field | Value |
| --- | --- |
| observation_size | 45 |
| action_size | 12 |
| physics_dt / control_dt | 0.002 / 0.02 |
| action_mode | `joint_position_delta` → PD torque on motors |

## Validate template

```bash
cmake --build --preset linux-debug --target AnygineMuJoCoPolicyPackage
./build/debug/Source/Demo/MuJoCoRobotDemo/AnygineMuJoCoPolicyPackage \
  Source/Demo/MuJoCoRobotDemo/Data/Policies/Go2JoystickPolicy --template
```

Python worker IPC (still stub_zero actions; host may synthesize demo pose-delta):

```bash
./build/debug/Source/Demo/MuJoCoRobotDemo/AnygineMuJoCoPolicyPackage \
  Source/Demo/MuJoCoRobotDemo/Data/Policies/Go2JoystickPolicy --template \
  --python-worker Source/Demo/MuJoCoRobotDemo/Python/policy_worker.py
```

## Seed into Assets/Data

```bash
./Scripts/FetchExternalData.sh fetch --pack policies
# recommended open weights (Hugging Face, obs=45):
./Scripts/FetchExternalData.sh fetch --pack policies --select go2_velocity_flat
# refresh:
./Scripts/FetchExternalData.sh fetch --pack policies --select go2_velocity_flat --force
```

Catalog: `policy.go2.joystick.template` / `policy.go2.joystick.velocity_flat`.

Weight sources and caveats: [`MuJoCoRobotDemoAssets.md`](../../../../Doc/Modules/SceneSimulation/MuJoCoRobotDemoAssets.md).

## Runnable package (blocks true locomotion / M7 DoD)

1. Fetch weights (`--select go2_velocity_flat`) **or** drop your own export under `policy/` and patch `manifest.json` / `action.json`.
2. Ensure Menagerie Go2 is present so `model_hash` can be computed (`fetch --pack menagerie`).
3. Extend `policy_worker.py` with an ONNX/Torch backend behind the same NDJSON protocol.
4. Validate **without** `--template` against `Assets/Data/Policies/Go2JoystickPolicy`.

Until the worker loads weights: SimulationStudio Drive uses **demo pose-delta** (PD response, not a gait).
