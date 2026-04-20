import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from anthropic import Anthropic
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.base import HataRaporu, HataOturumu, Kullanici, KullaniciAyari, YapayZekaIstegi, YapayZekaSaglayicisi
from app.services.oturum_servisi import tahmini_token_hesapla
from core.security import anahtar_maskele, metni_coz, metni_sifrele

SAGLAYICI_TIPLERI = {
    "openai": {"etiket": "OpenAI", "varsayilan_base_url": "https://api.openai.com/v1", "base_url_zorunlu": False},
    "anthropic": {"etiket": "Anthropic", "varsayilan_base_url": "https://api.anthropic.com", "base_url_zorunlu": False},
    "openrouter": {"etiket": "OpenRouter", "varsayilan_base_url": "https://openrouter.ai/api/v1", "base_url_zorunlu": False},
    "nvidia": {"etiket": "NVIDIA Build", "varsayilan_base_url": "https://integrate.api.nvidia.com/v1", "base_url_zorunlu": False},
    "huggingface": {"etiket": "Hugging Face Router", "varsayilan_base_url": "https://router.huggingface.co/v1", "base_url_zorunlu": False},
    "cloudflare": {"etiket": "Cloudflare AI", "varsayilan_base_url": "", "base_url_zorunlu": True},
    "custom_openai": {"etiket": "OpenAI Uyumlu", "varsayilan_base_url": "http://localhost:1234/v1", "base_url_zorunlu": True},
    "lmstudio": {"etiket": "LM Studio", "varsayilan_base_url": "http://localhost:1234/v1", "base_url_zorunlu": True},
    "ollama": {"etiket": "Ollama", "varsayilan_base_url": "http://localhost:11434/v1", "base_url_zorunlu": True},
}

MODEL_FIYAT_CARPANLARI = {
    "openai": (0.0000025, 0.00001),
    "anthropic": (0.000003, 0.000015),
    "openrouter": (0.000002, 0.000008),
    "nvidia": (0.0000012, 0.0000045),
    "huggingface": (0.0000004, 0.000001),
    "cloudflare": (0.0000008, 0.0000025),
    "custom_openai": (0.0, 0.0),
    "lmstudio": (0.0, 0.0),
    "ollama": (0.0, 0.0),
}

ANALIZ_ENGELLI_MODEL_ANAHTARLARI = ["embed", "embedding", "image", "vision", "whisper", "tts", "speech", "transcribe", "moderation", "rerank", "flux", "stable-diffusion"]

JSON_SABLONU = {"kok_neden": "", "onem_derecesi": "", "etkilenen_katman": "", "cozum_onerileri": "", "iyilestirilmis_kod": "", "guvenlik_notlari": ""}

SISTEM_ISTEMI = (
    "Sen kıdemli bir yazılım mimarı ve hata ayıklama uzmansın. "
    "Sadece geçerli bir JSON nesnesi döndür. JSON anahtarları şunlar olmalı: "
    "kok_neden, onem_derecesi, etkilenen_katman, cozum_onerileri, iyilestirilmis_kod, guvenlik_notlari. "
    "onem_derecesi yalnızca Yuksek, Orta veya Dusuk olmalı."
)


class AIServisHatasi(Exception):
    pass


class AnalizIcinSaglayiciEksikHatasi(AIServisHatasi):
    pass


class DesteklenmeyenModelHatasi(AIServisHatasi):
    pass


