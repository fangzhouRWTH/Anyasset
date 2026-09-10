# Go2 Mjlab U2400 joystick policy with heading hold

This template is the explicit import boundary for Unitree RL Mjlab Go2 velocity
policies. It retains Anygine's 58-value lifecycle observation ABI but adopts the
upstream leg order, default pose, 0.25 action scale, and 5 ms physics step.

It is intentionally a new action ABI. Do not copy Mjlab ONNX weights into the
legacy Go2 Package: that would misinterpret joint deltas and previous actions.

The importer projects the actor input as
`[observation[0:9], observation[48:50], observation[9:45]]`, with the phase pair
set to zero while the command norm is below 0.1. Lifecycle fields remain outside
the external actor and can be trained as later residual branches.

This candidate keeps the visually accepted U2400 actor unchanged and enables a
host-owned absolute-heading loop during planar motion with zero operator yaw.
The loop captures the current heading when translation starts and feeds a bounded
proportional correction through the existing yaw-rate command. Explicit operator
yaw input disables the loop immediately; releasing yaw recaptures the new heading.

No observation or action ABI changed. The Package controller block is consumed by
PolicyTrain acceptance, native PolicyAccept, and Simulation Studio.
