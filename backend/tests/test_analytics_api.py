from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def login(email,password):
 r=client.post('/api/v1/auth/login',json={'email':email,'password':password});assert r.status_code==200;return r.json()['access_token']
def test_analytics_admin_scope_and_real_payload_shape():
 admin=login('admin@lumen.demo','LumenAdmin2026!')
 response=client.get('/api/v1/analytics/',headers={'Authorization':f'Bearer {admin}'})
 assert response.status_code==200
 assert {'kpis','verdicts','trends','guideline_violations','disputes','data_note'}<=response.json().keys()
 creator=login('creator@lumen.demo','LumenCreator2026!')
 assert client.get('/api/v1/analytics/',headers={'Authorization':f'Bearer {creator}'}).status_code==403
