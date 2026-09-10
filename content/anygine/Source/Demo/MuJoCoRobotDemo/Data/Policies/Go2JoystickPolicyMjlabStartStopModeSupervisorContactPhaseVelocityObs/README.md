# Go2 Mjlab joystick lifecycle template

This template is the explicit import boundary for Unitree RL Mjlab Go2 velocity
policies. It retains Anygine's 58-value lifecycle observation ABI but adopts the
upstream leg order, default pose, 0.25 action scale, and 5 ms physics step.

It is intentionally a new action ABI. Do not copy Mjlab ONNX weights into the
legacy Go2 Package: that would misinterpret joint deltas and previous actions.

The importer projects the actor input as
`[observation[0:9], observation[48:50], observation[9:45]]`, with the phase pair
set to zero while the command norm is below 0.1. Lifecycle fields remain outside
the external actor and can be trained as later residual branches.
