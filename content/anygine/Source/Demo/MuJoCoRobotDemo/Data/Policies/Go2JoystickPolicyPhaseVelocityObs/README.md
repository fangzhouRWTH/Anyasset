# Go2JoystickPolicyPhaseVelocityObs

Experimental append-only observation ABI v3. It preserves the 48-D velocity
contract and appends `gait_phase=[sin(2πft), cos(2πft)]` at `[48:50]`, where
`f=controller.gait_phase_hz`.

- Package container version remains 1; observation spec version is 3.
- Reset phase is `[0, 1]` because MuJoCo time resets to zero.
- Action, command and stand-hold semantics are unchanged.
- Older checkpoints migrate by zero-extending every observation-input layer.
- This template is not a production/Assets pin.
