# Go2 Mjlab height-scan observation template

This experimental Phase 3 template is the explicit import boundary for Unitree RL Mjlab Go2
velocity policies. ABI v8 preserves Anygine's 58-value lifecycle ABI and appends a compact
15-point local terrain-height scan. It retains the upstream leg order, default pose, 0.25 action
scale, and 5 ms physics step.

Sampling uses the base heading frame rather than full body attitude, subtracts the terrain height
at base XY, clips to `[-0.20, 0.20] m`, and scales by `5.0`. The grid spans
`x=-0.30..0.80 m` and `y=-0.24..0.24 m`.

It is intentionally a new action ABI. Do not copy Mjlab ONNX weights into the
legacy Go2 Package: that would misinterpret joint deltas, previous actions, and observation size.

The importer projects the actor input as
`[observation[0:9], observation[48:50], observation[9:45]]`, with the phase pair
set to zero while the command norm is below 0.1. The probe importer also permits an old actor to
ignore the appended suffix so the host contract can be verified before terrain-aware training.
