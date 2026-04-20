from sqlalchemy import inspect, text
from core.database import motor


TABLO_KOLONLARI = {
    "calisma_alanlari": {
        "aciklama": "ALTER TABLE calisma_alanlari ADD COLUMN aciklama TEXT NULL",
        "aktif_mi": "ALTER TABLE calisma_alanlari ADD COLUMN aktif_mi BOOLEAN DEFAULT TRUE",
    },
    "hata_otirumlari": {
        "benzer_oturum_id": "ALTER TABLE hata_otirumlari ADD COLUMN benzer_oturum_id INTEGER NULL",
        "etiketler_metin": "ALTER TABLE hata_otirumlari ADD COLUMN etiketler_metin VARCHAR(500) NULL",
        "secilen_saglayici": "ALTER TABLE hata_otirumlari ADD COLUMN secilen_saglayici VARCHAR(100) NULL",
        "secilen_model": "ALTER TABLE hata_otirumlari ADD COLUMN secilen_model VARCHAR(255) NULL",
        "baglam_ozeti": "ALTER TABLE hata_otirumlari ADD COLUMN baglam_ozeti TEXT NULL",
        "benzerlik_skoru": "ALTER TABLE hata_otirumlari ADD COLUMN benzerlik_skoru FLOAT NULL",
        "tahmini_girdi_tokeni": "ALTER TABLE hata_otirumlari ADD COLUMN tahmini_girdi_tokeni INTEGER DEFAULT 0",
        "tahmini_cikti_tokeni": "ALTER TABLE hata_otirumlari ADD COLUMN tahmini_cikti_tokeni INTEGER DEFAULT 0",
        "tahmini_maliyet": "ALTER TABLE hata_otirumlari ADD COLUMN tahmini_maliyet FLOAT DEFAULT 0",
    },
    "yapay_zeka_istekleri": {
        "model": "ALTER TABLE yapay_zeka_istekleri ADD COLUMN model VARCHAR(255) NULL",
        "girdi_tokeni": "ALTER TABLE yapay_zeka_istekleri ADD COLUMN girdi_tokeni INTEGER DEFAULT 0",
        "cikti_tokeni": "ALTER TABLE yapay_zeka_istekleri ADD COLUMN cikti_tokeni INTEGER DEFAULT 0",
        "toplam_tokeni": "ALTER TABLE yapay_zeka_istekleri ADD COLUMN toplam_tokeni INTEGER DEFAULT 0",
        "tahmini_maliyet": "ALTER TABLE yapay_zeka_istekleri ADD COLUMN tahmini_maliyet FLOAT DEFAULT 0",
        "gecikme_ms": "ALTER TABLE yapay_zeka_istekleri ADD COLUMN gecikme_ms INTEGER DEFAULT 0",
    },
    "yapay_zeka_saglayicilari": {
        "kullanici_id": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN kullanici_id INTEGER NULL",
        "saglayici_tipi": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN saglayici_tipi VARCHAR(50) NULL",
        "gosterim_adi": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN gosterim_adi VARCHAR(100) NULL",
        "api_key_encrypted": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN api_key_encrypted TEXT NULL",
        "api_key_masked": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN api_key_masked VARCHAR(255) NULL",
        "varsayilan_model": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN varsayilan_model VARCHAR(255) NULL",
        "modeller_json": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN modeller_json TEXT NULL",
        "son_test_basarili": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN son_test_basarili BOOLEAN DEFAULT FALSE",
        "son_test_mesaji": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN son_test_mesaji TEXT NULL",
        "son_test_tarihi": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN son_test_tarihi DATETIME NULL",
        "son_gecikme_ms": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN son_gecikme_ms INTEGER DEFAULT 0",
        "son_basari_orani": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN son_basari_orani FLOAT DEFAULT 0",
        "son_kullanim_tarihi": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN son_kullanim_tarihi DATETIME NULL",
        "aylik_tahmini_maliyet": "ALTER TABLE yapay_zeka_saglayicilari ADD COLUMN aylik_tahmini_maliyet FLOAT DEFAULT 0",
    },
    "kullanici_ayarlari": {
        "aktif_calisma_alani_id": "ALTER TABLE kullanici_ayarlari ADD COLUMN aktif_calisma_alani_id INTEGER NULL",
    },
}


