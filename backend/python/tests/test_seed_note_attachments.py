"""Tests for how the seed script attaches images to notes.

These cover the pure selection logic and the stable-key upload contract, so
they need neither a database nor a bucket. The end-to-end assertion that
seeded notes actually carry attachments lives in ``test_seed_database.py``.
"""

import logging
import random
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import app.seed_database as seed_module
from app.utilities.gcp_client import GCPStorageClient
from app.utilities.seed_images import render_seed_image


@pytest.fixture
def pool() -> list[dict[str, str]]:
    return [
        {"filename": f"seed/note-images/{i:02d}-image.png", "url": f"https://x/{i}"}
        for i in range(seed_module.SEED_NOTE_IMAGE_COUNT)
    ]


class TestPickNoteAttachments:
    def test_returns_nothing_when_the_pool_is_empty(self) -> None:
        with patch.object(seed_module.random, "random", return_value=0.0):
            assert seed_module.pick_note_attachments([]) == []

    def test_returns_nothing_when_the_roll_misses(
        self, pool: list[dict[str, str]]
    ) -> None:
        with patch.object(seed_module.random, "random", return_value=1.0):
            assert seed_module.pick_note_attachments(pool) == []

    def test_boundary_roll_is_exclusive(self, pool: list[dict[str, str]]) -> None:
        """A roll exactly at the threshold must not attach; ``random()`` is [0, 1)."""
        threshold = seed_module.PROBABILITY_LOCATION_NOTE_IMAGES
        with patch.object(seed_module.random, "random", return_value=threshold):
            assert seed_module.pick_note_attachments(pool) == []

    def test_attaches_when_the_roll_hits(self, pool: list[dict[str, str]]) -> None:
        with patch.object(seed_module.random, "random", return_value=0.0):
            assert seed_module.pick_note_attachments(pool)

    def test_never_exceeds_the_frontend_cap(self, pool: list[dict[str, str]]) -> None:
        random.seed(20260812)
        for _ in range(500):
            chosen = seed_module.pick_note_attachments(pool)
            assert len(chosen) <= seed_module.MAX_NOTE_IMAGES

    def test_never_repeats_an_image_within_one_note(
        self, pool: list[dict[str, str]]
    ) -> None:
        random.seed(20260812)
        for _ in range(500):
            chosen = seed_module.pick_note_attachments(pool)
            filenames = [item["filename"] for item in chosen]
            assert len(set(filenames)) == len(filenames)

    def test_handles_a_pool_smaller_than_the_cap(self) -> None:
        small = [{"filename": "a.png", "url": "https://x/a"}]
        with patch.object(seed_module.random, "random", return_value=0.0):
            assert seed_module.pick_note_attachments(small) == small

    def test_returns_copies_so_notes_cannot_alias_one_dict(
        self, pool: list[dict[str, str]]
    ) -> None:
        with patch.object(seed_module.random, "random", return_value=0.0):
            chosen = seed_module.pick_note_attachments(pool)
        chosen[0]["url"] = "mutated"
        assert all(item["url"] != "mutated" for item in pool)

    def test_every_attachment_carries_filename_and_url(
        self, pool: list[dict[str, str]]
    ) -> None:
        random.seed(7)
        for _ in range(100):
            for item in seed_module.pick_note_attachments(pool):
                assert set(item) == {"filename", "url"}
                assert item["filename"] and item["url"]

    def test_roughly_matches_the_configured_probability(
        self, pool: list[dict[str, str]]
    ) -> None:
        random.seed(20260812)
        trials = 4000
        hits = sum(1 for _ in range(trials) if seed_module.pick_note_attachments(pool))
        expected = seed_module.PROBABILITY_LOCATION_NOTE_IMAGES
        assert abs(hits / trials - expected) < 0.05


