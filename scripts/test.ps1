$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Anyasset tests failed' }
    python -m anyasset catalog-check
    if ($LASTEXITCODE -ne 0) { throw 'Catalog validation failed' }
} finally { Pop-Location }
