from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.base import Kullanici, YapayZekaSaglayicisi
from app.routers.pano import mevcut_kullanici
from app.services.ai_servisi import (
    SAGLAYICI_TIPLERI,
    kullanici_ayarini_getir_veya_olustur,
    okunur_hata_mesaji,
    saglayici_kaydet_veya_guncelle,
    saglayici_modellerini_oku,
    saglayici_modellerini_yenile,
    saglayici_secimlerini_hazirla,
)
from app.services.oturum_servisi import (
    aylik_maliyet_ozeti,
    kullanici_aktif_calisma_alani,
    kullanici_calisma_alanlarini_getir,
    saglayici_saglik_ozetleri,
    workspace_olustur,
    workspace_sec,
)
from core.database import veritabani_al
from core.security import sifre_dogrula, sifre_hashle

router = APIRouter(prefix="/ayarlar", tags=["Ayarlar"])
sablonlar = Jinja2Templates(directory="app/templates")


def ayarlara_yonlendir(mesaj: str = "", hata: str = "", duzenle: str = ""):
    parametreler = {}
    if mesaj:
        parametreler["mesaj"] = mesaj
    if hata:
        parametreler["hata"] = hata
    if duzenle:
        parametreler["duzenle"] = duzenle
    sorgu = urlencode(parametreler)
    hedef = "/ayarlar"
    if sorgu:
        hedef = f"{hedef}?{sorgu}"
    return RedirectResponse(url=hedef, status_code=302)



def ayarlar_sayfasi_baglamini_hazirla(request: Request, vt: Session, kullanici: Kullanici):
    secimler = saglayici_secimlerini_hazirla(vt, kullanici.id)
    duzenle_id = request.query_params.get("duzenle", "")
    duzenlenen_saglayici = None
    if duzenle_id.isdigit():
        duzenlenen_saglayici = next((s for s in secimler["saglayicilar"] if s.id == int(duzenle_id)), None)
    return {
        "request": request,
        "kullanici": kullanici,
        "ayar": secimler["ayar"],
        "saglayicilar": secimler["saglayicilar"],
        "aktif_saglayici": secimler["aktif_saglayici"],
        "aktif_model_listesi": secimler["aktif_model_listesi"],
        "saglayici_tipleri": secimler["saglayici_tipleri"],
        "saglayici_model_haritasi": {s.id: saglayici_modellerini_oku(s) for s in secimler["saglayicilar"]},
        "saglayici_sagliklari": saglayici_saglik_ozetleri(vt, kullanici.id),
        "maliyet_ozeti": aylik_maliyet_ozeti(vt, kullanici.id),
        "calisma_alanlari": kullanici_calisma_alanlarini_getir(vt, kullanici.id),
        "aktif_calisma_alani": kullanici_aktif_calisma_alani(vt, kullanici.id),
        "duzenlenen_saglayici": duzenlenen_saglayici,
        "duzenlenen_modeller": saglayici_modellerini_oku(duzenlenen_saglayici) if duzenlenen_saglayici else [],
        "mesaj": request.query_params.get("mesaj", ""),
        "hata": request.query_params.get("hata", ""),
    }


