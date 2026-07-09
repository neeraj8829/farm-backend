from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.deps import require_admin
from app.core.config import settings
from app.core.database import db
from app.models.schemas import MediaCreate
from app.utils.datetime import new_id, now_utc


router = APIRouter(tags=["media"])

_ALLOWED_CONTENT_TYPES = ("image/", "video/")
_ALLOWED_RESOURCE_TYPES = {"image", "video"}


def _get_cloudinary_client() -> tuple[Any, Any, type[Exception]]:
    try:
        import cloudinary as cloudinary_api
        import cloudinary.uploader as cloudinary_uploader
        from cloudinary.exceptions import Error as CloudinaryError
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="Cloudinary SDK is not installed",
        ) from exc

    return cloudinary_api, cloudinary_uploader, CloudinaryError


def _missing_cloudinary_settings() -> list[str]:
    values = (
        ("CLOUDINARY_CLOUD_NAME", settings.cloudinary_cloud_name),
        ("CLOUDINARY_API_KEY", settings.cloudinary_api_key),
        ("CLOUDINARY_API_SECRET", settings.cloudinary_api_secret),
    )
    return [name for name, value in values if not value]


def _configure_cloudinary(cloudinary_api: Any) -> None:
    missing = _missing_cloudinary_settings()
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Cloudinary is not configured: {', '.join(missing)}",
        )

    cloudinary_api.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def _upload_to_cloudinary(file: UploadFile, cloudinary_uploader: Any) -> dict[str, Any]:
    return cloudinary_uploader.upload(
        file.file,
        folder=settings.cloudinary_folder,
        overwrite=False,
        resource_type="auto",
        unique_filename=True,
        use_filename=True,
    )


async def _discard_cloudinary_upload(
    public_id: str,
    resource_type: str,
    cloudinary_uploader: Any,
    cloudinary_error: type[Exception],
) -> None:
    try:
        await run_in_threadpool(
            cloudinary_uploader.destroy,
            public_id,
            resource_type=resource_type,
        )
    except cloudinary_error:
        pass


async def _save_media_doc(
    *,
    media_type: str,
    category: str,
    url: str,
    alt: str,
    is_hero: bool,
    public_id: str | None = None,
) -> dict[str, Any]:
    count = await db.media.count_documents({})
    doc: dict[str, Any] = {
        "id": new_id(),
        "type": media_type,
        "category": category,
        "url": url,
        "alt": alt,
        "isHero": is_hero,
        "sortOrder": count,
        "created_at": now_utc().isoformat(),
    }
    if public_id:
        doc["publicId"] = public_id

    if is_hero:
        await db.media.update_many({}, {"$set": {"isHero": False}})
    await db.media.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/media")
async def list_media():
    return await db.media.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(500)


@router.post("/media")
async def create_media(body: MediaCreate, user: dict = Depends(require_admin)):
    return await _save_media_doc(
        media_type=body.type,
        category=body.category,
        url=body.url,
        alt=body.alt,
        is_hero=body.isHero,
    )


@router.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    category: str = Form(...),
    alt: str = Form(...),
    is_hero: bool = Form(False, alias="isHero"),
    user: dict = Depends(require_admin),
):
    content_type = (file.content_type or "").lower()
    if content_type and not content_type.startswith(_ALLOWED_CONTENT_TYPES):
        raise HTTPException(
            status_code=400,
            detail="Only image and video uploads are supported",
        )

    cloudinary_api, cloudinary_uploader, cloudinary_error = _get_cloudinary_client()
    _configure_cloudinary(cloudinary_api)

    try:
        await file.seek(0)
        upload_result = await run_in_threadpool(
            _upload_to_cloudinary,
            file,
            cloudinary_uploader,
        )
    except cloudinary_error as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cloudinary upload failed: {exc}",
        ) from exc

    resource_type = upload_result.get("resource_type")
    public_id = upload_result.get("public_id")
    secure_url = upload_result.get("secure_url")

    if resource_type not in _ALLOWED_RESOURCE_TYPES:
        if public_id:
            await _discard_cloudinary_upload(
                public_id,
                resource_type or "raw",
                cloudinary_uploader,
                cloudinary_error,
            )
        raise HTTPException(
            status_code=400,
            detail="Only image and video uploads are supported",
        )

    if not public_id or not secure_url:
        raise HTTPException(
            status_code=502,
            detail="Cloudinary upload returned an invalid response",
        )

    return await _save_media_doc(
        media_type=resource_type,
        category=category,
        url=secure_url,
        alt=alt,
        is_hero=is_hero,
        public_id=public_id,
    )


@router.patch("/media/{mid}/hero")
async def set_hero(mid: str, user: dict = Depends(require_admin)):
    if not await db.media.find_one({"id": mid}):
        raise HTTPException(status_code=404, detail="Media not found")
    await db.media.update_many({}, {"$set": {"isHero": False}})
    await db.media.update_one({"id": mid}, {"$set": {"isHero": True}})
    return {"ok": True}


@router.delete("/media/{mid}")
async def delete_media(mid: str, user: dict = Depends(require_admin)):
    result = await db.media.delete_one({"id": mid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"ok": True}