from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.base import CalismaAlani, Kullanici, KullaniciAyari
from core.database import veritabani_al
from core.security import erisim_tokeni_olustur, sifre_dogrula, sifre_hashle

router = APIRouter(prefix="/yetkilendirme", tags=["Yetkilendirme"])
sablonlar = Jinja2Templates(directory="app/templates")


@router.get("/giris", response_class=HTMLResponse)
async def giris_sayfasi(request: Request):
    return sablonlar.TemplateResponse(request=request, name="auth/login.html")


@router.post("/giris")
async def giris_islem(request: Request, eposta: str = Form(...), sifre: str = Form(...), vt: Session = Depends(veritabani_al)):
    kullanici = vt.query(Kullanici).filter(Kullanici.eposta == eposta).first()
    if not kullanici or not sifre_dogrula(sifre, kullanici.sifre_hash):
        return sablonlar.TemplateResponse(request=request, name="auth/login.html", context={"hata": "E-posta veya şifre hatalı."})
    token = erisim_tokeni_olustur({"sub": str(kullanici.id)})
    yanit = RedirectResponse(url="/pano", status_code=status.HTTP_302_FOUND)
    yanit.set_cookie(key="erisim_tokeni", value=token, httponly=True)
    return yanit


@router.get("/kayit", response_class=HTMLResponse)
async def kayit_sayfasi(request: Request):
    return sablonlar.TemplateResponse(request=request, name="auth/register.html")


@router.post("/kayit")
async def kayit_islem(request: Request, ad_soyad: str = Form(...), eposta: str = Form(...), sifre: str = Form(...), vt: Session = Depends(veritabani_al)):
    mevcut = vt.query(Kullanici).filter(Kullanici.eposta == eposta).first()
    if mevcut:
        return sablonlar.TemplateResponse(request=request, name="auth/register.html", context={"hata": "Bu e-posta adresi zaten kullanımda."})
    yeni_kullanici = Kullanici(ad_soyad=ad_soyad, eposta=eposta, sifre_hash=sifre_hashle(sifre))
    vt.add(yeni_kullanici)
    vt.commit()
    vt.refresh(yeni_kullanici)
    yeni_alan = CalismaAlani(isim="Kişisel Çalışma Alanı", sahip_id=yeni_kullanici.id, aktif_mi=True)
    vt.add(yeni_alan)
    vt.commit()
    vt.refresh(yeni_alan)
    kullanici_ayari = KullaniciAyari(kullanici_id=yeni_kullanici.id, aktif_calisma_alani_id=yeni_alan.id)
    vt.add(kullanici_ayari)
    vt.commit()
    return RedirectResponse(url="/yetkilendirme/giris", status_code=status.HTTP_302_FOUND)


@router.get("/cikis")
async def cikis_islem():
    yanit = RedirectResponse(url="/yetkilendirme/giris", status_code=status.HTTP_302_FOUND)
    yanit.delete_cookie("erisim_tokeni")
    return yanit
