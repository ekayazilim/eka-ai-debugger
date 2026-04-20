from datetime import datetime, time
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.base import CalismaAlani, HataOturumu, HataRaporu, YapayZekaIstegi
from app.routers.pano import mevcut_kullanici
from app.services.ai_servisi import AnalizIcinSaglayiciEksikHatasi, DesteklenmeyenModelHatasi, analiz_baslat, analiz_icin_saglayiciyi_getir
from app.services.oturum_servisi import (
    benzer_oturumlari_bul,
    dosya_baglamini_uret,
    dosya_kayitlarini_olustur,
    dosya_yuklemelerini_kaydet,
    etiketleri_normallestir,
    ilgili_cozumleri_getir,
    kullanici_aktif_calisma_alani,
    kullanici_calisma_alanlarini_getir,
    oturum_arama_sorgusu,
    oturum_etiketleri_listesi,
    tahmini_token_hesapla,
)
from core.database import veritabani_al

router = APIRouter(prefix="/oturumlar", tags=["Oturumlar"])
sablonlar = Jinja2Templates(directory="app/templates")


def _secili_calisma_alani(vt: Session, kullanici_id: int, calisma_alani_id: int | None) -> CalismaAlani | None:
    if calisma_alani_id:
        return (
            vt.query(CalismaAlani)
            .filter(CalismaAlani.id == calisma_alani_id, CalismaAlani.sahip_id == kullanici_id, CalismaAlani.aktif_mi == True)
            .first()
        )
    return kullanici_aktif_calisma_alani(vt, kullanici_id)


def _yukleme_onizlemleri(dosyalar: list[UploadFile]) -> list[dict]:
    onizlemeler = []
    for dosya in dosyalar:
        if not dosya or not dosya.filename:
            continue
        icerik = dosya.file.read()
        dosya.file.seek(0)
        onizlemeler.append({"orijinal_ad": dosya.filename, "metin_icerigi": icerik.decode("utf-8", errors="ignore")[:50000]})
    return onizlemeler


