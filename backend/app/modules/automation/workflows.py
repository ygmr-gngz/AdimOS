from app.modules.automation.tasks import task_daily_brief, task_followup_check

_WORKFLOWS = {
    "daily_brief": {
        "name": "Günlük Özet",
        "description": "Her gün sabah 08:00'de günlük yönetim özeti oluşturur",
        "task": task_daily_brief,
    },
    "followup_check": {
        "name": "Takip Kontrolü",
        "description": "Her gün sabah 09:00'da takip edilmesi gereken lead'leri listeler",
        "task": task_followup_check,
    },
}


def list_workflows() -> list[dict]:
    return [
        {"id": wid, "name": w["name"], "description": w["description"]}
        for wid, w in _WORKFLOWS.items()
    ]


def run_workflow(workflow_id: str) -> dict:
    workflow = _WORKFLOWS.get(workflow_id)
    if not workflow:
        return {"error": f"İş akışı bulunamadı: {workflow_id}"}
    return {"workflow_id": workflow_id, "result": workflow["task"]()}
