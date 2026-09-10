# Go2 Mjlab Phase 2C mild-blind terrain candidate (v10 U2660)

This versioned Package is the Phase 2C visual candidate selected from the
targeted-reward continuation checkpoint `model_2660.pt`. It retains Anygine's
58-value lifecycle observation ABI and uses the upstream leg order, default
pose, 0.25 action scale, and 5 ms physics step.

It is intentionally a new action ABI. Do not copy Mjlab ONNX weights into the
legacy Go2 Package: that would misinterpret joint deltas and previous actions.

The importer projects the actor input as
`[observation[0:9], observation[48:50], observation[9:45]]`, with the phase pair
set to zero while the command norm is below 0.1. Lifecycle fields remain outside
the external actor and can be trained as later residual branches.

The actor was continued from the frozen flat family on a fully blind mixture of
flat ground, mild positive and negative slopes, and light uneven heightfields.
Training uses a sagittal mirror loss and explicit low-speed/standing-action
objectives. The Package model owns Mjlab-compatible foot contact `solimp`, so
the same contact contract reaches native MuJoCo, C++ acceptance, and Studio.

The Package retains the host-owned absolute-heading loop during planar motion
with zero operator yaw.
The loop captures the current heading when translation starts and feeds a bounded
proportional correction through the existing yaw-rate command. Explicit operator
yaw input disables the loop immediately; releasing yaw recaptures the new heading.

Lifecycle ownership also remains in the Package. A bounded 0.8 stand/brake
action scale is applied only at zero command; it does not alter moving policy
actions. No observation or action ABI changed. The controller block is consumed
by PolicyTrain acceptance, native PolicyAccept, and Simulation Studio.

This candidate has passed native terrain cohorts, 19/19 product scenarios,
80/80 robustness trials, eight C++ parity scenarios, a 30-second bilateral
trace, link self-check, and build/tests. It is awaiting human visual validation
and is not yet a frozen Phase 2C release.
