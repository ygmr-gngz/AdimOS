"""İçerik sağlık kontrolü ve temizleme sistemi."""
import logging
from datetime import datetime, timedelta
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)
_TABLE = "generated_contents"
_BUCKET = "content"


def _extract_storage_path(url: str | None) -> str | None:
    if not url:
        return None
    try:
        marker = f"/object/public/{_BUCKET}/"
        idx = url.find(marker)
        return url[idx + len(marker):] if idx != -1 else None
    except Exception:
        return None


def _safe_delete_storage(url: str | None) -> bool:
    path = _extract_storage_path(url)
    if not path:
        return False
    try:
        from app.db.storage import delete_file
        delete_file(_BUCKET, path)
        return True
    except Exception as e:
        logger.warning(f"[cleanup] storage silinemedi path={path}: {e}")
        return False


def run_health_check() -> dict:
    """Sorunlu içerikleri tespit edip 'corrupted' olarak işaretle."""
    sb = get_supabase_client()
    two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat()
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    marked = 0

    # Generating ama 2 saatten eski → takılı kalmış
    try:
        stuck = (
            sb.table(_TABLE).select("id")
            .eq("status", "generating")
            .lt("created_at", two_hours_ago)
            .execute()
        )
        ids = [r["id"] for r in (stuck.data or [])]
        if ids:
            sb.table(_TABLE).update({
                "status": "corrupted",
                "error_detail": "Render takılı kaldı (>2 saat)"
            }).in_("id", ids).execute()
            marked += len(ids)
    except Exception as e:
        logger.warning(f"[health] stuck check hatası: {e}")

    # pending_approval ama dosya yok ve 1 saatten eski
    try:
        broken = (
            sb.table(_TABLE).select("id")
            .eq("status", "pending_approval")
            .is_("video_url", "null")
            .is_("image_url", "null")
            .lt("created_at", one_hour_ago)
            .execute()
        )
        ids = [r["id"] for r in (broken.data or [])]
        if ids:
            sb.table(_TABLE).update({
                "status": "corrupted",
                "error_detail": "Onay bekliyor ama medya dosyası yok"
            }).in_("id", ids).execute()
            marked += len(ids)
    except Exception as e:
        logger.warning(f"[health] broken pending check hatası: {e}")

    return {"marked_corrupted": marked}


def run_full_cleanup() -> dict:
    """Tam temizlik — hatalı, yetim, takılı kayıtları sil, storage dosyalarını temizle."""
    sb = get_supabase_client()
    two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat()

    report = {
        "deleted_failed": 0,
        "deleted_stuck": 0,
        "deleted_corrupted": 0,
        "deleted_orphan": 0,
        "storage_cleaned": 0,
    }

    def _delete_rows(rows: list[dict], key: str):
        cleaned = 0
        for row in rows:
            cleaned += _safe_delete_storage(row.get("video_url"))
            cleaned += _safe_delete_storage(row.get("image_url"))
        ids = [r["id"] for r in rows]
        if ids:
            sb.table(_TABLE).delete().in_("id", ids).execute()
        report["storage_cleaned"] += cleaned
        return len(ids)

    # 1. error / failed
    try:
        rows = (
            sb.table(_TABLE).select("id, video_url, image_url")
            .in_("status", ["error", "failed"])
            .execute()
        ).data or []
        report["deleted_failed"] = _delete_rows(rows, "error/failed")
    except Exception as e:
        logger.warning(f"[cleanup] failed delete hatası: {e}")

    # 2. corrupted
    try:
        rows = (
            sb.table(_TABLE).select("id, video_url, image_url")
            .eq("status", "corrupted")
            .execute()
        ).data or []
        report["deleted_corrupted"] = _delete_rows(rows, "corrupted")
    except Exception as e:
        logger.warning(f"[cleanup] corrupted delete hatası: {e}")

    # 3. generating > 2 saat
    try:
        rows = (
            sb.table(_TABLE).select("id, video_url, image_url")
            .eq("status", "generating")
            .lt("created_at", two_hours_ago)
            .execute()
        ).data or []
        report["deleted_stuck"] = _delete_rows(rows, "stuck")
    except Exception as e:
        logger.warning(f"[cleanup] stuck delete hatası: {e}")

    # 4. Orphan — URL yok, önemli durum değil
    PROTECTED = ["generating", "approved", "published", "scheduled", "pending_approval", "archived"]
    try:
        rows = (
            sb.table(_TABLE).select("id")
            .is_("video_url", "null")
            .is_("image_url", "null")
            .not_.in_("status", PROTECTED)
            .execute()
        ).data or []
        ids = [r["id"] for r in rows]
        if ids:
            sb.table(_TABLE).delete().in_("id", ids).execute()
        report["deleted_orphan"] = len(ids)
    except Exception as e:
        logger.warning(f"[cleanup] orphan delete hatası: {e}")

    report["total_deleted"] = (
        report["deleted_failed"] + report["deleted_stuck"]
        + report["deleted_corrupted"] + report["deleted_orphan"]
    )
    logger.info(f"[cleanup] tamamlandı: {report}")
    return report


def safe_delete_content(content_id: str) -> None:
    """İçeriği ve storage dosyalarını birlikte sil."""
    sb = get_supabase_client()
    try:
        row = sb.table(_TABLE).select("video_url, image_url").eq("id", content_id).execute()
        if row.data:
            _safe_delete_storage(row.data[0].get("video_url"))
            _safe_delete_storage(row.data[0].get("image_url"))
    except Exception as e:
        logger.warning(f"[cleanup] storage silinemedi id={content_id}: {e}")
    sb.table(_TABLE).delete().eq("id", content_id).execute()
