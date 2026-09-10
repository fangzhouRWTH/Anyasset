# Go2 stop-mode/supervisor/contact/phase/velocity observation template

Experimental append-only observation ABI v6 for the Gymnasium + native MuJoCo
training path. It preserves ABI v5 `[0:55]` and appends host-owned
`stop_mode=[brake_active, stand_active]` at `[55:57]`.

The lifecycle is owned by the host controller, not hidden in ONNX. The Package's
`controller.json` defines identical MOVE/BRAKE/STAND hysteresis and dwell
semantics for Python training, headless acceptance, and Simulation Studio.

This is a template contract, not a promoted runnable policy. Do not copy it over
the protected `Assets/Data/Policies/Go2JoystickPolicy` production pin.
