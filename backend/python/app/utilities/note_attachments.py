from app.models.note import Attachment
from app.utilities.gcp_client import GCPStorageClient


def refresh_attachment_urls(
    attachments: list[Attachment] | None,
    gcp_client: GCPStorageClient,
    *,
    expiration_hours: int = 24,
) -> list[Attachment]:
    """Replace stored (possibly expired) signed URLs with fresh ones.

    ``filename`` is the durable GCS object key; ``url`` from upload is only a
    short-lived signed GET link and must not be treated as permanent.
    """
    if not attachments:
        return []
    return [
        Attachment(
            filename=attachment.filename,
            url=gcp_client.generate_signed_url(
                attachment.filename, expiration_hours=expiration_hours
            ),
        )
        for attachment in attachments
    ]
