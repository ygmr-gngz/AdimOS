import logging
import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from app.modules.content.service import (
    create_normal_video, create_short_video, create_post,
    create_question_solution_video, create_topic_explanation_video,
    publish_to_youtube, publish_to_instagram,
)
from app.db.repositories.generated_contents_repo import (
    create_content, update_content, get_content, list_contents,
    delete_content as db_delete, delete_orphan_contents,
)
from app.modules.content.cleanup import (
    run_full_cleanup, run_health_check, safe_delete_content,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ContentRequest(BaseModel):
    topic: str
    duration_minutes: int = 5
    question_text: str = ""
    category: str = "smmm"  # smmm | sgs | genel


class ApproveRequest(BaseModel):
    action: str  # "approve" | "reject"
    notes: str = ""


class EditRequest(BaseModel):
    message: str


class MotivationRequest(BaseModel):
    topic: str
    platform: str = "reels"   # reels | shorts | carousel | post
    tone: str = "sıcak ve samimi"


def _background_generate(content_id: str, fn, *args):
    from app.api.routes.notifications import push_notification
    try:
        logger.info(f"[content] üretim başladı id={content_id}")
        result = fn(*args)
        updates = {"status": "pending_approval"}
        for field in ("video_path", "audio_path", "image_path", "title", "caption", "script", "audio_base64"):
            if result.get(field):
                db_field = "video_url" if field == "video_path" else (
                    "audio_url" if field == "audio_path" else (
                    "image_url" if field == "image_path" else field))
                updates[db_field] = result[field]
        update_content(content_id, updates)
        title = result.get("title") or "İçerik"
        push_notification("content", f"İçerik hazır: {title}", "Onay bekliyor — Otomasyon sayfasından onaylayabilirsiniz.")
        logger.info(f"[content] üretim tamamlandı id={content_id}")
    except Exception as e:
        logger.error(f"[content] üretim hatası id={content_id} hata={e}", exc_info=True)
        update_content(content_id, {"status": "error", "error_detail": str(e)[:300]})
        push_notification("content_error", "İçerik üretim hatası", f"Üretim başarısız: {str(e)[:120]}")


# ── Generate endpoints (eski otomasyon kaynakları — SADECE Video Prodüksiyon'dan çağrılabilir)
# GÖREV 1: Bu endpointler İçerik Otomasyonu'ndan kaldırıldı.
# Frontend artık bu endpointleri çağırmıyor; koruma için 403 dönülür.

_AUTOMATION_DISABLED_MSG = (
    "Bu endpoint devre dışı bırakıldı. İçerik Otomasyonu artık kendi video üretimi yapmaz — "
    "Video Prodüksiyon (/video/create) kullanın."
)


@router.post("/video/generate")
def generate_video(req: ContentRequest, bg: BackgroundTasks):
    raise HTTPException(status_code=403, detail=_AUTOMATION_DISABLED_MSG)


@router.post("/short/generate")
def generate_short(req: ContentRequest, bg: BackgroundTasks):
    raise HTTPException(status_code=403, detail=_AUTOMATION_DISABLED_MSG)


@router.post("/post/generate")
def generate_post_endpoint(req: ContentRequest, bg: BackgroundTasks):
    raise HTTPException(status_code=403, detail=_AUTOMATION_DISABLED_MSG)


@router.post("/question-solution/generate")
def generate_question_solution(req: ContentRequest, bg: BackgroundTasks):
    raise HTTPException(status_code=403, detail=_AUTOMATION_DISABLED_MSG)


@router.post("/topic-explanation/generate")
def generate_topic_explanation(req: ContentRequest, bg: BackgroundTasks):
    raise HTTPException(status_code=403, detail=_AUTOMATION_DISABLED_MSG)


# ── Motivasyon videosu
def _bg_motivation(content_id: str, topic: str, platform: str, tone: str):
    from app.api.routes.notifications import push_notification
    from app.modules.content.motivation_generator import generate_motivation_storyboard
    from app.db.repositories.brand_repo import configure_video_watermark

    try:
        configure_video_watermark("motivation_video")

        storyboard = generate_motivation_storyboard(topic, platform, tone)
        scenes = storyboard.get("scenes", [])
        if not scenes:
            raise RuntimeError("Storyboard sahne içermiyor")

        # Sahne verilerinden dummy soru ID'leri oluştur (storyboard'u recycle ediyoruz)
        fake_plan = {
            "title": storyboard.get("title", f"Motivasyon: {topic}"),
            "topic": topic,
            "subject": "Motivasyon",
            "question_ids": [],
            "description": storyboard.get("description", ""),
            "_storyboard_override": storyboard,  # service'e direkt geçir
        }

        # Video üret (storyboard_override ile)
        from app.modules.sgs.storyboard import generate_sgs_topic_storyboard
        from app.modules.content.audio_generator import generate_audio_segment
        from app.modules.content.scene_engine import render_scene
        from app.modules.content.video_assembler import assemble_video
        from moviepy.editor import AudioFileClip
        from app.modules.voice.tts import synthesize

        clips = []
        audio_clips = []
        preview_narration = ""

        for i, scene in enumerate(scenes):
            narration = str(scene.get("narration", "")).strip() or scene.get("title", "devam")
            audio_path, audio_dur = generate_audio_segment(narration)
            clip = render_scene(scene, i + 1, len(scenes))
            clip = clip.set_duration(audio_dur)
            aclip = AudioFileClip(audio_path)
            audio_clips.append(aclip)
            clip = clip.set_audio(aclip)
            clips.append(clip)
            if i == 1:
                preview_narration = narration

        video_path = assemble_video(clips)
        for ac in audio_clips:
            try: ac.close()
            except Exception: pass

        try:
            audio_b64 = synthesize(preview_narration[:800], voice="nova")
        except Exception:
            audio_b64 = None

        update_content(content_id, {
            "status": "pending_approval",
            "video_url": video_path,
            "title": storyboard.get("title", topic),
            "script": "\n\n".join(f"{s.get('title','')}\n{s.get('narration','')}" for s in scenes),
            "audio_base64": audio_b64,
        })
        push_notification("content", f"Motivasyon videosu hazır: {storyboard.get('title', topic)}", "Onay bekliyor")
    except Exception as e:
        logger.error(f"[motivation] hata id={content_id}: {e}", exc_info=True)
        update_content(content_id, {"status": "error", "error_detail": str(e)[:300]})


@router.post("/motivation/generate")
def generate_motivation(req: MotivationRequest, bg: BackgroundTasks):
    row = create_content(f"Motivasyon: {req.topic[:50]}", "motivation_video")
    bg.add_task(_bg_motivation, row["id"], req.topic, req.platform, req.tone)
    return {"content_id": row["id"], "status": "generating", "topic": req.topic, "platform": req.platform}


# ── List / Get

@router.get("")
def list_content():
    return list_contents()


@router.get("/{content_id}")
def get_content_by_id(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    return item


# ── Approve / Reject

@router.patch("/{content_id}/approve")
def approve_content(content_id: str, req: ApproveRequest):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    new_status = "approved" if req.action == "approve" else "rejected"
    updates: dict = {"status": new_status}
    if req.notes:
        updates["approval_notes"] = req.notes
    return update_content(content_id, updates)


# ── Edit (doğal dil ile yeniden üretim)

@router.post("/{content_id}/edit")
def edit_content(content_id: str, req: EditRequest, bg: BackgroundTasks):
    """Doğal dil komutu ile içeriği analiz et ve arka planda yeniden üret."""
    from app.modules.content.editor import build_edit_plan

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Düzenleme mesajı boş olamaz")

    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")

    plan = build_edit_plan(item, req.message)
    enhanced_topic = plan.get("enhanced_topic") or (
        (item.get("topic") or item.get("title", "")) + f". {req.message}"
    )
    content_type = item.get("type", "video")
    category = item.get("category", "smmm")

    fn_map = {
        "video": (create_normal_video, (enhanced_topic, 5, category)),
        "short": (create_short_video, (enhanced_topic, category)),
        "post": (create_post, (enhanced_topic,)),
        "question_solution": (create_question_solution_video, (enhanced_topic, "", category)),
        "topic_explanation": (create_topic_explanation_video, (enhanced_topic, category)),
        "sgs_topic_video": (create_topic_explanation_video, (enhanced_topic, "sgs")),
    }
    fn, args = fn_map.get(content_type, (create_normal_video, (enhanced_topic, 5, "smmm")))

    update_content(content_id, {
        "status": "generating",
        "video_url": None,
        "audio_base64": None,
        "error_detail": None,
    })

    bg.add_task(_background_generate, content_id, fn, *args)

    return {
        "content_id": content_id,
        "status": "regenerating",
        "changes_summary": plan.get("changes_summary", [req.message]),
        "explanation": plan.get("explanation", ""),
    }


# ── Validate (video URL erişilebilir mi?)

@router.post("/{content_id}/validate")
async def validate_content(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")

    video_url = item.get("video_url") or item.get("image_url") or ""

    if not video_url or not video_url.startswith("http"):
        return {
            "valid": False, "playable": False,
            "reason": "Video URL bulunamadı veya geçersiz",
            "storageExists": False,
        }

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.head(video_url)
            ok = resp.status_code < 400
            size = int(resp.headers.get("content-length", 0))
            content_type = resp.headers.get("content-type", "")
            playable = ok and size > 1000 and ("video" in content_type or "octet" in content_type or video_url.endswith(".mp4"))
            return {
                "valid": ok,
                "playable": playable,
                "storageExists": ok,
                "size_bytes": size,
                "content_type": content_type,
                "reason": None if ok else f"HTTP {resp.status_code}",
            }
    except Exception as e:
        return {
            "valid": False, "playable": False,
            "storageExists": False,
            "reason": str(e)[:120],
        }


# ── Publish

@router.post("/{content_id}/publish")
def publish_content_unified(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    content_type = item.get("type", "video")
    if content_type in ("video", "short", "question_solution", "topic_explanation"):
        result = publish_to_youtube(item)
        platform = "youtube"
    else:
        result = publish_to_instagram(item)
        platform = "instagram"
    update_content(content_id, {"status": "published"})
    return {"content_id": content_id, "platform": platform, "status": "published", **result}


@router.post("/{content_id}/publish/youtube")
def publish_youtube(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    result = publish_to_youtube(item)
    update_content(content_id, {"status": "published"})
    return result


@router.post("/{content_id}/publish/instagram")
def publish_instagram(content_id: str):
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    result = publish_to_instagram(item)
    update_content(content_id, {"status": "published"})
    return result


# ── Retry failed content

@router.post("/{content_id}/retry")
def retry_content(content_id: str, bg: BackgroundTasks):
    """Başarısız içeriği aynı konu ile yeniden üret."""
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    if item.get("status") not in ("error", "failed", "corrupted", "rejected"):
        raise HTTPException(status_code=400, detail="Sadece hatalı içerikler yeniden üretilebilir")

    topic = item.get("topic") or item.get("title", "")
    content_type = item.get("type", "video")
    category = item.get("category", "smmm")

    fn_map = {
        "video": (create_normal_video, (topic, 5, category)),
        "short": (create_short_video, (topic, category)),
        "post": (create_post, (topic,)),
        "question_solution": (create_question_solution_video, (topic, "", category)),
        "topic_explanation": (create_topic_explanation_video, (topic, category)),
        "sgs_topic_video": (create_topic_explanation_video, (topic, "sgs")),
    }
    fn, args = fn_map.get(content_type, (create_normal_video, (topic, 5, "smmm")))

    update_content(content_id, {
        "status": "generating",
        "error_detail": None,
        "video_url": None,
        "audio_base64": None,
    })
    bg.add_task(_background_generate, content_id, fn, *args)
    return {"content_id": content_id, "status": "retrying"}


# ── Archive

@router.patch("/{content_id}/archive")
def archive_content(content_id: str):
    """İçeriği silmek yerine arşivle."""
    item = get_content(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="İçerik bulunamadı")
    return update_content(content_id, {"status": "archived"})


# ── Health check + Full cleanup

@router.post("/health-check")
def health_check():
    """Sorunlu içerikleri tespit edip 'corrupted' olarak işaretle."""
    result = run_health_check()
    return result


@router.post("/cleanup")
def full_cleanup():
    """Tam sistem temizliği — hatalı, yetim, takılı içerikleri sil."""
    result = run_full_cleanup()
    return result


# ── Legacy orphan (backwards compat)

@router.delete("/orphan")
def cleanup_orphan():
    count = delete_orphan_contents()
    return {"deleted": count}


# ── Delete (storage dahil)

@router.delete("/{content_id}")
def delete_content(content_id: str):
    safe_delete_content(content_id)
    return {"message": "İçerik ve dosyalar silindi"}
