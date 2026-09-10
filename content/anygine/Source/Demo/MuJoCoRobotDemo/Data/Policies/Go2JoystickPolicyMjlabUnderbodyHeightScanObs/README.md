# Go2 Mjlab underbody height-scan observation template

This experimental Phase 3 template is the explicit import boundary for Unitree RL Mjlab Go2
velocity policies. ABI v10 preserves all 78 ABI v9 values and appends two rear-centerline terrain
samples. The complete 22-value scan remains append-only.

The appended X positions are `-0.20` and `-0.10 m`, both at `y=0`. Together with v9, the scan has
no centerline gap wider than a `0.14 m` bar from `x=-0.30` through `x=0.925 m`. The obstacle
therefore remains observable while the rear legs pass it, not only during the front-leg approach.

Sampling uses the base heading frame, subtracts terrain height at base XY, clips to
`[-0.20, 0.20] m`, and scales by `5.0`. The importer projects a 72-value Mjlab actor input as
`[0:9,48:50,9:48]+[58:80]` and zeros the phase pair for standing commands.

This is a new observation ABI but retains the Mjlab joint-delta action ABI. It is a template only;
no locomotion capability is claimed until a trained actor passes automated and visual gates.
