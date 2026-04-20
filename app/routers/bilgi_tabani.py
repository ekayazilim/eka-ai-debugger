from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.base import BilgiTabaniKaydi, CalismaAlani, HataOturumu
from app.routers.pano import mevcut_kullanici
from app.services.oturum_servisi import etiketleri_normallestir, kullanici_aktif_calisma_alani, kullanici_calisma_alanlarini_getir
from core.database import veritabani_al

router = APIRouter(prefix="/bilgi-tabani", tags=["BilgiTabani"])
sablonlar = Jinja2Templates(directory="app/templates")


def _kayit_sorgusu(vt: Session, kullanici_id: int):
    return vt.query(BilgiTabaniKaydi).filter(BilgiTabaniKaydi.kullanici_id == kullanici_id)


def _kayit_getir(vt: Session, kullanici_id: int, kayit_id: int):
    return _kayit_sorgusu(vt, kullanici_id).filter(BilgiTabaniKaydi.id == kayit_id).first()


def _calisma_alani_getir(vt: Session, kullanici_id: int, calisma_alani_id: int | None):
    if not calisma_alani_id:
        return None
    return (
        vt.query(CalismaAlani)
        .filter(CalismaAlani.id == calisma_alani_id, CalismaAlani.sahip_id == kullanici_id, CalismaAlani.aktif_mi == True)
        .first()
    )


def _oturum_getir(vt: Session, kullanici_id: int, oturum_id: int | None):
    if not oturum_id:
        return None
    return vt.query(HataOturumu).filter(HataOturumu.id == oturum_id, HataOturumu.olusturan_id == kullanici_id).first()


