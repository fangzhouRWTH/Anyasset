"""Source checkout launcher; installed assetctl is preferred for consumers."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anyasset.cli import main

raise SystemExit(main())
