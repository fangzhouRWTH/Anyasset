# Anyasset contributor instructions

Read README.md, INTERFACES.md and ARCHITECTURE.md before changing the manager.
Read ANYGINE_INTEGRATION.md before editing engine integration examples.
Read ASSET_AUTHORING.md before adding or reorganizing catalog assets.
Read EXTERNAL_LIBRARIES.md before changing external providers or schema-2 contracts.

## Language policy

- Write all project text records in English: documentation, comments, docstrings, metadata prose, diagnostics, commit messages, and release notes.
- Communicate with the user in Chinese while collaborating with AI on development.
- Preserve required third-party attribution and original proper names verbatim when necessary.
- Apply this policy to new and edited content. Do not rewrite published Git history or move release tags to translate historical records.

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
- External indexes contain metadata only. Never copy external payloads, machine-local roots, or credentials into this repository as part of registration.
- Preserve schema-1 lock compatibility. External libraries use schema 2 and explicit namespaced IDs; do not implement silent live-directory overrides.
