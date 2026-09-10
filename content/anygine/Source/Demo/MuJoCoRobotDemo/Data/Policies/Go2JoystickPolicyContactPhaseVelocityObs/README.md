# Go2JoystickPolicyContactPhaseVelocityObs

Experimental append-only observation ABI v4. It preserves the 50-D phase and
velocity contract and appends `foot_contacts=[FL,FR,RL,RR]` at `[50:54]`.

- Contact body names and order come from `controller.foot_contact_bodies`.
- A value is 1 when any geom on that body is in MuJoCo's current contact list.
- Package container version remains 1; observation spec version is 4.
- Action, command, stand-hold, velocity and phase semantics are unchanged.
- Older checkpoints migrate by zero-extending every observation-input layer.
- This template is not a production/Assets pin.
