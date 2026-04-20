from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import veritabani_al
from core.security import token_dogrula
from app.models.base import Kullanici, HataOturumu
from app.services.oturum_servisi import aylik_maliyet_ozeti, kullanici_aktif_calisma_alani, kullanici_calisma_alanlarini_getir

router = APIRouter(prefix="/pano", tags=["Pano"])
sablonlar = Jinja2Templates(directory="app/templates")

def mevcut_kullanici(request: Request, vt: Session):
    token = request.cookies.get("erisim_tokeni")
    if not token:
        return None
    kullanici_id = token_dogrula(token)
    if not kullanici_id:
        return None
    kullanici = vt.query(Kullanici).filter(Kullanici.id == int(kullanici_id)).first()
    return kullanici

@router.get("/", response_class=HTMLResponse)
async def pano_sayfasi(request: Request, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")

    calisma_alani = kullanici_aktif_calisma_alani(vt, kullanici.id)

    toplam_oturum = 0
    cozulen_oturum = 0
    bekleyen_oturum = 0
    oturumlar = []

    if calisma_alani:
        oturumlar = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id).order_by(HataOturumu.olusturulma_tarihi.desc()).limit(5).all()
        toplam_oturum = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id).count()
        cozulen_oturum = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id, HataOturumu.durum == "tamamlandi").count()
        bekleyen_oturum = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id, HataOturumu.durum == "bekliyor").count()

    return sablonlar.TemplateResponse(request=request, name="dashboard/index.html", context={
        "kullanici": kullanici,
        "oturumlar": oturumlar,
        "aktif_calisma_alani": calisma_alani,
        "calisma_alanlari": kullanici_calisma_alanlarini_getir(vt, kullanici.id),
        "maliyet_ozeti": aylik_maliyet_ozeti(vt, kullanici.id),
        "istatistikler": {
            "toplam": toplam_oturum,
            "cozulen": cozulen_oturum,
            "bekleyen": bekleyen_oturum
        }
    })
