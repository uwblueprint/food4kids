from uuid import UUID

from sqlmodel import SQLModel


class GoogleMapsLinkResponse(SQLModel):
    """Response containing a Google Maps directions URL for a route."""

    route_id: UUID
    google_maps_url: str