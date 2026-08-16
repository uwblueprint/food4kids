"""Generate placeholder note attachment images for the seed script.

Seeded notes need real bytes in the bucket, not fabricated URLs: reads re-sign
from the stored ``filename``, and signing is an offline operation, so a made-up
key yields a perfectly valid URL that 404s the moment a thumbnail renders. The
images therefore have to exist.

They are drawn here rather than committed as fixtures so the repo carries no
binaries and no photo licensing question, and rather than fetched at seed time
so seeding needs no network beyond the bucket itself. Each is a flat-coloured
tile with a simple silhouette, which is enough to tell three thumbnails apart
in a note card and to show one is not square.
"""

import struct
import zlib

# Distinct hues so a note's three thumbnails are visibly different from each
# other, and from any real photo, at the 64px the note card renders them at.
SEED_IMAGE_PALETTE: list[tuple[str, tuple[int, int, int], tuple[int, int, int]]] = [
    ("front-door", (214, 222, 233), (61, 90, 128)),
    ("porch", (233, 226, 214), (147, 108, 71)),
    ("package", (222, 233, 216), (78, 122, 63)),
    ("gate", (233, 214, 222), (140, 61, 90)),
    ("driveway", (219, 219, 224), (86, 86, 110)),
    ("side-entrance", (233, 231, 210), (150, 140, 55)),
]

# Deliberately not square: the design lays thumbnails out in a fixed 64px box,
# so a non-square source is what proves the object-fit crop is right.
SEED_IMAGE_WIDTH = 160
SEED_IMAGE_HEIGHT = 120


def _png_chunk(tag: bytes, payload: bytes) -> bytes:
    """Serialize one PNG chunk: length, tag, payload, CRC over tag+payload."""
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def encode_png(rows: list[list[tuple[int, int, int]]]) -> bytes:
    """Encode RGB pixel rows as an 8-bit truecolour PNG.

    Each scanline is prefixed with filter type 0 (None), which is what the
    format requires even when no filtering is applied.
    """
    if not rows or not rows[0]:
        raise ValueError("Cannot encode a PNG with no pixels.")

    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("Every PNG row must have the same width.")

    raw = bytearray()
    for row in rows:
        raw.append(0)
        for red, green, blue in row:
            raw.extend((red, green, blue))

    header = struct.pack(">IIBBBBB", width, len(rows), 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _png_chunk(b"IEND", b"")
    )


def render_seed_image(index: int) -> tuple[str, bytes]:
    """Build the ``index``-th placeholder image, wrapping around the palette.

    Deterministic: the same index always yields identical bytes, so re-seeding
    overwrites each object with the same content instead of accumulating new
    ones.
    """
    if index < 0:
        raise ValueError(f"Seed image index must be non-negative, got {index}.")

    name, background, foreground = SEED_IMAGE_PALETTE[index % len(SEED_IMAGE_PALETTE)]

    # A centred rounded-ish block reads as a door/parcel silhouette at
    # thumbnail size, and off-centre proves the crop is not mirroring.
    left = SEED_IMAGE_WIDTH // 3
    right = SEED_IMAGE_WIDTH - SEED_IMAGE_WIDTH // 4
    top = SEED_IMAGE_HEIGHT // 4
    bottom = SEED_IMAGE_HEIGHT - SEED_IMAGE_HEIGHT // 8

    rows: list[list[tuple[int, int, int]]] = []
    for y in range(SEED_IMAGE_HEIGHT):
        row: list[tuple[int, int, int]] = []
        for x in range(SEED_IMAGE_WIDTH):
            inside = left <= x < right and top <= y < bottom
            row.append(foreground if inside else background)
        rows.append(row)

    return f"{name}.png", encode_png(rows)
