"""Tests for the placeholder note images used by the seed script.

The point of these images is that they are *real* decodable bytes sitting in
the bucket — a note whose thumbnail 404s is exactly the state seeding is meant
to fix — so these tests decode what we generate rather than trusting the
encoder.
"""

import struct
import zlib

import pytest

from app.utilities.seed_images import (
    SEED_IMAGE_HEIGHT,
    SEED_IMAGE_PALETTE,
    SEED_IMAGE_WIDTH,
    encode_png,
    render_seed_image,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def iter_chunks(png: bytes) -> list[tuple[bytes, bytes]]:
    """Walk a PNG's chunk stream, verifying each chunk's declared CRC."""
    assert png.startswith(PNG_SIGNATURE)

    chunks: list[tuple[bytes, bytes]] = []
    offset = len(PNG_SIGNATURE)
    while offset < len(png):
        (length,) = struct.unpack(">I", png[offset : offset + 4])
        tag = png[offset + 4 : offset + 8]
        payload = png[offset + 8 : offset + 8 + length]
        (declared_crc,) = struct.unpack(
            ">I", png[offset + 8 + length : offset + 12 + length]
        )
        assert declared_crc == zlib.crc32(tag + payload) & 0xFFFFFFFF, (
            f"CRC mismatch on {tag!r} chunk"
        )
        chunks.append((tag, payload))
        offset += 12 + length

    return chunks


def decode_pixels(png: bytes) -> list[list[tuple[int, int, int]]]:
    """Decode an unfiltered 8-bit truecolour PNG back to RGB rows."""
    chunks = dict(iter_chunks(png))
    width, height, depth, colour_type = struct.unpack(">IIBB", chunks[b"IHDR"][:10])
    assert (depth, colour_type) == (8, 2), "expected 8-bit truecolour"

    raw = zlib.decompress(chunks[b"IDAT"])
    stride = width * 3 + 1

    rows: list[list[tuple[int, int, int]]] = []
    for y in range(height):
        line = raw[y * stride : (y + 1) * stride]
        assert line[0] == 0, "every scanline must use filter type 0 (None)"
        pixels = line[1:]
        rows.append(
            [
                (pixels[x * 3], pixels[x * 3 + 1], pixels[x * 3 + 2])
                for x in range(width)
            ]
        )

    return rows


class TestEncodePng:
    def test_round_trips_pixels_exactly(self) -> None:
        original = [
            [(255, 0, 0), (0, 255, 0)],
            [(0, 0, 255), (16, 32, 48)],
        ]
        assert decode_pixels(encode_png(original)) == original

    def test_emits_signature_and_required_chunks_in_order(self) -> None:
        tags = [tag for tag, _ in iter_chunks(encode_png([[(1, 2, 3)]]))]
        assert tags == [b"IHDR", b"IDAT", b"IEND"]

    def test_header_records_dimensions(self) -> None:
        png = encode_png([[(0, 0, 0)] * 5 for _ in range(3)])
        chunks = dict(iter_chunks(png))
        width, height = struct.unpack(">II", chunks[b"IHDR"][:8])
        assert (width, height) == (5, 3)

    def test_single_pixel_is_valid(self) -> None:
        assert decode_pixels(encode_png([[(9, 9, 9)]])) == [[(9, 9, 9)]]

    @pytest.mark.parametrize("rows", [[], [[]]])
    def test_rejects_empty_image(self, rows: list[list[tuple[int, int, int]]]) -> None:
        with pytest.raises(ValueError, match="no pixels"):
            encode_png(rows)

    def test_rejects_ragged_rows(self) -> None:
        with pytest.raises(ValueError, match="same width"):
            encode_png([[(0, 0, 0), (1, 1, 1)], [(2, 2, 2)]])


class TestRenderSeedImage:
    def test_decodes_at_the_declared_size(self) -> None:
        _, contents = render_seed_image(0)
        rows = decode_pixels(contents)
        assert len(rows) == SEED_IMAGE_HEIGHT
        assert all(len(row) == SEED_IMAGE_WIDTH for row in rows)

    def test_is_not_square_so_the_thumbnail_crop_is_exercised(self) -> None:
        assert SEED_IMAGE_WIDTH != SEED_IMAGE_HEIGHT

    def test_is_deterministic_so_reseeding_overwrites_identical_bytes(self) -> None:
        assert render_seed_image(3) == render_seed_image(3)

    def test_uses_both_palette_colours(self) -> None:
        _, background, foreground = SEED_IMAGE_PALETTE[0]
        present = {
            pixel for row in decode_pixels(render_seed_image(0)[1]) for pixel in row
        }
        assert present == {background, foreground}, (
            "a flat image would not show the crop; expected a foreground shape"
        )

    def test_consecutive_images_are_visually_distinct(self) -> None:
        first, second = render_seed_image(0)[1], render_seed_image(1)[1]
        assert first != second

    def test_wraps_around_the_palette(self) -> None:
        size = len(SEED_IMAGE_PALETTE)
        assert render_seed_image(0) == render_seed_image(size)
        assert render_seed_image(1) == render_seed_image(size + 1)

    @pytest.mark.parametrize("index", range(len(SEED_IMAGE_PALETTE)))
    def test_every_palette_entry_renders(self, index: int) -> None:
        filename, contents = render_seed_image(index)
        assert filename.endswith(".png")
        assert filename == f"{SEED_IMAGE_PALETTE[index][0]}.png"
        assert decode_pixels(contents)

    def test_filenames_are_unique_across_the_palette(self) -> None:
        names = [render_seed_image(i)[0] for i in range(len(SEED_IMAGE_PALETTE))]
        assert len(set(names)) == len(names)

    def test_rejects_a_negative_index(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            render_seed_image(-1)