@router.get("/", response_class=HTMLResponse)
async def bilgi_tabani_sayfasi(
    request: Request,
    q: str = "",
    workspace: int | None = None,
    durum: str = "",
    kategori: str = "",
    duzenle: int | None = None,
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")

    sorgu = _kayit_sorgusu(vt, kullanici.id)
    if workspace:
        sorgu = sorgu.filter(BilgiTabaniKaydi.calisma_alani_id == workspace)
    if durum:
        sorgu = sorgu.filter(BilgiTabaniKaydi.durum == durum)
    if kategori:
        sorgu = sorgu.filter(BilgiTabaniKaydi.kategori == kategori)
    if q:
        ifade = f"%{q.strip()}%"
        sorgu = sorgu.filter(
            or_(
                BilgiTabaniKaydi.baslik.ilike(ifade),
                BilgiTabaniKaydi.ozet.ilike(ifade),
                BilgiTabaniKaydi.icerik.ilike(ifade),
                BilgiTabaniKaydi.etiketler_metin.ilike(ifade),
            )
        )

    kayitlar = sorgu.order_by(BilgiTabaniKaydi.guncellenme_tarihi.desc(), BilgiTabaniKaydi.olusturulma_tarihi.desc()).all()
    duzenlenen_kayit = _kayit_getir(vt, kullanici.id, duzenle) if duzenle else None
    tum_kayitlar = _kayit_sorgusu(vt, kullanici.id).all()
    kategoriler = sorted({kayit.kategori for kayit in tum_kayitlar if kayit.kategori})
    bagli_oturumlar = (
        vt.query(HataOturumu)
        .filter(HataOturumu.olusturan_id == kullanici.id)
        .order_by(HataOturumu.olusturulma_tarihi.desc())
        .limit(50)
        .all()
    )
    return sablonlar.TemplateResponse(
        request=request,
        name="knowledge/index.html",
        context={
            "kullanici": kullanici,
            "kayitlar": kayitlar,
            "duzenlenen_kayit": duzenlenen_kayit,
            "calisma_alanlari": kullanici_calisma_alanlarini_getir(vt, kullanici.id),
            "aktif_calisma_alani": kullanici_aktif_calisma_alani(vt, kullanici.id),
            "bagli_oturumlar": bagli_oturumlar,
            "kategoriler": kategoriler,
            "filtreler": {"q": q, "workspace": workspace, "durum": durum, "kategori": kategori},
            "mesaj": request.query_params.get("mesaj", ""),
            "hata": request.query_params.get("hata", ""),
        },
    )


@router.post("/")
async def bilgi_tabani_ekle(
    request: Request,
    baslik: str = Form(...),
    kategori: str = Form(""),
    etiketler: str = Form(""),
    ozet: str = Form(""),
    icerik: str = Form(...),
    durum: str = Form("taslak"),
    calisma_alani_id: int | None = Form(None),
    kaynak_oturum_id: int | None = Form(None),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")

    calisma_alani = _calisma_alani_getir(vt, kullanici.id, calisma_alani_id)
    if calisma_alani_id and not calisma_alani:
        return RedirectResponse(url=f"/bilgi-tabani?hata={quote('Çalışma alanı bulunamadı.')}", status_code=302)
    kaynak_oturum = _oturum_getir(vt, kullanici.id, kaynak_oturum_id)
    if kaynak_oturum_id and not kaynak_oturum:
        return RedirectResponse(url=f"/bilgi-tabani?hata={quote('Bağlı oturum bulunamadı.')}", status_code=302)

    kayit = BilgiTabaniKaydi(
        kullanici_id=kullanici.id,
        calisma_alani_id=calisma_alani.id if calisma_alani else None,
        kaynak_oturum_id=kaynak_oturum.id if kaynak_oturum else None,
        baslik=baslik.strip(),
        kategori=kategori.strip() or None,
        etiketler_metin=etiketleri_normallestir(etiketler),
        ozet=ozet.strip() or None,
        icerik=icerik.strip(),
        durum=durum,
        olusturulma_tarihi=datetime.utcnow(),
        guncellenme_tarihi=datetime.utcnow(),
    )
    vt.add(kayit)
    vt.commit()
    return RedirectResponse(url=f"/bilgi-tabani?mesaj={quote('Bilgi tabanı kaydı eklendi.')}", status_code=302)


@router.post("/{kayit_id}/guncelle")
async def bilgi_tabani_guncelle(
    request: Request,
    kayit_id: int,
    baslik: str = Form(...),
    kategori: str = Form(""),
    etiketler: str = Form(""),
    ozet: str = Form(""),
    icerik: str = Form(...),
    durum: str = Form("taslak"),
    calisma_alani_id: int | None = Form(None),
    kaynak_oturum_id: int | None = Form(None),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")

    kayit = _kayit_getir(vt, kullanici.id, kayit_id)
    if not kayit:
        return RedirectResponse(url=f"/bilgi-tabani?hata={quote('Kayıt bulunamadı.')}", status_code=302)

    calisma_alani = _calisma_alani_getir(vt, kullanici.id, calisma_alani_id)
    if calisma_alani_id and not calisma_alani:
        return RedirectResponse(url=f"/bilgi-tabani?duzenle={kayit_id}&hata={quote('Çalışma alanı bulunamadı.')}", status_code=302)
    kaynak_oturum = _oturum_getir(vt, kullanici.id, kaynak_oturum_id)
    if kaynak_oturum_id and not kaynak_oturum:
        return RedirectResponse(url=f"/bilgi-tabani?duzenle={kayit_id}&hata={quote('Bağlı oturum bulunamadı.')}", status_code=302)

    kayit.baslik = baslik.strip()
    kayit.kategori = kategori.strip() or None
    kayit.etiketler_metin = etiketleri_normallestir(etiketler)
    kayit.ozet = ozet.strip() or None
    kayit.icerik = icerik.strip()
    kayit.durum = durum
    kayit.calisma_alani_id = calisma_alani.id if calisma_alani else None
    kayit.kaynak_oturum_id = kaynak_oturum.id if kaynak_oturum else None
    kayit.guncellenme_tarihi = datetime.utcnow()
    vt.commit()
    return RedirectResponse(url=f"/bilgi-tabani?mesaj={quote('Bilgi tabanı kaydı güncellendi.')}", status_code=302)


@router.post("/{kayit_id}/sil")
async def bilgi_tabani_sil(request: Request, kayit_id: int, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")

    kayit = _kayit_getir(vt, kullanici.id, kayit_id)
    if not kayit:
        return RedirectResponse(url=f"/bilgi-tabani?hata={quote('Kayıt bulunamadı.')}", status_code=302)

    vt.delete(kayit)
    vt.commit()
    return RedirectResponse(url=f"/bilgi-tabani?mesaj={quote('Bilgi tabanı kaydı silindi.')}", status_code=302)
