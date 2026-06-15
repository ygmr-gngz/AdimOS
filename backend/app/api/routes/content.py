from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.modules.content.service import (
    create_normal_video, create_short_video, create_post,
    publish_to_youtube, publish_to_instagram,
)
import uuid

router = APIRouter()

# Üretilen içerikleri bellekte tut (Supabase'e taşınacak)
_store: dict[str, dict] = {}


class ContentRequest(BaseModel):
    topic: str
    duration_minutes: int = 5


class ApproveRequest(BaseModel):
    action: str  # "approve" | "reject"
    notes: str = ""


def _background_generate(content_id: str, fn, *args):
    try:
        result = fn(*args)
        result["id"] = content_id
        _store[content_id] = result
    except Exception as e:
        _store[content_id] = {"id": content_id, "status": "error", "error": str(e)}


@router.post("/video/generate")
def generate_video(req: ContentRequest, bg: BackgroundTasks):
    content_id = str(uuid.uuid4())
    _store[content_id] = {"id": content_id, "status": "generating", "type": "video"}
    bg.add_task(_background_generate, content_id, create_normal_video, req.topic, req.duration_minutes)
    return {"content_id": content_id, "status": "generating"}


@router.post("/short/generate")
def generate_short(req: ContentRequest, bg: BackgroundTasks):
    content_id = str(uuid.uuid4())
    _store[content_id] = {"id": content_id, "status": "generating", "type": "short"}
    bg.add_task(_background_generate, content_id, create_short_video, req.topic)
    return {"content_id": content_id, "status": "generating"}


@router.post("/post/generate")
def generate_post(req: ContentRequest, bg: BackgroundTasks):
    content_id = str(uuid.uuid4())
    _store[content_id] = {"id": content_id, "status": "generating", "type": "post"}
    bg.add_task(_background_generate, content_id, create_post, req.topic)
    return {"content_id": content_id, "status": "generating"}


@router.get("")
def list_content():
    return list(_store.values())


@router.get("/{content_id}")
def get_content(content_id: str):
    item = _store.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    return item


@router.post("/{content_id}/publish/youtube")
def publish_youtube(content_id: str):
    item = _store.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    if item.get("type") not in ("video", "short"):
        raise HTTPException(status_code=400, detail="Bu içerik türü YouTube'a yüklenemez")
    result = publish_to_youtube(item)
    _store[content_id]["youtube"] = result
    _store[content_id]["status"] = "published"
    return result


@router.post("/{content_id}/publish/instagram")
def publish_instagram(content_id: str):
    item = _store.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    result = publish_to_instagram(item)
    _store[content_id]["instagram"] = result
    _store[content_id]["status"] = "published"
    return result


@router.patch("/{content_id}/approve")
def approve_content(content_id: str, req: ApproveRequest):
    item = _store.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    new_status = "approved" if req.action == "approve" else "rejected"
    _store[content_id]["status"] = new_status
    if req.notes:
        _store[content_id]["approval_notes"] = req.notes
    return _store[content_id]


@router.post("/{content_id}/publish")
def publish_content(content_id: str):
    item = _store.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    content_type = item.get("type", "video")
    if content_type in ("video", "short"):
        result = publish_to_youtube(item)
        _store[content_id]["youtube"] = result
        platform = "youtube"
    else:
        result = publish_to_instagram(item)
        _store[content_id]["instagram"] = result
        platform = "instagram"
    _store[content_id]["status"] = "published"
    return {"content_id": content_id, "platform": platform, "status": "published"}


@router.delete("/{content_id}")
def delete_content(content_id: str):
    _store.pop(content_id, None)
    return {"message": "İçerik silindi"}
