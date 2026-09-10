# Go2 supervisor/contact/phase/velocity observation template

Experimental append-only observation ABI v5 for the Gymnasium + native MuJoCo
training path. It preserves ABI v4 `[0:54]` and appends one explicit
`recovery_mode` value at `[54:55]`.

The mode is owned by the host controller, not hidden in ONNX. The Package's
`controller.json` defines identical enter/exit hysteresis and minimum-hold
semantics for Python training, headless acceptance, and Simulation Studio.

This is a template contract, not a promoted runnable policy. Do not copy it over
the protected `Assets/Data/Policies/Go2JoystickPolicy` production pin.