class TemelSaglayiciAdaptoru:
    def __init__(self, kayit: YapayZekaSaglayicisi):
        self.kayit = kayit
        self.api_key = metni_coz(kayit.api_key_encrypted)
        self.base_url = self._base_url_hazirla()

    def _base_url_hazirla(self) -> str:
        tip = SAGLAYICI_TIPLERI[self.kayit.saglayici_tipi]
        return (self.kayit.base_url or tip["varsayilan_base_url"]).rstrip("/")

    def test_connection(self) -> Dict[str, Any]:
        baslangic = time.perf_counter()
        modeller = self.fetch_models()
        gecikme_ms = int((time.perf_counter() - baslangic) * 1000)
        mesaj = "Bağlantı doğrulandı."
        if modeller:
            mesaj = f"Bağlantı doğrulandı, {len(modeller)} model bulundu."
        return {"basarili": True, "mesaj": mesaj, "modeller": modeller, "gecikme_ms": gecikme_ms}

    def fetch_models(self) -> List[str]:
        raise NotImplementedError

    def analyze_debug_context(self, baglam: str, model: str) -> Dict[str, Any]:
        raise NotImplementedError


class OpenAIUyumluAdaptoru(TemelSaglayiciAdaptoru):
    def _istemci(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def fetch_models(self) -> List[str]:
        istemci = self._istemci()
        try:
            modeller = istemci.models.list()
            model_listesi = sorted({getattr(model, "id", "") for model in getattr(modeller, "data", []) if getattr(model, "id", "")})
            if model_listesi:
                return model_listesi
        except Exception:
            pass
        with httpx.Client(timeout=30.0) as istemci_http:
            yanit = istemci_http.get(f"{self.base_url}/models", headers={"Authorization": f"Bearer {self.api_key}"})
            yanit.raise_for_status()
            veri = yanit.json()
        if isinstance(veri, dict):
            if isinstance(veri.get("data"), list):
                return sorted({item.get("id", "") for item in veri["data"] if isinstance(item, dict) and item.get("id")})
            if isinstance(veri.get("models"), list):
                return sorted({item.get("id", "") if isinstance(item, dict) else str(item) for item in veri["models"] if item})
        raise AIServisHatasi("Model listesi alınamadı.")

    def analyze_debug_context(self, baglam: str, model: str) -> Dict[str, Any]:
        baslangic = time.perf_counter()
        try:
            yanit = self._istemci().chat.completions.create(model=model, messages=[{"role": "system", "content": SISTEM_ISTEMI}, {"role": "user", "content": baglam}], temperature=0.2)
        except Exception as hata:
            raise AIServisHatasi(str(hata)) from hata
        icerik = ""
        if getattr(yanit, "choices", None):
            mesaj = yanit.choices[0].message
            icerik = mesaj.content if isinstance(mesaj.content, str) else str(mesaj.content)
        sonuc = json_cevabini_normallestir(icerik)
        return {"sonuc": sonuc, "gecikme_ms": int((time.perf_counter() - baslangic) * 1000), "girdi_tokeni": tahmini_token_hesapla(baglam), "cikti_tokeni": tahmini_token_hesapla(icerik)}


class AnthropicAdaptoru(TemelSaglayiciAdaptoru):
    def _istemci(self) -> Anthropic:
        return Anthropic(api_key=self.api_key)

    def fetch_models(self) -> List[str]:
        try:
            modeller = self._istemci().models.list()
            veri = getattr(modeller, "data", None)
            if veri is None and hasattr(modeller, "__iter__"):
                veri = list(modeller)
            return sorted({getattr(model, "id", "") for model in veri or [] if getattr(model, "id", "")})
        except Exception as hata:
            raise AIServisHatasi(str(hata)) from hata

    def analyze_debug_context(self, baglam: str, model: str) -> Dict[str, Any]:
        baslangic = time.perf_counter()
        try:
            yanit = self._istemci().messages.create(model=model, max_tokens=1800, temperature=0.2, system=SISTEM_ISTEMI, messages=[{"role": "user", "content": baglam}])
        except Exception as hata:
            raise AIServisHatasi(str(hata)) from hata
        parcalar = []
        for parca in getattr(yanit, "content", []):
            if getattr(parca, "type", "") == "text":
                parcalar.append(getattr(parca, "text", ""))
        icerik = "\n".join(parcalar)
        sonuc = json_cevabini_normallestir(icerik)
        return {"sonuc": sonuc, "gecikme_ms": int((time.perf_counter() - baslangic) * 1000), "girdi_tokeni": tahmini_token_hesapla(baglam), "cikti_tokeni": tahmini_token_hesapla(icerik)}


class CloudflareAdaptoru(TemelSaglayiciAdaptoru):
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def fetch_models(self) -> List[str]:
        adaylar = [
            f"{self.base_url}/models/search", 
            f"{self.base_url}/models",
            f"{self.base_url.replace('/v1', '')}/models/search"
        ]
        son_hata = None
        with httpx.Client(timeout=30.0) as istemci_http:
            for url in adaylar:
                try:
                    yanit = istemci_http.get(url, headers=self._headers())
                    yanit.raise_for_status()
                    veri = yanit.json()
                    modeller = cloudflare_model_listesini_ayikla(veri)
                    if modeller:
                        return modeller
                except Exception as hata:
                    son_hata = hata
        if son_hata:
            raise AIServisHatasi(str(son_hata)) from son_hata
        raise AIServisHatasi("Cloudflare model listesi alınamadı.")

    def analyze_debug_context(self, baglam: str, model: str) -> Dict[str, Any]:
        govde = {"model": model, "messages": [{"role": "system", "content": SISTEM_ISTEMI}, {"role": "user", "content": baglam}], "temperature": 0.2}
        baslangic = time.perf_counter()
        try:
            with httpx.Client(timeout=60.0) as istemci_http:
                yanit = istemci_http.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=govde)
                yanit.raise_for_status()
                veri = yanit.json()
        except Exception as hata:
            raise AIServisHatasi(str(hata)) from hata
        icerik = ""
        if isinstance(veri, dict):
            kaynak = veri.get("result", veri)
            if isinstance(kaynak, dict) and isinstance(kaynak.get("response"), str):
                icerik = kaynak["response"]
            elif isinstance(kaynak, dict) and isinstance(kaynak.get("choices"), list) and kaynak["choices"]:
                mesaj = kaynak["choices"][0].get("message", {})
                icerik = mesaj.get("content", "")
        sonuc = json_cevabini_normallestir(icerik)
        return {"sonuc": sonuc, "gecikme_ms": int((time.perf_counter() - baslangic) * 1000), "girdi_tokeni": tahmini_token_hesapla(baglam), "cikti_tokeni": tahmini_token_hesapla(icerik)}


