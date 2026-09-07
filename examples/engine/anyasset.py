"""Copy to Anygine Scripts/AI/anyasset.py; requires installed anyasset package.

Example: python Scripts/AI/anyasset.py sync --locked
"""
from pathlib import Path
import sys

# Prevent this file (anyasset.py) from shadowing the installed anyasset package.
sys.path = [p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]
try:
    from anyasset.cli import main
except ImportError:
    raise SystemExit("Install a pinned Anyasset tool release in this Python environment first.")

args = sys.argv[1:]
if args and args[0] not in ("catalog-check", "--version", "--help", "-h") and "--project" not in args:
    args += ["--project", str(Path(__file__).resolve().parents[2])]
raise SystemExit(main(args))
