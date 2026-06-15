from fastapi import APIRouter
from app.modules.automation.service import get_scheduled_jobs, get_workflows, trigger_workflow

router = APIRouter()


@router.get("/jobs")
def list_jobs():
    return get_scheduled_jobs()


@router.get("/workflows")
def list_workflows():
    return get_workflows()


@router.post("/workflows/{workflow_id}/run")
def run_workflow(workflow_id: str):
    return trigger_workflow(workflow_id)