@router.get("/", response_class=HTMLResponse)
async def ayarlar_sayfasi(request: Request, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    baglam = ayarlar_sayfasi_baglamini_hazirla(request, vt, kullanici)
    return sablonlar.TemplateResponse(request=request, name="settings/index.html", context=baglam)


@router.post("/profil")
async def profil_guncelle(
    request: Request,
    ad_soyad: str = Form(...),
    eposta: str = Form(...),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    cakisan = vt.query(Kullanici).filter(Kullanici.eposta == eposta.strip(), Kullanici.id != kullanici.id).first()
    if cakisan:
        return ayarlara_yonlendir(hata="Bu e-posta adresi baska bir hesapta kullanimda.")
    kullanici.ad_soyad = ad_soyad.strip()
    kullanici.eposta = eposta.strip()
    vt.commit()
    return ayarlara_yonlendir(mesaj="Profil bilgileri guncellendi.")


@router.post("/sifre")
async def sifre_guncelle(
    request: Request,
    mevcut_sifre: str = Form(...),
    yeni_sifre: str = Form(...),
    yeni_sifre_tekrar: str = Form(...),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    if not sifre_dogrula(mevcut_sifre, kullanici.sifre_hash):
        return ayarlara_yonlendir(hata="Mevcut sifre dogrulanamadi.")
    if len(yeni_sifre) < 8:
        return ayarlara_yonlendir(hata="Yeni sifre en az 8 karakter olmalidir.")
    if yeni_sifre != yeni_sifre_tekrar:
        return ayarlara_yonlendir(hata="Yeni sifre tekrar alani eslesmiyor.")
    kullanici.sifre_hash = sifre_hashle(yeni_sifre)
    vt.commit()
    return ayarlara_yonlendir(mesaj="Sifre basariyla guncellendi.")


@router.post("/saglayicilar")
async def saglayici_ekle(
    request: Request,
    saglayici_tipi: str = Form(...),
    gosterim_adi: str = Form(...),
    api_key: str = Form(...),
    base_url: str = Form(""),
    varsayilan_model: str = Form(""),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    try:
        saglayici = saglayici_kaydet_veya_guncelle(vt, kullanici, None, saglayici_tipi, gosterim_adi, api_key, base_url, varsayilan_model)
        sonuc = saglayici_modellerini_yenile(vt, saglayici)
        return ayarlara_yonlendir(mesaj=f"Saglayici eklendi. {sonuc['mesaj']}")
    except Exception as hata:
        return ayarlara_yonlendir(hata=okunur_hata_mesaji(hata))


@router.post("/saglayicilar/{saglayici_id}/guncelle")
async def saglayici_guncelle(
    request: Request,
    saglayici_id: int,
    saglayici_tipi: str = Form(...),
    gosterim_adi: str = Form(...),
    api_key: str = Form(""),
    base_url: str = Form(""),
    varsayilan_model: str = Form(""),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    saglayici = vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.id == saglayici_id, YapayZekaSaglayicisi.kullanici_id == kullanici.id).first()
    if not saglayici:
        return ayarlara_yonlendir(hata="Saglayici kaydi bulunamadi.")
    try:
        saglayici = saglayici_kaydet_veya_guncelle(vt, kullanici, saglayici, saglayici_tipi, gosterim_adi, api_key, base_url, varsayilan_model)
        sonuc = saglayici_modellerini_yenile(vt, saglayici)
        return ayarlara_yonlendir(mesaj=f"Saglayici guncellendi. {sonuc['mesaj']}")
    except Exception as hata:
        return ayarlara_yonlendir(hata=okunur_hata_mesaji(hata), duzenle=str(saglayici_id))


@router.post("/saglayicilar/{saglayici_id}/test")
async def saglayici_test_et(request: Request, saglayici_id: int, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    saglayici = vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.id == saglayici_id, YapayZekaSaglayicisi.kullanici_id == kullanici.id).first()
    if not saglayici:
        return ayarlara_yonlendir(hata="Saglayici kaydi bulunamadi.")
    try:
        sonuc = saglayici_modellerini_yenile(vt, saglayici)
        return ayarlara_yonlendir(mesaj=sonuc["mesaj"], duzenle=str(saglayici_id))
    except Exception as hata:
        return ayarlara_yonlendir(hata=okunur_hata_mesaji(hata), duzenle=str(saglayici_id))


@router.post("/saglayicilar/{saglayici_id}/modelleri-yenile")
async def saglayici_modellerini_elle_yenile(request: Request, saglayici_id: int, vt: Session = Depends(veritabani_al)):
    return await saglayici_test_et(request, saglayici_id, vt)


@router.post("/saglayicilar/{saglayici_id}/sil")
async def saglayici_sil(request: Request, saglayici_id: int, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    saglayici = vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.id == saglayici_id, YapayZekaSaglayicisi.kullanici_id == kullanici.id).first()
    if not saglayici:
        return ayarlara_yonlendir(hata="Saglayici kaydi bulunamadi.")
    ayar = kullanici_ayarini_getir_veya_olustur(vt, kullanici.id)
    if ayar.secili_saglayici_id == saglayici.id:
        ayar.secili_saglayici_id = None
        ayar.secili_model = None
    vt.delete(saglayici)
    vt.commit()
    return ayarlara_yonlendir(mesaj="Saglayici silindi.")


@router.post("/tercihler")
async def tercihleri_guncelle(
    request: Request,
    secili_saglayici_id: int = Form(...),
    secili_model: str = Form(""),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    saglayici = vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.id == secili_saglayici_id, YapayZekaSaglayicisi.kullanici_id == kullanici.id).first()
    if not saglayici:
        return ayarlara_yonlendir(hata="Secilen saglayici kaydi bulunamadi.")
    if not saglayici.son_test_basarili:
        return ayarlara_yonlendir(hata="Secilen saglayici once basariyla test edilmelidir.")
    ayar = kullanici_ayarini_getir_veya_olustur(vt, kullanici.id)
    ayar.secili_saglayici_id = saglayici.id
    secili_model_degeri = secili_model.strip() or saglayici.varsayilan_model
    if secili_model_degeri:
        mevcut_modeller = saglayici_modellerini_oku(saglayici)
        if mevcut_modeller and secili_model_degeri not in mevcut_modeller:
            return ayarlara_yonlendir(hata="Secilen model bu saglayici icin gecerli degil.")
        ayar.secili_model = secili_model_degeri
    else:
        ayar.secili_model = None
    vt.commit()
    return ayarlara_yonlendir(mesaj="Varsayilan AI profili guncellendi.")


@router.post("/workspaces")
async def workspace_ekle(
    request: Request,
    isim: str = Form(...),
    aciklama: str = Form(""),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    if not isim.strip():
        return ayarlara_yonlendir(hata="Çalışma alanı adı zorunludur.")
    alan = workspace_olustur(vt, kullanici.id, isim, aciklama)
    workspace_sec(vt, kullanici.id, alan.id)
    return ayarlara_yonlendir(mesaj="Yeni çalışma alanı oluşturuldu ve aktif hale getirildi.")


@router.post("/workspaces/sec")
async def workspace_secimi(
    request: Request,
    calisma_alani_id: int = Form(...),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    workspace_sec(vt, kullanici.id, calisma_alani_id)
    return ayarlara_yonlendir(mesaj="Aktif çalışma alanı güncellendi.")
