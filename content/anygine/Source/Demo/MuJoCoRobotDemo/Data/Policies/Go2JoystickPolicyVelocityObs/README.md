# Go2JoystickPolicyVelocityObs

Experimental sibling template for stop-observability work. It preserves all 45 existing
observation offsets and appends body-frame `base_lin_vel` at `[45:48]`.

- Package container version remains 1.
- `observation.json` is ABI version 2.
- Action, controller and command semantics match the protected HF/u6 contract.
- A 45D checkpoint may be migrated by zero-extending the first linear layer; that migration must
  reproduce the old policy exactly before the new inputs are trained.
- This template has no runnable policy and must never replace the protected Assets pin directly.
