import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db, init_db
from app.db.models import ApprovalRequest, WorkflowRun
from app.services.workflow_service import approve_action, reject_action

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_approval_flow_rejection():
    # Submit workflow that triggers approval (sending email)
    res = client.post(
        "/api/workflows/run",
        json={"goal": "Send an email to alert@example.com with subject Warning and body High load."},
    )
    assert res.status_code == 200
    data = res.json()
    run_id = data["run_id"]
    assert data["status"] == "awaiting_approval"

    # List pending approvals
    app_res = client.get("/api/approvals")
    assert app_res.status_code == 200
    approvals = app_res.json()
    matching = [a for a in approvals if a["run_id"] == run_id]
    assert len(matching) == 1
    approval_id = matching[0]["id"]
    assert matching[0]["status"] == "pending"

    # Reject the approval
    reject_res = client.post(
        f"/api/approvals/{approval_id}/reject",
        json={"notes": "Security test rejection"},
    )
    assert reject_res.status_code == 200
    reject_data = reject_res.json()
    assert reject_data["success"] is True
    assert reject_data["approval"]["status"] == "rejected"
    assert reject_data["workflow_status"] == "cancelled"

    # Verify workflow state in DB
    detail_res = client.get(f"/api/workflows/history/{run_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["status"] == "cancelled"
    assert "Security test rejection" in detail_res.json()["message"]


def test_cancel_workflow():
    # Create workflow
    res = client.post(
        "/api/workflows/run",
        json={"goal": "Send an email to boss@example.com with subject Status and body Done."},
    )
    run_id = res.json()["run_id"]

    cancel_res = client.post(f"/api/workflows/{run_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    detail = client.get(f"/api/workflows/history/{run_id}").json()
    assert detail["status"] == "cancelled"