def cloudflare_model_listesini_ayikla(veri: Any) -> List[str]:
    sonuc = []
    kaynak = veri.get("result", veri) if isinstance(veri, dict) else veri
    if isinstance(kaynak, list):
        for oge in kaynak:
            if isinstance(oge, dict):
                model_adi = oge.get("name") or oge.get("id") or oge.get("model")
                if model_adi:
                    sonuc.append(model_adi)
    elif isinstance(kaynak, dict):
        for anahtar in ("models", "data"):
            if isinstance(kaynak.get(anahtar), list):
                for oge in kaynak[anahtar]:
                    if isinstance(oge, dict):
                        model_adi = oge.get("name") or oge.get("id") or oge.get("model")
                        if model_adi:
                            sonuc.append(model_adi)
    return sorted(set(sonuc))


def adaptoru_olustur(kayit: YapayZekaSaglayicisi) -> TemelSaglayiciAdaptoru:
    if kayit.saglayici_tipi == "anthropic":
        return AnthropicAdaptoru(kayit)
    if kayit.saglayici_tipi == "cloudflare":
        return CloudflareAdaptoru(kayit)
    if kayit.saglayici_tipi in {"openai", "openrouter", "nvidia", "huggingface", "custom_openai", "lmstudio", "ollama"}:
        return OpenAIUyumluAdaptoru(kayit)
    raise AIServisHatasi("Desteklenmeyen sağlayıcı tipi.")