@router.get("/yeni", response_class=HTMLResponse)
async def yeni_oturum_sayfasi(request: Request, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    hata = request.query_params.get("hata", "")
    aktif_saglayici = None
    aktif_model = None
    try:
        _, aktif_saglayici, aktif_model = analiz_icin_saglayiciyi_getir(vt, kullanici.id)
    except Exception:
        pass
    aktif_calisma_alani = kullanici_aktif_calisma_alani(vt, kullanici.id)
    oneriler = []
    if aktif_calisma_alani:
        oneriler = ilgili_cozumleri_getir(vt, kullanici.id, aktif_calisma_alani.id, "kod hata stack trace çözüm")
    return sablonlar.TemplateResponse(
        request=request,
        name="sessions/create.html",
        context={
            "kullanici": kullanici,
            "hata": hata,
            "aktif_saglayici": aktif_saglayici,
            "aktif_model": aktif_model,
            "calisma_alanlari": kullanici_calisma_alanlarini_getir(vt, kullanici.id),
            "aktif_calisma_alani": aktif_calisma_alani,
            "onerilen_cozumler": oneriler,
        },
    )


@router.post("/yeni")
async def yeni_oturum_islem(
    request: Request,
    baslik: str = Form(...),
    programlama_dili: str = Form(...),
    kod_parcasi: str = Form(...),
    hata_logu: str = Form(""),
    yigin_izleme: str = Form(""),
    ek_notlar: str = Form(""),
    etiketler: str = Form(""),
    calisma_alani_id: int = Form(...),
    dosyalar: list[UploadFile] = File(default=[]),
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    try:
        _, aktif_saglayici, aktif_model = analiz_icin_saglayiciyi_getir(vt, kullanici.id)
    except (AnalizIcinSaglayiciEksikHatasi, DesteklenmeyenModelHatasi) as hata:
        return RedirectResponse(url=f"/oturumlar/yeni?hata={quote(str(hata))}", status_code=302)

    calisma_alani = _secili_calisma_alani(vt, kullanici.id, calisma_alani_id)
    if not calisma_alani:
        return RedirectResponse(url=f"/oturumlar/yeni?hata={quote('Çalışma alanı bulunamadı.')}", status_code=302)

    etiketler_metin = etiketleri_normallestir(etiketler)
    dosya_onizlemeleri = _yukleme_onizlemleri(dosyalar)
    dosya_baglami = dosya_baglamini_uret(dosya_onizlemeleri)
    tam_baglam = "\n".join([baslik, programlama_dili, kod_parcasi, hata_logu, yigin_izleme, ek_notlar, etiketler_metin, dosya_baglami])
    benzer_oturumlar = benzer_oturumlari_bul(vt, kullanici.id, calisma_alani.id, tam_baglam, limit=1)
    benzer_oturum = benzer_oturumlar[0][0] if benzer_oturumlar else None
    benzerlik_skoru = benzer_oturumlar[0][1] if benzer_oturumlar else None

    yeni_oturum = HataOturumu(
        calisma_alani_id=calisma_alani.id,
        olusturan_id=kullanici.id,
        benzer_oturum_id=benzer_oturum.id if benzer_oturum else None,
        baslik=baslik,
        programlama_dili=programlama_dili,
        kod_parcasi=kod_parcasi,
        hata_logu=hata_logu,
        yigin_izleme=yigin_izleme,
        ek_notlar=ek_notlar,
        etiketler_metin=etiketler_metin,
        secilen_saglayici=aktif_saglayici.gosterim_adi,
        secilen_model=aktif_model,
        baglam_ozeti=tam_baglam[:4000],
        benzerlik_skoru=benzerlik_skoru,
        tahmini_girdi_tokeni=tahmini_token_hesapla(tam_baglam),
        durum="bekliyor",
        olusturulma_tarihi=datetime.utcnow(),
    )
    vt.add(yeni_oturum)
    vt.commit()
    vt.refresh(yeni_oturum)

    if dosya_onizlemeleri:
        gercek_kayitlar = dosya_yuklemelerini_kaydet(yeni_oturum.id, dosyalar)
        dosya_kayitlarini_olustur(vt, yeni_oturum, gercek_kayitlar)
        dosya_baglami = dosya_baglamini_uret(gercek_kayitlar)
    baglam = (
        f"Çalışma Alanı: {calisma_alani.isim}\n"
        f"Programlama Dili: {programlama_dili}\n"
        f"Aktif Sağlayıcı: {aktif_saglayici.gosterim_adi}\n"
        f"Aktif Model: {aktif_model}\n"
        f"Etiketler: {etiketler_metin}\n"
        f"Kod:\n{kod_parcasi}\n"
        f"Hata Logu:\n{hata_logu}\n"
        f"Yığın İzleme:\n{yigin_izleme}\n"
        f"Notlar:\n{ek_notlar}\n"
        f"Dosya Bağlamı:\n{dosya_baglami}"
    )
    try:
        analiz_baslat(vt, yeni_oturum, baglam, kullanici.id)
    except Exception:
        return RedirectResponse(url=f"/oturumlar/detay/{yeni_oturum.id}", status_code=302)
    return RedirectResponse(url=f"/oturumlar/detay/{yeni_oturum.id}", status_code=302)


@router.get("/", response_class=HTMLResponse)
async def oturumlar_sayfasi(
    request: Request,
    q: str = "",
    dil: str = "",
    durum: str = "",
    saglayici: str = "",
    model: str = "",
    workspace: int | None = None,
    etiket: str = "",
    tarih_baslangic: str = "",
    tarih_bitis: str = "",
    vt: Session = Depends(veritabani_al),
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    sorgu = oturum_arama_sorgusu(vt, kullanici.id, workspace, q)
    if dil:
        sorgu = sorgu.filter(HataOturumu.programlama_dili == dil)
    if durum:
        sorgu = sorgu.filter(HataOturumu.durum == durum)
    if saglayici:
        sorgu = sorgu.filter(HataOturumu.secilen_saglayici == saglayici)
    if model:
        sorgu = sorgu.filter(HataOturumu.secilen_model == model)
    if etiket:
        sorgu = sorgu.filter(HataOturumu.etiketler_metin.ilike(f"%{etiket.lower()}%"))
    if tarih_baslangic:
        try:
            sorgu = sorgu.filter(HataOturumu.olusturulma_tarihi >= datetime.strptime(tarih_baslangic, "%Y-%m-%d"))
        except ValueError:
            tarih_baslangic = ""
    if tarih_bitis:
        try:
            bitis = datetime.combine(datetime.strptime(tarih_bitis, "%Y-%m-%d").date(), time.max)
            sorgu = sorgu.filter(HataOturumu.olusturulma_tarihi <= bitis)
        except ValueError:
            tarih_bitis = ""
    oturumlar = sorgu.order_by(HataOturumu.olusturulma_tarihi.desc()).all()
    tum_oturumlar = vt.query(HataOturumu).filter(HataOturumu.olusturan_id == kullanici.id).all()
    saglayicilar = sorted({oturum.secilen_saglayici for oturum in tum_oturumlar if oturum.secilen_saglayici})
    modeller = sorted({oturum.secilen_model for oturum in tum_oturumlar if oturum.secilen_model})
    diller = sorted({oturum.programlama_dili for oturum in tum_oturumlar if oturum.programlama_dili})
    return sablonlar.TemplateResponse(
        request=request,
        name="sessions/list.html",
        context={
            "kullanici": kullanici,
            "oturumlar": oturumlar,
            "calisma_alanlari": kullanici_calisma_alanlarini_getir(vt, kullanici.id),
            "filtreler": {
                "q": q,
                "dil": dil,
                "durum": durum,
                "saglayici": saglayici,
                "model": model,
                "workspace": workspace,
                "etiket": etiket,
                "tarih_baslangic": tarih_baslangic,
                "tarih_bitis": tarih_bitis,
            },
            "saglayicilar": saglayicilar,
            "modeller": modeller,
            "diller": diller,
        },
    )


@router.get("/detay/{oturum_id}", response_class=HTMLResponse)
async def oturum_detay(request: Request, oturum_id: int, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    oturum = vt.query(HataOturumu).filter(HataOturumu.id == oturum_id, HataOturumu.olusturan_id == kullanici.id).first()
    rapor = vt.query(HataRaporu).filter(HataRaporu.oturum_id == oturum.id).first() if oturum else None
    son_istek = vt.query(YapayZekaIstegi).filter(YapayZekaIstegi.oturum_id == oturum.id).order_by(YapayZekaIstegi.id.desc()).first() if oturum else None
    benzer_oturumlar = ilgili_cozumleri_getir(vt, kullanici.id, oturum.calisma_alani_id, oturum.baglam_ozeti or "", haric_oturum_id=oturum.id) if oturum else []
    return sablonlar.TemplateResponse(
        request=request,
        name="sessions/detail.html",
        context={
            "kullanici": kullanici,
            "oturum": oturum,
            "rapor": rapor,
            "son_istek": son_istek,
            "benzer_oturumlar": benzer_oturumlar,
            "etiketler": oturum_etiketleri_listesi(oturum) if oturum else [],
        },
    )
