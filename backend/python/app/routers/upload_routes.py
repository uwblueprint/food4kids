from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies.services import get_gcp_storage_client
from app.utilities.gcp_client import GCPStorageClient, GCSStorageError

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif", "application/pdf"}
MAX_SIZE_MB = 5


@router.post("/")
async def upload_image(
    file: UploadFile = File(...),
    gcp_client: GCPStorageClient = Depends(get_gcp_storage_client),
) -> dict[str, str]:
    """
    Create a file upload
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, detail=f"Unsupported type: {file.content_type}"
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Exceeds {MAX_SIZE_MB}MB limit")

    try:
        result = gcp_client.upload_file(contents, str(file.filename), file.content_type)
    except GCSStorageError as e:
        status_code = 403 if "permission denied" in str(e).lower() else 503
        raise HTTPException(status_code=status_code, detail=str(e)) from e

    return {"url": result.url, "filename": result.filename}


@router.delete("/{filename:path}")
async def delete_image(
    filename: str,
    gcp_client: GCPStorageClient = Depends(get_gcp_storage_client),
) -> dict[str, str]:
    """
    Delete a file given the filename
    """
    try:
        gcp_client.delete_file(filename)
        return {"message": f"Deleted {filename}"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found") from None
    except GCSStorageError as e:
        status_code = 403 if "permission denied" in str(e).lower() else 503
        raise HTTPException(status_code=status_code, detail=str(e)) from e
