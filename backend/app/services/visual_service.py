from io import BytesIO
from math import pow
from PIL import Image, UnidentifiedImageError
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.api.deps import TenantContext
from app.models.visual import VisualBrandConfig, VisualAssetReview
from app.schemas.visual import VisualConfigRequest

MAX_BYTES = 10 * 1024 * 1024
ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}

def _hex(rgb): return "#{:02X}{:02X}{:02X}".format(*rgb)
def _lum(rgb):
    c = [x / 255 for x in rgb]
    c = [x / 12.92 if x <= .04045 else pow((x + .055) / 1.055, 2.4) for x in c]
    return .2126*c[0] + .7152*c[1] + .0722*c[2]
def _contrast(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + .05) / (y + .05)

class VisualService:
    @staticmethod
    def config(db, ctx, req: VisualConfigRequest):
        config = db.query(VisualBrandConfig).filter_by(organization_id=ctx.org_id).first()
        if not config:
            config = VisualBrandConfig(organization_id=ctx.org_id); db.add(config)
        for key, value in req.model_dump().items(): setattr(config, key, value)
        db.commit(); db.refresh(config); return config
    @staticmethod
    def get_config(db, ctx):
        return db.query(VisualBrandConfig).filter_by(organization_id=ctx.org_id).first() or VisualBrandConfig(organization_id=ctx.org_id, approved_colors=[], approved_fonts=[], minimum_contrast_ratio=4.5)
    @staticmethod
    async def review(db: Session, ctx: TenantContext, file: UploadFile):
        data = await file.read(MAX_BYTES + 1)
        if not data or len(data) > MAX_BYTES: raise HTTPException(status_code=413, detail="Image must be between 1 byte and 10 MB.")
        try:
            image = Image.open(BytesIO(data)); image.verify(); image = Image.open(BytesIO(data)); detected_format = image.format; image = image.convert("RGB")
        except (UnidentifiedImageError, OSError): raise HTTPException(status_code=422, detail="Upload must be a valid PNG, JPEG, or WebP image.")
        if detected_format not in ALLOWED_FORMATS: raise HTTPException(status_code=422, detail="Only PNG, JPEG, and WebP images are supported.")
        width, height = image.size
        if width < 16 or height < 16 or width > 10000 or height > 10000: raise HTTPException(status_code=422, detail="Image dimensions must be between 16 and 10000 pixels.")
        config = VisualService.get_config(db, ctx); findings=[]
        sample = image.resize((min(64,width), min(64,height))).getdata(); colors = {}
        for rgb in sample: colors[rgb] = colors.get(rgb, 0) + 1
        dominant = [rgb for rgb, _ in sorted(colors.items(), key=lambda item:item[1], reverse=True)[:5]]
        approved = {value.upper() for value in (config.approved_colors or [])}
        if approved and not any(_hex(rgb) in approved for rgb in dominant): findings.append({"type":"palette","deterministic":True,"issue":"No sampled dominant color matches the approved palette.","expected":sorted(approved),"measured":[_hex(x) for x in dominant],"suggested_correction":"Use an approved brand color in a prominent visual area."})
        if len(dominant) >= 2:
            ratio = _contrast(dominant[0], dominant[1])
            if ratio < config.minimum_contrast_ratio: findings.append({"type":"contrast","deterministic":True,"issue":"The two most common sampled colors are below the configured contrast target.","expected":config.minimum_contrast_ratio,"measured":round(ratio,2),"suggested_correction":"Increase foreground/background contrast; this is a sampled measurement, not text detection."})
        ratio = width / height
        logos = [x for x in (config.primary_logo_aspect_ratio, config.secondary_logo_aspect_ratio) if x]
        if logos and min(abs(ratio-x)/x for x in logos) > .08: findings.append({"type":"logo_aspect_ratio","deterministic":True,"issue":"Asset aspect ratio does not match configured logo ratios within 8%.","expected":logos,"measured":round(ratio,3),"suggested_correction":"This is only an aspect-ratio comparison; confirm logo identity manually."})
        findings.append({"type":"dimensions_format","deterministic":True,"issue":"Asset dimensions and format measured.","expected":"PNG, JPEG, or WebP; 16–10000 px","measured":{"width":width,"height":height,"format":detected_format},"suggested_correction":"No correction required."})
        review = VisualAssetReview(organization_id=ctx.org_id, created_by_user_id=ctx.user.id, filename=(file.filename or "asset")[:255], content_type=file.content_type or "application/octet-stream", byte_size=len(data), width=width, height=height, detected_format=detected_format, findings_json=findings)
        db.add(review); db.commit(); db.refresh(review); return review
    @staticmethod
    def list(db,ctx): return db.query(VisualAssetReview).filter_by(organization_id=ctx.org_id).order_by(VisualAssetReview.created_at.desc()).limit(50).all()
