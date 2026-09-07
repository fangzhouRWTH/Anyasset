"""Anyasset v1 public API. No third-party runtime dependencies."""
from .core import AssetError, AssetManager, resolve_asset

__version__ = "0.2.0"
__all__ = ["AssetError", "AssetManager", "resolve_asset"]
