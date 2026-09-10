# Textures

Version-controlled source textures for development, terrain-material prototyping, and Sandbox
validation.

Path policy:

- Runtime loads use `configuration::ProjectPaths::Resolve(ProjectDirectory::Assets, relativePath)`.
- Sandbox default texture: `Textures/SandboxCheckerboard.png`.
- The eight reviewed outdoor PBR kits are indexed by
  `OutdoorTerrain/terrain-material-library.v1.json`. Base color is sRGB; normal, roughness, and
  height are linear data. The manifest is the stable application/engine migration boundary and
  records authored physical coverage and provenance.
- Renderer-owned GGX LTC lookup payloads: `Textures/LtcGgx/`; provenance, license, encoding and
  deterministic import instructions are local to that folder.
- `Skybox/default_skybox_2.hdr` is the checked-in CC0 outdoor sky used by DirectDriveStudio for
  its visible background and environment lighting; `Skybox/README.md` records provenance and the
  pinned digest.

These 1K source kits are intentionally versioned test assets. Larger source scans, generated
variants, and runtime captures do not belong here.
