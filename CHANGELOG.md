# Changelog

## 0.2.0

- Add external local-directory libraries with metadata-only version indexes,
  machine-local bindings, namespaced asset IDs, and verified snapshot import.
- Add schema-2 requirements/locks/bindings while retaining schema-1 compatibility.
- Make new managed-repository initialization atomic and repair missing remote/LFS
  configuration in valid existing managed bare repositories.
- Check dependency cycles throughout the catalog, including unselected assets.
- Bound Git process duration, terminate subprocess trees on timeout, and report
  fetch/clone progress on stderr. Configure Git and lock timeouts through environment.
- Batch selected missing LFS paths to reduce repeated fetch startup overhead.
- Add plan and doctor diagnostics without automatic destructive repair or GC.
- Extend regression tests and English integration/maintenance documentation.

## 0.1.0

- Initial standard Git/LFS asset manager, exact locks, shared object cache,
  versioned views, offline restore, Python/CLI/CMake interfaces, and CI.