def saglayici_formunu_dogrula(saglayici_tipi: str, gosterim_adi: str, api_key: str, base_url: str, api_key_zorunlu: bool = True) -> Tuple[str, str, str]:
    tip = SAGLAYICI_TIPLERI.get(saglayici_tipi)
    if not tip:
        raise AIServisHatasi("Geçersiz sağlayıcı tipi seçildi.")
    if not gosterim_adi.strip():
        raise AIServisHatasi("Sağlayıcı görünüm adı zorunludur.")
    if api_key_zorunlu and not api_key.strip():
        raise AIServisHatasi("API anahtarı zorunludur.")
    etkili_base_url = base_url.strip() or tip["varsayilan_base_url"]
    if tip["base_url_zorunlu"] and not etkili_base_url:
        raise AIServisHatasi("Bu sağlayıcı için base URL zorunludur.")
    return saglayici_tipi, gosterim_adi.strip(), etkili_base_url.rstrip("/")


def saglayici_kaydet_veya_guncelle(vt: Session, kullanici: Kullanici, saglayici: Optional[YapayZekaSaglayicisi], saglayici_tipi: str, gosterim_adi: str, api_key: str, base_url: str, varsayilan_model: str) -> YapayZekaSaglayicisi:
    mevcut_api_key_var = bool(saglayici and saglayici.api_key_encrypted)
    saglayici_tipi, gosterim_adi, etkili_base_url = saglayici_formunu_dogrula(saglayici_tipi, gosterim_adi, api_key, base_url, api_key_zorunlu=not mevcut_api_key_var)
    if saglayici is None:
        saglayici = YapayZekaSaglayicisi(kullanici_id=kullanici.id)
        vt.add(saglayici)
    saglayici.saglayici_tipi = saglayici_tipi
    saglayici.ad = gosterim_adi
    saglayici.gosterim_adi = gosterim_adi
    saglayici.base_url = etkili_base_url
    if api_key.strip():
        sifreli_anahtar = metni_sifrele(api_key.strip())
        saglayici.api_key = sifreli_anahtar
        saglayici.api_key_encrypted = sifreli_anahtar
        saglayici.api_key_masked = anahtar_maskele(api_key.strip())
    saglayici.varsayilan_model = varsayilan_model.strip() or None
    saglayici.aktif_mi = True
    vt.commit()
    vt.refresh(saglayici)
    return saglayici


def saglayici_modellerini_oku(saglayici: YapayZekaSaglayicisi | None) -> List[str]:
    if not saglayici or not saglayici.modeller_json:
        return []
    try:
        veri = json.loads(saglayici.modeller_json)
        return [str(oge) for oge in veri] if isinstance(veri, list) else []
    except json.JSONDecodeError:
        return []


def saglayici_modellerini_yenile(vt: Session, saglayici: YapayZekaSaglayicisi) -> Dict[str, Any]:
    adaptor = adaptoru_olustur(saglayici)
    try:
        sonuc = adaptor.test_connection()
        modeller = sonuc.get("modeller", [])
        modeller_json = json.dumps(modeller, ensure_ascii=False)
        saglayici.modeller = modeller_json
        saglayici.modeller_json = modeller_json
        saglayici.son_test_basarili = bool(sonuc.get("basarili"))
        saglayici.son_test_mesaji = sonuc.get("mesaj", "")
        saglayici.son_test_tarihi = datetime.utcnow()
        saglayici.son_gecikme_ms = sonuc.get("gecikme_ms", 0)
        if modeller and not saglayici.varsayilan_model:
            saglayici.varsayilan_model = modeller[0]
        vt.commit()
        vt.refresh(saglayici)
        return sonuc
    except Exception as hata:
        saglayici.son_test_basarili = False
        saglayici.son_test_mesaji = okunur_hata_mesaji(hata)
        saglayici.son_test_tarihi = datetime.utcnow()
        vt.commit()
        raise AIServisHatasi(saglayici.son_test_mesaji) from hata


