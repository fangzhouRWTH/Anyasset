"""Example use at build/setup time; no absolute paths in tracked code."""
import argparse
from anyasset import resolve_asset

parser = argparse.ArgumentParser()
parser.add_argument("project")
parser.add_argument("asset_id")
args = parser.parse_args()
print(resolve_asset(args.project, args.asset_id))
