from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
def test_health_and_readiness_expose_operational_status():
    health=client.get('/health'); assert health.status_code==200; assert health.json()['service']=='BrandProof'
    ready=client.get('/ready'); assert ready.status_code in {200,503}
