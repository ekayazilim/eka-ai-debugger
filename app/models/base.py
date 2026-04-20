from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from core.database import Taban


class Kullanici(Taban):
    __tablename__ = "kullanicilar"

    id = Column(Integer, primary_key=True, index=True)
    ad_soyad = Column(String(255), nullable=False)
    eposta = Column(String(255), unique=True, index=True, nullable=False)
    sifre_hash = Column(String(255), nullable=False)
    rol = Column(String(50), default="kullanici")
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    calisma_alanlari = relationship("CalismaAlani", back_populates="sahip")
    oturumlar = relationship("HataOturumu", back_populates="olusturan")
    bilgi_tabani_kayitlari = relationship("BilgiTabaniKaydi", back_populates="kullanici", cascade="all, delete-orphan")
    yapay_zeka_saglayicilari = relationship("YapayZekaSaglayicisi", back_populates="kullanici", cascade="all, delete-orphan")
    ayar = relationship("KullaniciAyari", back_populates="kullanici", uselist=False, cascade="all, delete-orphan")


class CalismaAlani(Taban):
    __tablename__ = "calisma_alanlari"

    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(255), nullable=False)
    aciklama = Column(Text, nullable=True)
    sahip_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False)
    aktif_mi = Column(Boolean, default=True)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    sahip = relationship("Kullanici", back_populates="calisma_alanlari")
    uyeler = relationship("CalismaAlaniUyesi", back_populates="calisma_alani", cascade="all, delete-orphan")
    oturumlar = relationship("HataOturumu", back_populates="calisma_alani")
    bilgi_tabani_kayitlari = relationship("BilgiTabaniKaydi", back_populates="calisma_alani", cascade="all, delete-orphan")


class CalismaAlaniUyesi(Taban):
    __tablename__ = "calisma_alani_uyeleri"

    id = Column(Integer, primary_key=True, index=True)
    calisma_alani_id = Column(Integer, ForeignKey("calisma_alanlari.id", ondelete="CASCADE"), nullable=False)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False)
    rol = Column(String(50), default="uye")
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    calisma_alani = relationship("CalismaAlani", back_populates="uyeler")
    kullanici = relationship("Kullanici")


class HataOturumu(Taban):
    __tablename__ = "hata_otirumlari"

    id = Column(Integer, primary_key=True, index=True)
    calisma_alani_id = Column(Integer, ForeignKey("calisma_alanlari.id", ondelete="CASCADE"), nullable=False)
    olusturan_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False)
    benzer_oturum_id = Column(Integer, ForeignKey("hata_otirumlari.id", ondelete="SET NULL"), nullable=True)
    baslik = Column(String(255), nullable=False)
    programlama_dili = Column(String(100), nullable=False)
    kod_parcasi = Column(Text, nullable=False)
    hata_logu = Column(Text)
    yigin_izleme = Column(Text)
    ek_notlar = Column(Text)
    etiketler_metin = Column(String(500), nullable=True)
    secilen_saglayici = Column(String(100), nullable=True)
    secilen_model = Column(String(255), nullable=True)
    baglam_ozeti = Column(Text, nullable=True)
    benzerlik_skoru = Column(Float, nullable=True)
    tahmini_girdi_tokeni = Column(Integer, default=0)
    tahmini_cikti_tokeni = Column(Integer, default=0)
    tahmini_maliyet = Column(Float, default=0)
    durum = Column(String(50), default="bekliyor")
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    calisma_alani = relationship("CalismaAlani", back_populates="oturumlar")
    olusturan = relationship("Kullanici", back_populates="oturumlar")
    rapor = relationship("HataRaporu", back_populates="oturum", uselist=False, cascade="all, delete-orphan")
    dosyalar = relationship("HataOturumDosyasi", back_populates="oturum", cascade="all, delete-orphan")
    benzer_oturum = relationship("HataOturumu", remote_side=[id])
    bilgi_tabani_kayitlari = relationship("BilgiTabaniKaydi", back_populates="kaynak_oturum")


class HataOturumDosyasi(Taban):
    __tablename__ = "hata_oturum_dosyalari"

    id = Column(Integer, primary_key=True, index=True)
    oturum_id = Column(Integer, ForeignKey("hata_otirumlari.id", ondelete="CASCADE"), nullable=False)
    dosya_adi = Column(String(255), nullable=False)
    orijinal_ad = Column(String(255), nullable=False)
    icerik_tipi = Column(String(120), nullable=True)
    boyut = Column(Integer, default=0)
    kayit_yolu = Column(String(500), nullable=False)
    metin_icerigi = Column(Text, nullable=True)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    oturum = relationship("HataOturumu", back_populates="dosyalar")