class TestUploadSeedNoteImages:
    @pytest.fixture(autouse=True)
    def configured_gcs(self) -> Any:
        """Pretend GCS is configured.

        Without this the tests would pass or skip depending on whether the
        machine running them happens to have GCP credentials in its env — which
        is exactly the difference between a laptop and CI.
        """
        with patch.multiple(
            seed_module.settings,
            gcp_bucket_name="test-bucket",
            gcp_service_account_private_key="-----BEGIN PRIVATE KEY-----test",
        ):
            yield

    def _client(self) -> tuple[MagicMock, list[dict[str, Any]]]:
        calls: list[dict[str, Any]] = []

        def upload_file(
            contents: bytes,
            filename: str,
            content_type: str,
            expiration_hours: int = 1,
            key: str | None = None,
        ) -> Any:
            calls.append(
                {
                    "contents": contents,
                    "filename": filename,
                    "content_type": content_type,
                    "expiration_hours": expiration_hours,
                    "key": key,
                }
            )
            return MagicMock(filename=key, url=f"https://signed/{key}")

        client = MagicMock()
        client.upload_file.side_effect = upload_file
        # The uploads run concurrently, so `calls` arrives in whatever order
        # the pool finishes in. Assert on what each key was given, never on
        # the order the recorder saw them.
        return client, calls

    def test_uploads_one_object_per_configured_image(self) -> None:
        client, calls = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client):
            attachments = seed_module.upload_seed_note_images()

        assert len(calls) == seed_module.SEED_NOTE_IMAGE_COUNT
        assert len(attachments) == seed_module.SEED_NOTE_IMAGE_COUNT

    def test_uses_stable_prefixed_keys_so_reseeding_overwrites(self) -> None:
        client, calls = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client):
            seed_module.upload_seed_note_images()

        keys = [call["key"] for call in calls]
        assert all(
            key.startswith(f"{seed_module.SEED_NOTE_IMAGE_PREFIX}/") for key in keys
        )
        assert len(set(keys)) == len(keys), "keys must be unique within a run"

        client2, calls2 = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client2):
            seed_module.upload_seed_note_images()
        assert sorted(call["key"] for call in calls2) == sorted(keys), (
            "keys must be stable across runs"
        )

    def test_uploads_identical_bytes_across_runs(self) -> None:
        client, calls = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client):
            seed_module.upload_seed_note_images()
        client2, calls2 = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client2):
            seed_module.upload_seed_note_images()

        assert {c["key"]: c["contents"] for c in calls} == {
            c["key"]: c["contents"] for c in calls2
        }

    def test_the_returned_attachments_keep_their_order(self) -> None:
        """Notes sample from this list, so a run-to-run reshuffle would move
        every image even though the objects in the bucket are identical."""
        client, _ = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client):
            first = seed_module.upload_seed_note_images()
        client2, _ = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client2):
            second = seed_module.upload_seed_note_images()

        assert first == second
        assert [a["filename"] for a in first] == [
            f"{seed_module.SEED_NOTE_IMAGE_PREFIX}/{i:02d}-{render_seed_image(i)[0]}"
            for i in range(seed_module.SEED_NOTE_IMAGE_COUNT)
        ]

    def test_uploads_real_png_bytes(self) -> None:
        client, calls = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client):
            seed_module.upload_seed_note_images()

        for call in calls:
            assert call["contents"].startswith(b"\x89PNG\r\n\x1a\n")
            assert call["content_type"] == "image/png"

    def test_requests_a_long_lived_url(self) -> None:
        client, calls = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client):
            seed_module.upload_seed_note_images()

        for call in calls:
            assert call["expiration_hours"] == seed_module.SEED_NOTE_IMAGE_URL_HOURS
            # GCS V4 signing refuses anything beyond seven days.
            assert call["expiration_hours"] <= 24 * 7

    def test_returns_the_stored_key_not_the_local_filename(self) -> None:
        client, _ = self._client()
        with patch.object(seed_module, "GCPStorageClient", return_value=client):
            attachments = seed_module.upload_seed_note_images()

        for attachment in attachments:
            assert attachment["filename"].startswith(
                f"{seed_module.SEED_NOTE_IMAGE_PREFIX}/"
            )
            assert set(attachment) == {"filename", "url"}


class TestUploadSeedNoteImagesWithoutGCS:
    """The seed has to survive an environment with no bucket.

    CI's boot smoke job runs the seed with no GCP settings at all, so uploading
    must degrade to "notes without images" rather than taking the whole seed
    down with it.
    """

    @pytest.mark.parametrize(
        ("bucket", "private_key"),
        [
            ("", ""),
            ("", "-----BEGIN PRIVATE KEY-----test"),
            ("test-bucket", ""),
        ],
    )
    def test_returns_nothing_when_settings_are_missing(
        self, bucket: str, private_key: str
    ) -> None:
        with (
            patch.multiple(
                seed_module.settings,
                gcp_bucket_name=bucket,
                gcp_service_account_private_key=private_key,
            ),
            patch.object(seed_module, "GCPStorageClient") as client_class,
        ):
            assert seed_module.upload_seed_note_images() == []

        # Never even constructed — building the client is what parses the key
        # and raises on a malformed PEM.
        client_class.assert_not_called()

    def test_an_empty_pool_seeds_notes_without_attachments(self) -> None:
        """The skip has to reach the notes, not just the upload helper."""
        random.seed(1)
        for _ in range(50):
            assert seed_module.pick_note_attachments([]) == []


class TestUploadFileKeyOverride:
    """``upload_file`` must keep collision-proof keys for real user uploads."""

    def _client_with_stub_bucket(self) -> tuple[GCPStorageClient, MagicMock]:
        client = GCPStorageClient.__new__(GCPStorageClient)
        client.logger = logging.getLogger(__name__)
        bucket = MagicMock()
        bucket.blob.return_value.generate_signed_url.return_value = "https://signed"
        client.bucket = bucket
        return client, bucket

    def test_defaults_to_a_uuid_prefixed_key(self) -> None:
        client, bucket = self._client_with_stub_bucket()
        result = client.upload_file(b"x", "photo.jpg", "image/jpeg")

        used_key = bucket.blob.call_args[0][0]
        assert used_key.endswith("-photo.jpg")
        assert used_key != "photo.jpg"
        assert result.filename == used_key

    def test_two_uploads_of_one_filename_do_not_collide(self) -> None:
        client, _bucket = self._client_with_stub_bucket()
        first = client.upload_file(b"x", "photo.jpg", "image/jpeg")
        second = client.upload_file(b"y", "photo.jpg", "image/jpeg")
        assert first.filename != second.filename

    def test_explicit_key_is_used_verbatim(self) -> None:
        client, bucket = self._client_with_stub_bucket()
        result = client.upload_file(
            b"x", "photo.jpg", "image/jpeg", key="seed/note-images/00-front-door.png"
        )

        assert bucket.blob.call_args[0][0] == "seed/note-images/00-front-door.png"
        assert result.filename == "seed/note-images/00-front-door.png"

    def test_explicit_key_is_repeatable(self) -> None:
        client, _ = self._client_with_stub_bucket()
        first = client.upload_file(b"x", "a.png", "image/png", key="seed/fixed.png")
        second = client.upload_file(b"y", "a.png", "image/png", key="seed/fixed.png")
        assert first.filename == second.filename == "seed/fixed.png"