def kullanici_ayarini_getir_veya_olustur(vt: Session, kullanici_id: int) -> KullaniciAyari:
    ayar = vt.query(KullaniciAyari).filter(KullaniciAyari.kullanici_id == kullanici_id).first()
    if ayar:
        return ayar
    ayar = KullaniciAyari(kullanici_id=kullanici_id)
    vt.add(ayar)
    vt.commit()
    vt.refresh(ayar)
    return ayar


def model_analize_uygun_mu(model: str) -> bool:
    ad = (model or "").lower()
    return bool(ad) and not any(kelime in ad for kelime in ANALIZ_ENGELLI_MODEL_ANAHTARLARI)


def analiz_icin_saglayiciyi_getir(vt: Session, kullanici_id: int) -> Tuple[KullaniciAyari, YapayZekaSaglayicisi, str]:
    ayar = kullanici_ayarini_getir_veya_olustur(vt, kullanici_id)
    if not ayar.secili_saglayici_id:
        raise AnalizIcinSaglayiciEksikHatasi("Varsayılan AI sağlayıcısı seçilmemiş.")
    saglayici = vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.id == ayar.secili_saglayici_id, YapayZekaSaglayicisi.kullanici_id == kullanici_id, YapayZekaSaglayicisi.aktif_mi == True).first()
    if not saglayici:
        raise AnalizIcinSaglayiciEksikHatasi("Seçili AI sağlayıcısı bulunamadı.")
    if not saglayici.son_test_basarili:
        raise AnalizIcinSaglayiciEksikHatasi("Seçili AI sağlayıcısı test edilmemiş veya bağlantı hatalı.")
    model = ayar.secili_model or saglayici.varsayilan_model
    if not model:
        modeller = saglayici_modellerini_oku(saglayici)
        model = modeller[0] if modeller else ""
    if not model:
        raise AnalizIcinSaglayiciEksikHatasi("Seçili sağlayıcı için kullanılabilir model yok.")
    if not model_analize_uygun_mu(model):
        raise DesteklenmeyenModelHatasi("Seçili model debugger analizine uygun değil.")
    return ayar, saglayici, model


def okunur_hata_mesaji(hata: Exception) -> str:
    mesaj = str(hata).strip()
    return mesaj or "İşlem sırasında bir hata oluştu."


def json_cevabini_normallestir(ham_icerik: str) -> Dict[str, str]:
    temiz_icerik = (ham_icerik or "").strip()
    if not temiz_icerik:
        raise AIServisHatasi("Sağlayıcıdan boş yanıt döndü.")
    baslangic = temiz_icerik.find("{")
    bitis = temiz_icerik.rfind("}")
    if baslangic != -1 and bitis != -1 and bitis >= baslangic:
        temiz_icerik = temiz_icerik[baslangic:bitis + 1]
    try:
        veri = json.loads(temiz_icerik)
    except json.JSONDecodeError as hata:
        raise AIServisHatasi("Sağlayıcı geçerli JSON döndürmedi.") from hata
    sonuc = JSON_SABLONU.copy()
    for anahtar in sonuc:
        if anahtar in veri and veri[anahtar] is not None:
            sonuc[anahtar] = str(veri[anahtar])
    if not sonuc["kok_neden"]:
        raise AIServisHatasi("Analiz yanıtı eksik alanlar içeriyor.")
    return sonuc


def fiyat_hesapla(saglayici_tipi: str, girdi_tokeni: int, cikti_tokeni: int) -> float:
    giris_birim, cikis_birim = MODEL_FIYAT_CARPANLARI.get(saglayici_tipi, (0.0, 0.0))
    return round((girdi_tokeni * giris_birim) + (cikti_tokeni * cikis_birim), 6)


def kullanici_saglayicilarini_getir(vt: Session, kullanici_id: int) -> List[YapayZekaSaglayicisi]:
    return vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.kullanici_id == kullanici_id).order_by(YapayZekaSaglayicisi.olusturulma_tarihi.desc()).all()


