import json
import re
from pathlib import Path
from typing import Iterable, List, Tuple
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.base import CalismaAlani, HataOturumDosyasi, HataOturumu, HataRaporu, KullaniciAyari, YapayZekaIstegi, YapayZekaSaglayicisi

DESTEKLENEN_DOSYA_UZANTILARI = {".log", ".txt", ".json", ".py", ".php"}
DOSYA_KAYIT_DIZINI = Path("app_data/uploads")


def kullanici_aktif_calisma_alani(vt: Session, kullanici_id: int) -> CalismaAlani | None:
    ayar = vt.query(KullaniciAyari).filter(KullaniciAyari.kullanici_id == kullanici_id).first()
    if ayar and ayar.aktif_calisma_alani_id:
        alan = vt.query(CalismaAlani).filter(CalismaAlani.id == ayar.aktif_calisma_alani_id, CalismaAlani.sahip_id == kullanici_id).first()
        if alan:
            return alan
    return vt.query(CalismaAlani).filter(CalismaAlani.sahip_id == kullanici_id, CalismaAlani.aktif_mi == True).order_by(CalismaAlani.id.asc()).first()


def kullanici_calisma_alanlarini_getir(vt: Session, kullanici_id: int) -> List[CalismaAlani]:
    return vt.query(CalismaAlani).filter(CalismaAlani.sahip_id == kullanici_id, CalismaAlani.aktif_mi == True).order_by(CalismaAlani.olusturulma_tarihi.asc()).all()


def workspace_olustur(vt: Session, kullanici_id: int, isim: str, aciklama: str) -> CalismaAlani:
    alan = CalismaAlani(isim=isim.strip(), aciklama=aciklama.strip() or None, sahip_id=kullanici_id, aktif_mi=True)
    vt.add(alan)
    vt.commit()
    vt.refresh(alan)
    ayar = vt.query(KullaniciAyari).filter(KullaniciAyari.kullanici_id == kullanici_id).first()
    if ayar and not ayar.aktif_calisma_alani_id:
        ayar.aktif_calisma_alani_id = alan.id
        vt.commit()
    return alan


def workspace_sec(vt: Session, kullanici_id: int, calisma_alani_id: int):
    ayar = vt.query(KullaniciAyari).filter(KullaniciAyari.kullanici_id == kullanici_id).first()
    alan = vt.query(CalismaAlani).filter(CalismaAlani.id == calisma_alani_id, CalismaAlani.sahip_id == kullanici_id, CalismaAlani.aktif_mi == True).first()
    if ayar and alan:
        ayar.aktif_calisma_alani_id = alan.id
        vt.commit()


def etiketleri_normallestir(etiketler: str) -> str:
    parcalar = [parca.strip().lower() for parca in (etiketler or "").replace(";", ",").split(",")]
    temiz = [parca for parca in parcalar if parca]
    return ",".join(dict.fromkeys(temiz))


def metni_tokenlestir(metin: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9_]{3,}", (metin or "").lower()))


def benzerlik_skoru_hesapla(kaynak: str, hedef: str) -> float:
    kaynak_kume = metni_tokenlestir(kaynak)
    hedef_kume = metni_tokenlestir(hedef)
    if not kaynak_kume or not hedef_kume:
        return 0.0
    kesisim = kaynak_kume & hedef_kume
    birlesim = kaynak_kume | hedef_kume
    return round(len(kesisim) / len(birlesim), 4) if birlesim else 0.0


def benzer_oturumlari_bul(vt: Session, kullanici_id: int, calisma_alani_id: int, baglam: str, haric_oturum_id: int | None = None, limit: int = 5) -> List[Tuple[HataOturumu, float]]:
    sorgu = (
        vt.query(HataOturumu)
        .filter(HataOturumu.olusturan_id == kullanici_id, HataOturumu.calisma_alani_id == calisma_alani_id)
        .order_by(HataOturumu.olusturulma_tarihi.desc())
    )
    if haric_oturum_id:
        sorgu = sorgu.filter(HataOturumu.id != haric_oturum_id)
    adaylar = sorgu.limit(40).all()
    skorlar = []
    for aday in adaylar:
        aday_metin = "\n".join([aday.baslik or "", aday.kod_parcasi or "", aday.hata_logu or "", aday.yigin_izleme or "", aday.ek_notlar or "", aday.baglam_ozeti or ""])
        skor = benzerlik_skoru_hesapla(baglam, aday_metin)
        if skor > 0:
            skorlar.append((aday, skor))
    skorlar.sort(key=lambda oge: oge[1], reverse=True)
    return skorlar[:limit]


def ilgili_cozumleri_getir(vt: Session, kullanici_id: int, calisma_alani_id: int, baglam: str, haric_oturum_id: int | None = None, limit: int = 3) -> List[Tuple[HataOturumu, float]]:
    skorlar = benzer_oturumlari_bul(vt, kullanici_id, calisma_alani_id, baglam, haric_oturum_id=haric_oturum_id, limit=12)
    return [(oturum, skor) for oturum, skor in skorlar if oturum.rapor][:limit]


