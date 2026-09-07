# Anyasset contributor instructions

Read README.md, INTERFACES.md and ARCHITECTURE.md before changing the manager.
Read ANYGINE_INTEGRATION.md before editing engine integration examples.

- Preserve exact commit locks. `sync` must never resolve a moving branch or modify assets.lock.json.
- Never checkout, reset, clean, or prune a user's author repository during consumption.
- Never modify published views in place. Keep generated outputs outside source views.
- Do not introduce hard links from writable workspaces to cache objects.
- Retain atomic publication, hash verification, portable paths, dependency closure and process locking.
- Keep JSON stdout stable and errors on stderr. Do not log credentials.
- Runtime dependencies remain Python standard library + Git/LFS unless a concrete need justifies a change.
- Do not import existing Anygine assets without recording provenance/license and a complete dependency list.
- Do not claim engine-format compatibility based only on this repository's data-management tests.
- Run `python -m unittest discover -s tests -v` and `python -m anyasset catalog-check` for behavioral changes.
- Update schemas, interface docs and tests together for public contract changes.
- No automatic destructive GC in schema/tool v1 initial implementation. Add retention/lease design before implementing deletion.
- Engine-side modifications are a separate repository; do not stage its contents into Anyasset or add Anyasset as a submodule.