class HataRaporu(Taban):
    __tablename__ = "hata_raporlari"

    id = Column(Integer, primary_key=True, index=True)
    oturum_id = Column(Integer, ForeignKey("hata_otirumlari.id", ondelete="CASCADE"), nullable=False)
    kok_neden = Column(Text)
    onem_derecesi = Column(String(50))
    etkilenen_katman = Column(String(100))
    cozum_onerileri = Column(Text)
    iyilestirilmis_kod = Column(Text)
    guvenlik_notlari = Column(Text)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    oturum = relationship("HataOturumu", back_populates="rapor")


class BilgiTabaniKaydi(Taban):
    __tablename__ = "bilgi_tabani_kayitlari"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False, index=True)
    calisma_alani_id = Column(Integer, ForeignKey("calisma_alanlari.id", ondelete="SET NULL"), nullable=True, index=True)
    kaynak_oturum_id = Column(Integer, ForeignKey("hata_otirumlari.id", ondelete="SET NULL"), nullable=True)
    baslik = Column(String(255), nullable=False)
    kategori = Column(String(100), nullable=True)
    etiketler_metin = Column(String(500), nullable=True)
    ozet = Column(Text, nullable=True)
    icerik = Column(Text, nullable=False)
    durum = Column(String(50), default="taslak")
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncellenme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kullanici = relationship("Kullanici", back_populates="bilgi_tabani_kayitlari")
    calisma_alani = relationship("CalismaAlani", back_populates="bilgi_tabani_kayitlari")
    kaynak_oturum = relationship("HataOturumu", back_populates="bilgi_tabani_kayitlari")


class IstemeSablonu(Taban):
    __tablename__ = "istem_sablonlari"

    id = Column(Integer, primary_key=True, index=True)
    baslik = Column(String(255), nullable=False)
    icerik = Column(Text, nullable=False)
    versiyon = Column(Integer, default=1)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)


class YapayZekaIstegi(Taban):
    __tablename__ = "yapay_zeka_istekleri"

    id = Column(Integer, primary_key=True, index=True)
    oturum_id = Column(Integer, ForeignKey("hata_otirumlari.id", ondelete="CASCADE"), nullable=False)
    saglayici = Column(String(100), nullable=False)
    model = Column(String(255), nullable=True)
    istek_icerigi = Column(Text, nullable=False)
    yanit_icerigi = Column(Text)
    girdi_tokeni = Column(Integer, default=0)
    cikti_tokeni = Column(Integer, default=0)
    toplam_tokeni = Column(Integer, default=0)
    tahmini_maliyet = Column(Float, default=0)
    gecikme_ms = Column(Integer, default=0)
    basarili = Column(Boolean, default=False)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)


class SistemGunlukleri(Taban):
    __tablename__ = "sistem_gunlukleri"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="SET NULL"), nullable=True)
    islem_tipi = Column(String(100), nullable=False)
    detaylar = Column(Text)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)


class YapayZekaSaglayicisi(Taban):
    __tablename__ = "yapay_zeka_saglayicilari"

    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), nullable=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False, index=True)
    saglayici_tipi = Column(String(50), nullable=False)
    gosterim_adi = Column(String(100), nullable=False)
    base_url = Column(String(255), nullable=True)
    api_key = Column(Text, nullable=True)
    api_key_encrypted = Column(Text, nullable=False)
    api_key_masked = Column(String(255), nullable=True)
    varsayilan_model = Column(String(255), nullable=True)
    modeller = Column(Text, nullable=True)
    modeller_json = Column(Text, nullable=True)
    son_test_basarili = Column(Boolean, default=False)
    son_test_mesaji = Column(Text, nullable=True)
    son_test_tarihi = Column(DateTime, nullable=True)
    son_gecikme_ms = Column(Integer, default=0)
    son_basari_orani = Column(Float, default=0)
    son_kullanim_tarihi = Column(DateTime, nullable=True)
    aylik_tahmini_maliyet = Column(Float, default=0)
    aktif_mi = Column(Boolean, default=True)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    kullanici = relationship("Kullanici", back_populates="yapay_zeka_saglayicilari")
    kullanan_ayarlar = relationship("KullaniciAyari", back_populates="secili_saglayici")


class KullaniciAyari(Taban):
    __tablename__ = "kullanici_ayarlari"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), unique=True, nullable=False)
    aktif_calisma_alani_id = Column(Integer, ForeignKey("calisma_alanlari.id", ondelete="SET NULL"), nullable=True)
    secili_saglayici_id = Column(Integer, ForeignKey("yapay_zeka_saglayicilari.id", ondelete="SET NULL"), nullable=True)
    secili_model = Column(String(255), nullable=True)

    kullanici = relationship("Kullanici", back_populates="ayar")
    secili_saglayici = relationship("YapayZekaSaglayicisi", back_populates="kullanan_ayarlar")
    aktif_calisma_alani = relationship("CalismaAlani")