def _kolonlari_ekle(tablo_adi: str, baglanti):
    denetleyici = inspect(motor)
    kolonlar = {kolon["name"] for kolon in denetleyici.get_columns(tablo_adi)}
    for kolon_adi, sql in TABLO_KOLONLARI.get(tablo_adi, {}).items():
        if kolon_adi not in kolonlar:
            baglanti.execute(text(sql))


def ayarlar_semasini_yukselt():
    denetleyici = inspect(motor)
    tablolar = set(denetleyici.get_table_names())

    with motor.begin() as baglanti:
        for tablo_adi in TABLO_KOLONLARI:
            if tablo_adi in tablolar:
                _kolonlari_ekle(tablo_adi, baglanti)

        if "yapay_zeka_saglayicilari" in tablolar:
            kolonlar = {kolon["name"] for kolon in inspect(motor).get_columns("yapay_zeka_saglayicilari")}
            if "gosterim_adi" in kolonlar and "ad" in kolonlar:
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET gosterim_adi = COALESCE(gosterim_adi, ad) WHERE gosterim_adi IS NULL OR gosterim_adi = ''"))
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET ad = COALESCE(ad, gosterim_adi, saglayici_tipi, 'Saglayici') WHERE ad IS NULL OR ad = ''"))
            if "api_key_encrypted" in kolonlar and "api_key" in kolonlar:
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET api_key_encrypted = COALESCE(api_key_encrypted, api_key) WHERE (api_key_encrypted IS NULL OR api_key_encrypted = '') AND api_key IS NOT NULL AND api_key <> ''"))
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET api_key = COALESCE(api_key, api_key_encrypted) WHERE (api_key IS NULL OR api_key = '') AND api_key_encrypted IS NOT NULL AND api_key_encrypted <> ''"))
            if "modeller_json" in kolonlar and "modeller" in kolonlar:
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET modeller_json = COALESCE(modeller_json, modeller) WHERE (modeller_json IS NULL OR modeller_json = '') AND modeller IS NOT NULL AND modeller <> ''"))
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET modeller = COALESCE(modeller, modeller_json) WHERE (modeller IS NULL OR modeller = '') AND modeller_json IS NOT NULL AND modeller_json <> ''"))
            if "saglayici_tipi" in kolonlar:
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET saglayici_tipi = COALESCE(saglayici_tipi, 'openai') WHERE saglayici_tipi IS NULL OR saglayici_tipi = ''"))
            if "gosterim_adi" in kolonlar:
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET gosterim_adi = COALESCE(gosterim_adi, saglayici_tipi, 'Saglayici') WHERE gosterim_adi IS NULL OR gosterim_adi = ''"))
            if "aktif_mi" in kolonlar:
                baglanti.execute(text("UPDATE yapay_zeka_saglayicilari SET aktif_mi = 1 WHERE aktif_mi IS NULL"))

        if "kullanici_ayarlari" in tablolar:
            baglanti.execute(text("INSERT INTO kullanici_ayarlari (kullanici_id, secili_saglayici_id, secili_model, aktif_calisma_alani_id) SELECT k.id, NULL, NULL, NULL FROM kullanicilar k LEFT JOIN kullanici_ayarlari ka ON ka.kullanici_id = k.id WHERE ka.id IS NULL"))
            baglanti.execute(text("UPDATE kullanici_ayarlari ka SET aktif_calisma_alani_id = (SELECT ca.id FROM calisma_alanlari ca WHERE ca.sahip_id = ka.kullanici_id ORDER BY ca.id LIMIT 1) WHERE aktif_calisma_alani_id IS NULL"))
