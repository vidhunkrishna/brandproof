from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def _token(email, password):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_guideline_health_is_admin_scoped_and_evidence_shaped():
    admin = _token("admin@lumen.demo", "LumenAdmin2026!")
    response = client.get("/api/v1/guideline-health/", headers={"Authorization": f"Bearer {admin}"})
    assert response.status_code == 200
    payload = response.json()
    assert {"active_guideline_count", "healthy_guidelines", "warnings"} <= payload.keys()
    for warning in payload["warnings"]:
        assert {"guideline_id", "reason", "recommendation", "evidence"} <= warning.keys()
    creator = _token("creator@lumen.demo", "LumenCreator2026!")
    denied = client.get("/api/v1/guideline-health/", headers={"Authorization": f"Bearer {creator}"})
    assert denied.status_code == 403
