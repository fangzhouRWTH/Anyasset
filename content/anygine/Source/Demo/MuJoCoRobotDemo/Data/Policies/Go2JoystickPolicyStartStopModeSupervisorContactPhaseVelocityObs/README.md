# Go2 start/stop lifecycle observation template

Experimental append-only observation ABI v7 for the Gymnasium + native MuJoCo
training path. It preserves ABI v6 `[0:57]` and appends host-owned
`start_mode` at `[57:58]`.

The Package controller owns `STAND → START → MOVE → BRAKE → STAND`, resets the
gait phase on each START, and uses command-relative forward recovery thresholds.
The lifecycle is mirrored by PolicyTrain, headless acceptance and Simulation
Studio. This directory is a template, not a runnable production policy.
