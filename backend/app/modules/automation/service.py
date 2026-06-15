from app.modules.automation.scheduler import get_jobs
from app.modules.automation.workflows import list_workflows, run_workflow


def get_scheduled_jobs() -> list[dict]:
    return get_jobs()


def get_workflows() -> list[dict]:
    return list_workflows()


def trigger_workflow(workflow_id: str) -> dict:
    return run_workflow(workflow_id)