def dosya_yuklemelerini_kaydet(oturum_id: int, dosyalar: Iterable[UploadFile]) -> List[dict]:
    kayitlar = []
    hedef_klasor = DOSYA_KAYIT_DIZINI / str(oturum_id)
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    for dosya in dosyalar:
        if not dosya or not dosya.filename:
            continue
        uzanti = Path(dosya.filename).suffix.lower()
        if uzanti not in DESTEKLENEN_DOSYA_UZANTILARI:
            continue
        icerik = dosya.file.read()
        metin = icerik.decode("utf-8", errors="ignore")
        yeni_ad = f"{uuid4().hex}{uzanti}"
        hedef_yol = hedef_klasor / yeni_ad
        hedef_yol.write_bytes(icerik)
        kayitlar.append(
            {
                "dosya_adi": yeni_ad,
                "orijinal_ad": dosya.filename,
                "icerik_tipi": dosya.content_type,
                "boyut": len(icerik),
                "kayit_yolu": str(hedef_yol).replace("\\", "/"),
                "metin_icerigi": metin[:50000],
            }
        )
    return kayitlar


def dosya_kayitlarini_olustur(vt: Session, oturum: HataOturumu, dosya_kayitlari: list[dict]):
    for kayit in dosya_kayitlari:
        vt.add(HataOturumDosyasi(oturum_id=oturum.id, **kayit))
    vt.commit()


def dosya_baglamini_uret(dosya_kayitlari: list[dict]) -> str:
    bloklar = []
    for kayit in dosya_kayitlari:
        bloklar.append(f"Dosya: {kayit['orijinal_ad']}\nIcerik:\n{kayit['metin_icerigi']}")
    return "\n\n".join(bloklar)


def tahmini_token_hesapla(metin: str) -> int:
    return max(1, len((metin or "").encode("utf-8")) // 4)


def aylik_maliyet_ozeti(vt: Session, kullanici_id: int) -> dict:
    toplam = 0.0
    sorgu = (
        vt.query(YapayZekaIstegi)
        .join(HataOturumu, HataOturumu.id == YapayZekaIstegi.oturum_id)
        .filter(HataOturumu.olusturan_id == kullanici_id)
        .all()
    )
    for kayit in sorgu:
        toplam += kayit.tahmini_maliyet or 0
    return {"aylik_maliyet": round(toplam, 4), "istek_sayisi": len(sorgu)}


def saglayici_saglik_ozetleri(vt: Session, kullanici_id: int) -> dict[int, dict]:
    saglayicilar = vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.kullanici_id == kullanici_id).all()
    sonuc = {}
    for saglayici in saglayicilar:
        istekler = (
            vt.query(YapayZekaIstegi)
            .join(HataOturumu, HataOturumu.id == YapayZekaIstegi.oturum_id)
            .filter(HataOturumu.olusturan_id == kullanici_id, YapayZekaIstegi.saglayici == saglayici.gosterim_adi)
            .all()
        )
        toplam = len(istekler)
        basarili = len([istek for istek in istekler if istek.basarili])
        ort_gecikme = int(sum(istek.gecikme_ms or 0 for istek in istekler) / toplam) if toplam else saglayici.son_gecikme_ms or 0
        aylik_maliyet = round(sum(istek.tahmini_maliyet or 0 for istek in istekler), 4)
        sonuc[saglayici.id] = {
            "basari_orani": round((basarili / toplam) * 100, 1) if toplam else round((saglayici.son_basari_orani or 0) * 100, 1),
            "ortalama_gecikme": ort_gecikme,
            "istek_sayisi": toplam,
            "aylik_maliyet": aylik_maliyet,
            "son_kullanim": saglayici.son_kullanim_tarihi,
        }
    return sonuc


def oturum_arama_sorgusu(vt: Session, kullanici_id: int, calisma_alani_id: int | None, arama: str):
    sorgu = vt.query(HataOturumu).outerjoin(HataRaporu, HataRaporu.oturum_id == HataOturumu.id).filter(HataOturumu.olusturan_id == kullanici_id)
    if calisma_alani_id:
        sorgu = sorgu.filter(HataOturumu.calisma_alani_id == calisma_alani_id)
    if arama:
        ifade = f"%{arama.strip()}%"
        sorgu = sorgu.filter(
            or_(
                HataOturumu.baslik.ilike(ifade),
                HataOturumu.kod_parcasi.ilike(ifade),
                HataOturumu.hata_logu.ilike(ifade),
                HataOturumu.yigin_izleme.ilike(ifade),
                HataOturumu.ek_notlar.ilike(ifade),
                HataOturumu.etiketler_metin.ilike(ifade),
                HataRaporu.kok_neden.ilike(ifade),
                HataRaporu.cozum_onerileri.ilike(ifade),
            )
        )
    return sorgu


def oturum_etiketleri_listesi(oturum: HataOturumu) -> List[str]:
    return [etiket for etiket in (oturum.etiketler_metin or "").split(",") if etiket]


def rapor_onerilerini_json(oneriler: List[Tuple[HataOturumu, float]]) -> str:
    veri = [
        {
            "id": oturum.id,
            "baslik": oturum.baslik,
            "skor": skor,
            "cozum": oturum.rapor.cozum_onerileri if oturum.rapor else "",
        }
        for oturum, skor in oneriler
    ]
    return json.dumps(veri, ensure_ascii=False)
