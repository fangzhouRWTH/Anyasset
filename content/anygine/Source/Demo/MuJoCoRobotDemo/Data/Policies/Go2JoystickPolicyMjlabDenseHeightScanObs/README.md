# Go2 Mjlab dense height-scan observation template

This experimental Phase 3 template is the explicit import boundary for Unitree RL Mjlab Go2
velocity policies. ABI v9 preserves all 73 ABI v8 values and appends five forward-centerline
terrain samples. The complete 20-value scan therefore remains append-only.

The appended X positions are `0.10`, `0.20`, `0.425`, `0.675`, and `0.925 m`, all at `y=0`.
Together with ABI v8's centerline rows, the maximum forward spacing is `0.125 m` beyond the
near-base region and `0.10 m` inside it. A centered `0.14 m`-deep bar can no longer disappear
between consecutive samples while it approaches the robot.

Sampling uses the base heading frame, subtracts terrain height at base XY, clips to
`[-0.20, 0.20] m`, and scales by `5.0`. The importer projects a 70-value Mjlab actor input as
`[0:9,48:50,9:48]+[58:78]` and zeros the phase pair for standing commands.

This is a new observation ABI but retains the Mjlab joint-delta action ABI. It is a template only;
no locomotion capability is claimed until a trained actor passes automated and visual gates.
