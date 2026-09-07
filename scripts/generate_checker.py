"""Regenerate the original 2x2 magenta/black PNG fixture using only stdlib."""
from pathlib import Path
import struct
import zlib


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


pixels = bytes([0, 255, 0, 255, 0, 0, 0, 0, 0, 0, 0, 255, 0, 255])
png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(pixels))
png += chunk(b"IEND", b"")
target = Path(__file__).resolve().parents[1] / "content/defaults/checker.png"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_bytes(png)
print(target)
