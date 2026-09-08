# GGX LTC Lookup Tables

This folder contains the pinned lookup payload used by Anygine's rectangular area-light LTC
contract. It is a runtime renderer resource, not a test-generated baseline.

Source identity and storage semantics are frozen in `manifest.json`. The payloads are raw 64x64
RGBA16F little-endian texels with no container header, mip chain or array layers. Runtime upload
must use linear clamp-to-edge sampling and the manifest content fingerprint.

The tables originate from the authors' `selfshadow/ltc_code` reference implementation. Preserve
`LICENSE.selfshadow-ltc-code.txt` and the paper citation recorded by the manifest when
redistributing source or binaries.

Reproduce from an exact upstream checkout:

```bash
python3 Scripts/ImportLtcGgx.py import \
  --source-root /path/to/ltc_code-at-31e5e96b \
  --output-dir Assets/Textures/LtcGgx
```

Download the pinned files and reproduce them directly:

```bash
python3 Scripts/ImportLtcGgx.py download --output-dir Assets/Textures/LtcGgx
```

The maintained offline check is:

```bash
python3 Scripts/ImportLtcGgx.py verify --output-dir Assets/Textures/LtcGgx
```
