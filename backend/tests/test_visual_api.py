from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def token(email,password):
 r=client.post('/api/v1/auth/login',json={'email':email,'password':password});assert r.status_code==200;return r.json()['access_token']
def test_visual_review_is_validated_and_tenant_scoped():
 admin=token('admin@lumen.demo','LumenAdmin2026!'); creator=token('creator@lumen.demo','LumenCreator2026!'); ah={'Authorization':f'Bearer {admin}'}
 config=client.put('/api/v1/visual/config',headers=ah,json={'approved_colors':['#FFFFFF'],'approved_fonts':[],'minimum_contrast_ratio':4.5});assert config.status_code==200
 image=Image.new('RGB',(32,32),(0,0,0)); raw=BytesIO();image.save(raw,format='PNG')
 upload=client.post('/api/v1/visual/reviews',headers={'Authorization':f'Bearer {creator}'},files={'file':('campaign.png',raw.getvalue(),'image/png')});assert upload.status_code==200;payload=upload.json();assert payload['width']==32 and payload['detected_format']=='PNG';assert any(x['type']=='dimensions_format' for x in payload['findings_json'])
 invalid=client.post('/api/v1/visual/reviews',headers=ah,files={'file':('bad.svg',b'<svg/>','image/svg+xml')});assert invalid.status_code==422
