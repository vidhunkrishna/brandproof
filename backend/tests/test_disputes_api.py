"""Authorization and immutable audit coverage for the human review workflow."""
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _token(email, password):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_creator_dispute_reviewer_override_and_duplicate_protection():
    creator = _token("creator@lumen.demo", "LumenCreator2026!")
    reviewer = _token("reviewer@lumen.demo", "LumenReviewer2026!")
    headers = {"Authorization": f"Bearer {creator}"}
    created = client.post("/api/v1/submissions/", headers=headers, json={
        "title": f"Dispute workflow {uuid.uuid4().hex[:8]}",
        "content_type": "website_copy",
        "content_text": "Every Lumen product comes with a lifetime warranty.",
    })
    assert created.status_code == 201
    finding = next(item for item in created.json()["review_result"]["findings"] if item["verdict"] == "CONTRADICTED")

    dispute = client.post("/api/v1/disputes/", headers=headers, json={
        "finding_id": finding["id"], "reason": "The supplied policy has a documented exception for this product line.",
    })
    assert dispute.status_code == 201
    dispute_id = dispute.json()["id"]
    assert dispute.json()["finding"]["verdict"] == "CONTRADICTED"

    duplicate = client.post("/api/v1/disputes/", headers=headers, json={
        "finding_id": finding["id"], "reason": "Submitting a second active dispute must be rejected.",
    })
    assert duplicate.status_code == 409

    creator_resolution = client.post(f"/api/v1/disputes/{dispute_id}/resolve", headers=headers, json={
        "action": "uphold", "reason": "Creators may not resolve their own disputes.",
    })
    assert creator_resolution.status_code == 403

    resolved = client.post(f"/api/v1/disputes/{dispute_id}/resolve", headers={"Authorization": f"Bearer {reviewer}"}, json={
        "action": "override", "override_verdict": "UNVERIFIABLE",
        "reason": "The cited policy exception prevents a conclusive lifetime-warranty verdict.",
    })
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "rejected"
    assert resolved.json()["override_verdict"] == "UNVERIFIABLE"
    # Original finding remains untouched; the override is an auditable dispute layer.
    assert resolved.json()["finding"]["verdict"] == "CONTRADICTED"

    queue = client.get("/api/v1/disputes/?queue_only=true", headers={"Authorization": f"Bearer {reviewer}"})
    assert queue.status_code == 200
    assert all(item["status"] in {"open", "needs_info"} for item in queue.json())