def analiz_baslat(vt: Session, oturum: HataOturumu, baglam: str, kullanici_id: int):
    _, saglayici, model = analiz_icin_saglayiciyi_getir(vt, kullanici_id)
    adaptor = adaptoru_olustur(saglayici)
    istek_kaydi = YapayZekaIstegi(oturum_id=oturum.id, saglayici=saglayici.gosterim_adi, model=model, istek_icerigi=baglam)
    vt.add(istek_kaydi)
    vt.commit()

    try:
        cevap = adaptor.analyze_debug_context(baglam, model)
    except Exception as hata:
        oturum.durum = "hata_olustu"
        istek_kaydi.basarili = False
        istek_kaydi.yanit_icerigi = okunur_hata_mesaji(hata)
        vt.commit()
        raise

    sonuc = cevap["sonuc"]
    girdi_tokeni = cevap["girdi_tokeni"]
    cikti_tokeni = cevap["cikti_tokeni"]
    toplam_tokeni = girdi_tokeni + cikti_tokeni
    tahmini_maliyet = fiyat_hesapla(saglayici.saglayici_tipi, girdi_tokeni, cikti_tokeni)

    istek_kaydi.yanit_icerigi = json.dumps(sonuc, ensure_ascii=False)
    istek_kaydi.basarili = True
    istek_kaydi.girdi_tokeni = girdi_tokeni
    istek_kaydi.cikti_tokeni = cikti_tokeni
    istek_kaydi.toplam_tokeni = toplam_tokeni
    istek_kaydi.tahmini_maliyet = tahmini_maliyet
    istek_kaydi.gecikme_ms = cevap["gecikme_ms"]

    rapor = HataRaporu(oturum_id=oturum.id, kok_neden=sonuc.get("kok_neden", ""), onem_derecesi=sonuc.get("onem_derecesi", ""), etkilenen_katman=sonuc.get("etkilenen_katman", ""), cozum_onerileri=sonuc.get("cozum_onerileri", ""), iyilestirilmis_kod=sonuc.get("iyilestirilmis_kod", ""), guvenlik_notlari=sonuc.get("guvenlik_notlari", ""))
    vt.add(rapor)

    oturum.durum = "tamamlandi"
    oturum.secilen_saglayici = saglayici.gosterim_adi
    oturum.secilen_model = model
    oturum.tahmini_girdi_tokeni = girdi_tokeni
    oturum.tahmini_cikti_tokeni = cikti_tokeni
    oturum.tahmini_maliyet = tahmini_maliyet

    saglayici.son_kullanim_tarihi = datetime.utcnow()
    saglayici.son_gecikme_ms = cevap["gecikme_ms"]
    onceki_toplam = vt.query(YapayZekaIstegi).filter(YapayZekaIstegi.saglayici == saglayici.gosterim_adi).count()
    onceki_basarili = vt.query(YapayZekaIstegi).filter(YapayZekaIstegi.saglayici == saglayici.gosterim_adi, YapayZekaIstegi.basarili == True).count()
    saglayici.son_basari_orani = ((onceki_basarili + 1) / max(onceki_toplam + 1, 1))
    saglayici.aylik_tahmini_maliyet = round((saglayici.aylik_tahmini_maliyet or 0) + tahmini_maliyet, 6)

    vt.commit()


def saglayici_secimlerini_hazirla(vt: Session, kullanici_id: int) -> Dict[str, Any]:
    ayar = kullanici_ayarini_getir_veya_olustur(vt, kullanici_id)
    saglayicilar = kullanici_saglayicilarini_getir(vt, kullanici_id)
    aktif_saglayici = next((s for s in saglayicilar if s.id == ayar.secili_saglayici_id), None)
    aktif_model_listesi = saglayici_modellerini_oku(aktif_saglayici) if aktif_saglayici else []
    return {"ayar": ayar, "saglayicilar": saglayicilar, "aktif_saglayici": aktif_saglayici, "aktif_model_listesi": aktif_model_listesi, "saglayici_tipleri": SAGLAYICI_TIPLERI}
