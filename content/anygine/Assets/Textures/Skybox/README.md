# Default sky environment

`default_skybox_2.hdr` is the 1K Radiance HDR distribution of **Kloofendal 48d Partly Cloudy**
by Greg Zaal, downloaded from Poly Haven:

- Asset page: <https://polyhaven.com/a/kloofendal_48d_partly_cloudy>
- Source file: <https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/kloofendal_48d_partly_cloudy_1k.hdr>
- License: CC0 1.0 / public domain
- MD5: `ee096fe9e26ce29d8f110b5ba0579011`
- Source dimensions: 1024 x 512, equirectangular RGBE

DirectDriveStudio selects this file explicitly from its startup configuration. The engine
`EnvironmentMap` owns upload, skybox rendering, and split-sum IBL baking. The current `ImageFile`
contract tone-maps HDR input to RGBA8 sRGB before upload; retaining a floating-point environment
through the full renderer remains a separate engine upgrade.
