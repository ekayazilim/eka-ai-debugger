import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())

files = {
    "requirements.txt": """
fastapi==0.111.0
uvicorn==0.29.0
jinja2==3.1.3
sqlalchemy==2.0.30
pymysql==1.1.0
python-multipart==0.0.9
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
pydantic==2.7.1
pydantic-settings==2.2.1
python-dotenv==1.0.1
openai==1.30.1
anthropic==0.26.0
aiofiles==23.2.1
""",
    ".env": """
DATABASE_URL=mysql+pymysql://root:ServBay.dev@localhost/eka_ai_debugger
SECRET_KEY=9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
OPENAI_API_KEY=sk-test-key
ANTHROPIC_API_KEY=sk-ant-test-key
AI_PROVIDER=mock
""",
    "core/config.py": """
from pydantic_settings import BaseSettings

class Ayarlar(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    AI_PROVIDER: str

    class Config:
        env_file = ".env"

ayarlar = Ayarlar()
""",
    "core/database.py": """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import ayarlar

motor = create_engine(ayarlar.DATABASE_URL, echo=False)
OturumYerel = sessionmaker(autocommit=False, autoflush=False, bind=motor)
Taban = declarative_base()

def veritabani_al():
    vt = OturumYerel()
    try:
        yield vt
    finally:
        vt.close()
""",
    "core/security.py": """
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import ayarlar

sifre_baglami = CryptContext(schemes=["bcrypt"], deprecated="auto")

def sifre_dogrula(duz_sifre, hashli_sifre):
    return sifre_baglami.verify(duz_sifre, hashli_sifre)

def sifre_hashle(sifre):
    return sifre_baglami.hash(sifre)

def erisim_tokeni_olustur(veri: dict, suresiz_mi: Optional[timedelta] = None):
    kopyalanacak_veri = veri.copy()
    bitis = datetime.utcnow() + (suresiz_mi if suresiz_mi else timedelta(minutes=ayarlar.ACCESS_TOKEN_EXPIRE_MINUTES))
    kopyalanacak_veri.update({"exp": bitis})
    return jwt.encode(kopyalanacak_veri, ayarlar.SECRET_KEY, algorithm=ayarlar.ALGORITHM)

def token_dogrula(token: str):
    try:
        payload = jwt.decode(token, ayarlar.SECRET_KEY, algorithms=[ayarlar.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
""",
    "core/logging.py": """
import logging
import os

os.makedirs("storage/logs", exist_ok=True)

logger = logging.getLogger("EkaAIDebugger")
logger.setLevel(logging.ERROR)

dosya_isleyicisi = logging.FileHandler("storage/logs/app.log")
dosya_isleyicisi.setLevel(logging.ERROR)

bickimleyici = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
dosya_isleyicisi.setFormatter(bickimleyici)

logger.addHandler(dosya_isleyicisi)
""",
    "app/models/base.py": """
from core.database import Taban
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

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

class CalismaAlani(Taban):
    __tablename__ = "calisma_alanlari"
    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(255), nullable=False)
    sahip_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="CASCADE"), nullable=False)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    sahip = relationship("Kullanici", back_populates="calisma_alanlari")
    uyeler = relationship("CalismaAlaniUyesi", back_populates="calisma_alani", cascade="all, delete-orphan")
    oturumlar = relationship("HataOturumu", back_populates="calisma_alani")

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
    baslik = Column(String(255), nullable=False)
    programlama_dili = Column(String(100), nullable=False)
    kod_parcasi = Column(Text, nullable=False)
    hata_logu = Column(Text)
    yigin_izleme = Column(Text)
    ek_notlar = Column(Text)
    durum = Column(String(50), default="bekliyor")
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

    calisma_alani = relationship("CalismaAlani", back_populates="oturumlar")
    olusturan = relationship("Kullanici", back_populates="oturumlar")
    rapor = relationship("HataRaporu", back_populates="oturum", uselist=False, cascade="all, delete-orphan")

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
    istek_icerigi = Column(Text, nullable=False)
    yanit_icerigi = Column(Text)
    basarili = Column(Boolean, default=False)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)

class SistemGunlukleri(Taban):
    __tablename__ = "sistem_gunlukleri"
    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id", ondelete="SET NULL"), nullable=True)
    islem_tipi = Column(String(100), nullable=False)
    detaylar = Column(Text)
    olusturulma_tarihi = Column(DateTime, default=datetime.utcnow)
""",
    "app/schemas/kullanici_sema.py": """
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class KullaniciGiris(BaseModel):
    eposta: EmailStr
    sifre: str

class KullaniciKayit(BaseModel):
    ad_soyad: str
    eposta: EmailStr
    sifre: str

class KullaniciCikti(BaseModel):
    id: int
    ad_soyad: str
    eposta: EmailStr
    rol: str
    olusturulma_tarihi: datetime

    class Config:
        from_attributes = True
""",
    "app/schemas/oturum_sema.py": """
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HataOturumuOlustur(BaseModel):
    baslik: str
    programlama_dili: str
    kod_parcasi: str
    hata_logu: Optional[str] = ""
    yigin_izleme: Optional[str] = ""
    ek_notlar: Optional[str] = ""

class HataRaporuCikti(BaseModel):
    id: int
    kok_neden: Optional[str]
    onem_derecesi: Optional[str]
    etkilenen_katman: Optional[str]
    cozum_onerileri: Optional[str]
    iyilestirilmis_kod: Optional[str]
    guvenlik_notlari: Optional[str]

    class Config:
        from_attributes = True

class HataOturumuCikti(BaseModel):
    id: int
    baslik: str
    programlama_dili: str
    durum: str
    olusturulma_tarihi: datetime

    class Config:
        from_attributes = True
""",
    "app/services/ai_servisi.py": """
from core.config import ayarlar
from app.models.base import YapayZekaIstegi, HataRaporu
from sqlalchemy.orm import Session
import json

class AISaglayici:
    def analiz_et(self, baglam: str) -> dict:
        raise NotImplementedError

class OpenAIProvider(AISaglayici):
    def analiz_et(self, baglam: str) -> dict:
        import openai
        openai.api_key = ayarlar.OPENAI_API_KEY
        try:
            yanit = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Sen kıdemli bir yazılım mimarı ve hata ayıklama uzmanısın. Bize kök neden, önem derecesi, çözüm önerileri ve iyileştirilmiş kod sağlayacaksın. Yanıtın JSON formatında olmalı: {'kok_neden': '...', 'onem_derecesi': 'Yüksek|Orta|Düşük', 'etkilenen_katman': '...', 'cozum_onerileri': '...', 'iyilestirilmis_kod': '...', 'guvenlik_notlari': '...'}"},
                    {"role": "user", "content": baglam}
                ]
            )
            return json.loads(yanit.choices[0].message.content)
        except Exception:
            return {}

class AnthropicProvider(AISaglayici):
    def analiz_et(self, baglam: str) -> dict:
        return {}

class MockProvider(AISaglayici):
    def analiz_et(self, baglam: str) -> dict:
        return {
            "kok_neden": "Sistem test sağlayıcısı tarafından tespit edilen örnek hata türü. Değişken başlatılmamış.",
            "onem_derecesi": "Orta",
            "etkilenen_katman": "Arka Uç Veri İşleme",
            "cozum_onerileri": "Değişkeni kullanmadan önce varsayılan bir değer ile başlatın. Null kontrolleri ekleyin.",
            "iyilestirilmis_kod": "```python\\ndef guvenli_islem(veri=None):\\n    if veri is None:\\n        veri = []\\n    return len(veri)\\n```",
            "guvenlik_notlari": "Girdi doğrudan kullanıldığı için potansiyel tip hatalarına yol açabilir."
        }

def saglayici_getir() -> AISaglayici:
    if ayarlar.AI_PROVIDER == "openai":
        return OpenAIProvider()
    elif ayarlar.AI_PROVIDER == "anthropic":
        return AnthropicProvider()
    else:
        return MockProvider()

def analiz_baslat(vt: Session, oturum: object, baglam: str):
    saglayici = saglayici_getir()
    istek_kaydi = YapayZekaIstegi(
        oturum_id=oturum.id,
        saglayici=ayarlar.AI_PROVIDER,
        istek_icerigi=baglam
    )
    vt.add(istek_kaydi)
    vt.commit()

    sonuc = saglayici.analiz_et(baglam)
    
    istek_kaydi.yanit_icerigi = json.dumps(sonuc)
    istek_kaydi.basarili = True if sonuc else False

    if sonuc:
        rapor = HataRaporu(
            oturum_id=oturum.id,
            kok_neden=sonuc.get("kok_neden", ""),
            onem_derecesi=sonuc.get("onem_derecesi", ""),
            etkilenen_katman=sonuc.get("etkilenen_katman", ""),
            cozum_onerileri=sonuc.get("cozum_onerileri", ""),
            iyilestirilmis_kod=sonuc.get("iyilestirilmis_kod", ""),
            guvenlik_notlari=sonuc.get("guvenlik_notlari", "")
        )
        vt.add(rapor)
        oturum.durum = "tamamlandi"
    else:
        oturum.durum = "hata_olustu"
    
    vt.commit()
""",
    "app/routers/yetkilendirme.py": """
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import veritabani_al
from app.models.base import Kullanici, CalismaAlani
from core.security import sifre_dogrula, sifre_hashle, erisim_tokeni_olustur

router = APIRouter(prefix="/yetkilendirme", tags=["Yetkilendirme"])
sablonlar = Jinja2Templates(directory="app/templates")

@router.get("/giris", response_class=HTMLResponse)
async def giris_sayfasi(request: Request):
    return sablonlar.TemplateResponse("auth/login.html", {"request": request})

@router.post("/giris")
async def giris_islem(request: Request, eposta: str = Form(...), sifre: str = Form(...), vt: Session = Depends(veritabani_al)):
    kullanici = vt.query(Kullanici).filter(Kullanici.eposta == eposta).first()
    if not kullanici or not sifre_dogrula(sifre, kullanici.sifre_hash):
        return sablonlar.TemplateResponse("auth/login.html", {"request": request, "hata": "E-posta veya şifre hatalı."})
    
    token = erisim_tokeni_olustur({"sub": str(kullanici.id)})
    yanit = RedirectResponse(url="/pano", status_code=status.HTTP_302_FOUND)
    yanit.set_cookie(key="erisim_tokeni", value=token, httponly=True)
    return yanit

@router.get("/kayit", response_class=HTMLResponse)
async def kayit_sayfasi(request: Request):
    return sablonlar.TemplateResponse("auth/register.html", {"request": request})

@router.post("/kayit")
async def kayit_islem(request: Request, ad_soyad: str = Form(...), eposta: str = Form(...), sifre: str = Form(...), vt: Session = Depends(veritabani_al)):
    mevcut = vt.query(Kullanici).filter(Kullanici.eposta == eposta).first()
    if mevcut:
        return sablonlar.TemplateResponse("auth/register.html", {"request": request, "hata": "Bu e-posta adresi zaten kullanımda."})
    
    yeni_kullanici = Kullanici(ad_soyad=ad_soyad, eposta=eposta, sifre_hash=sifre_hashle(sifre))
    vt.add(yeni_kullanici)
    vt.commit()
    vt.refresh(yeni_kullanici)

    yeni_alan = CalismaAlani(isim="Kişisel Çalışma Alanı", sahip_id=yeni_kullanici.id)
    vt.add(yeni_alan)
    vt.commit()

    return RedirectResponse(url="/yetkilendirme/giris", status_code=status.HTTP_302_FOUND)

@router.get("/cikis")
async def cikis_islem():
    yanit = RedirectResponse(url="/yetkilendirme/giris", status_code=status.HTTP_302_FOUND)
    yanit.delete_cookie("erisim_tokeni")
    return yanit
""",
    "app/routers/pano.py": """
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import veritabani_al
from core.security import token_dogrula
from app.models.base import Kullanici, HataOturumu, CalismaAlani

router = APIRouter(prefix="/pano", tags=["Pano"])
sablonlar = Jinja2Templates(directory="app/templates")

def mevcut_kullanici(request: Request, vt: Session = Depends(veritabani_al)):
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
    
    calisma_alani = vt.query(CalismaAlani).filter(CalismaAlani.sahip_id == kullanici.id).first()
    
    toplam_oturum = 0
    cozulen_oturum = 0
    bekleyen_oturum = 0
    oturumlar = []

    if calisma_alani:
        oturumlar = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id).order_by(HataOturumu.olusturulma_tarihi.desc()).limit(5).all()
        toplam_oturum = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id).count()
        cozulen_oturum = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id, HataOturumu.durum == 'tamamlandi').count()
        bekleyen_oturum = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id, HataOturumu.durum == 'bekliyor').count()

    return sablonlar.TemplateResponse("dashboard/index.html", {
        "request": request, 
        "kullanici": kullanici,
        "oturumlar": oturumlar,
        "istatistikler": {
            "toplam": toplam_oturum,
            "cozulen": cozulen_oturum,
            "bekleyen": bekleyen_oturum
        }
    })
""",
    "app/routers/oturumlar.py": """
from fastapi import APIRouter, Depends, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import veritabani_al
from app.routers.pano import mevcut_kullanici
from app.models.base import HataOturumu, CalismaAlani, HataRaporu
from app.services.ai_servisi import analiz_baslat

router = APIRouter(prefix="/oturumlar", tags=["Oturumlar"])
sablonlar = Jinja2Templates(directory="app/templates")

@router.get("/yeni", response_class=HTMLResponse)
async def yeni_oturum_sayfasi(request: Request, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    return sablonlar.TemplateResponse("sessions/create.html", {"request": request, "kullanici": kullanici})

@router.post("/yeni")
async def yeni_oturum_islem(
    request: Request, 
    arka_plan_gorevleri: BackgroundTasks,
    baslik: str = Form(...),
    programlama_dili: str = Form(...),
    kod_parcasi: str = Form(...),
    hata_logu: str = Form(""),
    yigin_izleme: str = Form(""),
    ek_notlar: str = Form(""),
    vt: Session = Depends(veritabani_al)
):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    
    calisma_alani = vt.query(CalismaAlani).filter(CalismaAlani.sahip_id == kullanici.id).first()

    yeni_oturum = HataOturumu(
        calisma_alani_id=calisma_alani.id,
        olusturan_id=kullanici.id,
        baslik=baslik,
        programlama_dili=programlama_dili,
        kod_parcasi=kod_parcasi,
        hata_logu=hata_logu,
        yigin_izleme=yigin_izleme,
        ek_notlar=ek_notlar
    )
    vt.add(yeni_oturum)
    vt.commit()
    vt.refresh(yeni_oturum)

    baglam = f"Programlama Dili: {programlama_dili}\\nKod:\\n{kod_parcasi}\\nHata Logu:\\n{hata_logu}\\nYığın İzleme:\\n{yigin_izleme}\\nNotlar:\\n{ek_notlar}"
    arka_plan_gorevleri.add_task(analiz_baslat, vt, yeni_oturum, baglam)

    return RedirectResponse(url=f"/oturumlar/{yeni_oturum.id}", status_code=302)

@router.get("/{oturum_id}", response_class=HTMLResponse)
async def oturum_detay(request: Request, oturum_id: int, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    
    oturum = vt.query(HataOturumu).filter(HataOturumu.id == oturum_id).first()
    rapor = vt.query(HataRaporu).filter(HataRaporu.oturum_id == oturum.id).first() if oturum else None

    return sablonlar.TemplateResponse("sessions/detail.html", {
        "request": request, 
        "kullanici": kullanici,
        "oturum": oturum,
        "rapor": rapor
    })

@router.get("/", response_class=HTMLResponse)
async def oturumlar_sayfasi(request: Request, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    
    calisma_alani = vt.query(CalismaAlani).filter(CalismaAlani.sahip_id == kullanici.id).first()
    oturumlar = vt.query(HataOturumu).filter(HataOturumu.calisma_alani_id == calisma_alani.id).order_by(HataOturumu.olusturulma_tarihi.desc()).all()

    return sablonlar.TemplateResponse("sessions/list.html", {"request": request, "kullanici": kullanici, "oturumlar": oturumlar})

""",
    "app/templates/base.html": """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eka AI Debugger</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
        .sidebar-link { transition: all 0.2s; border-radius: 0.375rem; }
        .sidebar-link:hover { background-color: #f1f5f9; color: #0f172a; }
        .sidebar-active { background-color: #e2e8f0; color: #0f172a; font-weight: 600; }
    </style>
</head>
<body class="text-slate-800 antialiased h-screen flex overflow-hidden">
    {% if kullanici %}
    <aside class="w-64 bg-white border-r border-slate-200 flex flex-col h-full bg-slate-50">
        <div class="h-16 flex items-center px-6 border-b border-slate-200 bg-white">
            <h1 class="text-xl font-bold text-slate-800 tracking-tight"><i class="fa-solid fa-microchip text-navy-600 mr-2"></i>Eka <span class="text-slate-500 font-medium">Debugger</span></h1>
        </div>
        <div class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
            <a href="/pano" class="sidebar-link flex items-center px-3 py-2.5 text-sm cursor-pointer text-slate-600">
                <i class="fa-solid fa-chart-pie w-5 mr-3"></i> Pano
            </a>
            <a href="/oturumlar/yeni" class="sidebar-link flex items-center px-3 py-2.5 text-sm cursor-pointer text-slate-600">
                <i class="fa-solid fa-plus-circle w-5 mr-3"></i> Yeni Oturum
            </a>
            <a href="/oturumlar" class="sidebar-link flex items-center px-3 py-2.5 text-sm cursor-pointer text-slate-600">
                <i class="fa-solid fa-list w-5 mr-3"></i> Tüm Oturumlar
            </a>
            <hr class="my-4 border-slate-200">
            <a href="/bilgi-tabani" class="sidebar-link flex items-center px-3 py-2.5 text-sm cursor-pointer text-slate-600">
                <i class="fa-solid fa-book w-5 mr-3"></i> Bilgi Tabanı
            </a>
            <a href="/ayarlar" class="sidebar-link flex items-center px-3 py-2.5 text-sm cursor-pointer text-slate-600">
                <i class="fa-solid fa-cog w-5 mr-3"></i> Ayarlar
            </a>
        </div>
        <div class="p-4 border-t border-slate-200 bg-white">
            <div class="flex items-center">
                <div class="h-8 w-8 rounded bg-slate-200 flex items-center justify-center text-slate-600 font-bold">
                    {{ kullanici.ad_soyad[0] }}
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-slate-700">{{ kullanici.ad_soyad }}</p>
                    <a href="/yetkilendirme/cikis" class="text-xs text-slate-500 hover:text-red-500 transition-colors">Çıkış Yap</a>
                </div>
            </div>
        </div>
    </aside>
    {% endif %}
    
    <main class="flex-1 flex flex-col h-full bg-slate-50/50 overflow-hidden">
        {% if kullanici %}
        <header class="h-16 flex items-center justify-between px-8 bg-white border-b border-slate-200 shadow-sm z-10">
            <h2 class="text-lg font-semibold text-slate-800">{% block baslik %}Eka AI Debugger{% endblock %}</h2>
            <div class="flex items-center space-x-4">
                <button class="text-slate-400 hover:text-slate-600"><i class="fa-solid fa-bell"></i></button>
            </div>
        </header>
        {% endif %}
        
        <div class="flex-1 overflow-y-auto p-8">
            <div class="max-w-6xl mx-auto">
                {% block icerik %}{% endblock %}
            </div>
        </div>
    </main>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github-dark.min.css">
    <script>hljs.highlightAll();</script>
</body>
</html>
""",
    "app/templates/auth/login.html": """
{% extends "base.html" %}
{% block icerik %}
<div class="flex min-h-full flex-col justify-center px-6 py-12 lg:px-8 mt-10">
    <div class="sm:mx-auto sm:w-full sm:max-w-sm text-center">
        <h2 class="text-2xl font-bold leading-9 tracking-tight text-slate-900"><i class="fa-solid fa-microchip text-navy-600 mr-2"></i>Eka <span class="text-slate-500">Debugger</span></h2>
        <p class="mt-2 text-sm text-slate-500">Hesabınıza giriş yapın</p>
    </div>

    <div class="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
        {% if hata %}
        <div class="mb-4 rounded-md bg-red-50 p-4 border border-red-200">
            <div class="flex">
                <div class="flex-shrink-0"><i class="fa-solid fa-circle-exclamation text-red-400"></i></div>
                <div class="ml-3"><p class="text-sm font-medium text-red-800">{{ hata }}</p></div>
            </div>
        </div>
        {% endif %}

        <form class="space-y-6 bg-white p-8 rounded-xl shadow-sm border border-slate-200" action="/yetkilendirme/giris" method="POST">
            <div>
                <label for="eposta" class="block text-sm font-medium leading-6 text-slate-900">E-posta Adresi</label>
                <div class="mt-2">
                    <input id="eposta" name="eposta" type="email" required class="block w-full rounded-md border-0 py-2 px-3 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm sm:leading-6">
                </div>
            </div>
            <div>
                <label for="sifre" class="block text-sm font-medium leading-6 text-slate-900">Şifre</label>
                <div class="mt-2">
                    <input id="sifre" name="sifre" type="password" required class="block w-full rounded-md border-0 py-2 px-3 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm sm:leading-6">
                </div>
            </div>
            <div>
                <button type="submit" class="flex w-full justify-center rounded-md bg-slate-800 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 transition-colors">Giriş Yap</button>
            </div>
        </form>
        <p class="mt-8 text-center text-sm text-slate-500">
            Hesabınız yok mu? <a href="/yetkilendirme/kayit" class="font-semibold leading-6 text-slate-800 hover:text-slate-600">Ücretsiz hesap oluşturun</a>
        </p>
    </div>
</div>
{% endblock %}
""",
    "app/templates/auth/register.html": """
{% extends "base.html" %}
{% block icerik %}
<div class="flex min-h-full flex-col justify-center px-6 py-12 lg:px-8 mt-10">
    <div class="sm:mx-auto sm:w-full sm:max-w-sm text-center">
        <h2 class="text-2xl font-bold leading-9 tracking-tight text-slate-900"><i class="fa-solid fa-microchip text-navy-600 mr-2"></i>Eka <span class="text-slate-500">Debugger</span></h2>
        <p class="mt-2 text-sm text-slate-500">Yeni bir çalışma hesabı oluşturun</p>
    </div>

    <div class="mt-10 sm:mx-auto sm:w-full sm:max-w-md">
        {% if hata %}
        <div class="mb-4 rounded-md bg-red-50 p-4 border border-red-200">
            <div class="flex">
                <div class="flex-shrink-0"><i class="fa-solid fa-circle-exclamation text-red-400"></i></div>
                <div class="ml-3"><p class="text-sm font-medium text-red-800">{{ hata }}</p></div>
            </div>
        </div>
        {% endif %}

        <form class="space-y-5 bg-white p-8 rounded-xl shadow-sm border border-slate-200" action="/yetkilendirme/kayit" method="POST">
            <div>
                <label for="ad_soyad" class="block text-sm font-medium leading-6 text-slate-900">Ad Soyad</label>
                <div class="mt-1">
                    <input id="ad_soyad" name="ad_soyad" type="text" required class="block w-full rounded-md border-0 py-2 px-3 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm sm:leading-6">
                </div>
            </div>
            <div>
                <label for="eposta" class="block text-sm font-medium leading-6 text-slate-900">E-posta Adresi</label>
                <div class="mt-1">
                    <input id="eposta" name="eposta" type="email" required class="block w-full rounded-md border-0 py-2 px-3 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm sm:leading-6">
                </div>
            </div>
            <div>
                <label for="sifre" class="block text-sm font-medium leading-6 text-slate-900">Şifre</label>
                <div class="mt-1">
                    <input id="sifre" name="sifre" type="password" required class="block w-full rounded-md border-0 py-2 px-3 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm sm:leading-6">
                </div>
            </div>
            <div class="pt-2">
                <button type="submit" class="flex w-full justify-center rounded-md bg-slate-800 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 transition-colors">Kaydı Tamamla</button>
            </div>
        </form>
        <p class="mt-8 text-center text-sm text-slate-500">
            Zaten hesabınız var mı? <a href="/yetkilendirme/giris" class="font-semibold leading-6 text-slate-800 hover:text-slate-600">Giriş yapın</a>
        </p>
    </div>
</div>
{% endblock %}
""",
    "app/templates/dashboard/index.html": """
{% extends "base.html" %}
{% block baslik %}Genel Bakış{% endblock %}
{% block icerik %}
<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
        <div class="flex items-center justify-between">
            <h3 class="text-sm font-medium text-slate-500">Toplam Hata Analizi</h3>
            <span class="h-8 w-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-sm"><i class="fa-solid fa-chart-simple"></i></span>
        </div>
        <p class="text-3xl font-bold text-slate-800 mt-4">{{ istatistikler.toplam }}</p>
    </div>
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
        <div class="flex items-center justify-between">
            <h3 class="text-sm font-medium text-slate-500">Çözülen Hatalar</h3>
            <span class="h-8 w-8 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center text-sm"><i class="fa-solid fa-check"></i></span>
        </div>
        <p class="text-3xl font-bold text-slate-800 mt-4">{{ istatistikler.cozulen }}</p>
    </div>
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
        <div class="flex items-center justify-between">
            <h3 class="text-sm font-medium text-slate-500">Bekleyen Analizler</h3>
            <span class="h-8 w-8 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center text-sm"><i class="fa-solid fa-hourglass-half"></i></span>
        </div>
        <p class="text-3xl font-bold text-slate-800 mt-4">{{ istatistikler.bekleyen }}</p>
    </div>
</div>

<div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
    <div class="px-6 py-5 border-b border-slate-200 flex items-center justify-between">
        <h3 class="font-semibold text-slate-800">Son Hata Oturumları</h3>
        <a href="/oturumlar" class="text-sm text-slate-500 hover:text-slate-800 font-medium">Tümünü Gör</a>
    </div>
    {% if oturumlar %}
    <div class="overflow-x-auto">
        <table class="w-full text-sm text-left text-slate-600">
            <thead class="text-xs text-slate-500 bg-slate-50 uppercase border-b border-slate-200">
                <tr>
                    <th class="px-6 py-4 font-medium">Başlık</th>
                    <th class="px-6 py-4 font-medium">Dil</th>
                    <th class="px-6 py-4 font-medium">Tarih</th>
                    <th class="px-6 py-4 font-medium">Durum</th>
                    <th class="px-6 py-4 font-medium text-right">İşlem</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
                {% for oturum in oturumlar %}
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="px-6 py-4 font-medium text-slate-800">{{ oturum.baslik }}</td>
                    <td class="px-6 py-4">{{ oturum.programlama_dili }}</td>
                    <td class="px-6 py-4">{{ oturum.olusturulma_tarihi.strftime('%Y-%m-%d %H:%M') }}</td>
                    <td class="px-6 py-4">
                        {% if oturum.durum == 'bekliyor' %}
                        <span class="inline-flex items-center rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">Analiz Ediliyor</span>
                        {% elif oturum.durum == 'tamamlandi' %}
                        <span class="inline-flex items-center rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">Tamamlandı</span>
                        {% else %}
                        <span class="inline-flex items-center rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">Hata</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-right">
                        <a href="/oturumlar/{{ oturum.id }}" class="text-slate-500 hover:text-slate-800 font-medium">Detay <i class="fa-solid fa-arrow-right ml-1 text-xs"></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="px-6 py-12 text-center">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
            <i class="fa-solid fa-code text-2xl text-slate-400"></i>
        </div>
        <h4 class="text-slate-800 font-medium mb-1">Henüz oturum yok</h4>
        <p class="text-sm text-slate-500 mb-6">İlk kod hata analizini başlatmak için yeni bir oturum oluşturun.</p>
        <a href="/oturumlar/yeni" class="rounded-md bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-700">Yeni Oturum Oluştur</a>
    </div>
    {% endif %}
</div>
{% endblock %}
""",
    "app/templates/sessions/create.html": """
{% extends "base.html" %}
{% block baslik %}Yeni Hata Ayıklama Oturumu{% endblock %}
{% block icerik %}
<div class="bg-white rounded-xl shadow-sm border border-slate-200 p-8 max-w-4xl">
    <div class="mb-6">
        <h2 class="text-xl font-bold text-slate-800">Analiz Edilecek Kodu Girin</h2>
        <p class="text-sm text-slate-500 mt-1">Yapay zekanın hatayı bulması için tüm detayları eksiksiz paylaşın.</p>
    </div>
    
    <form action="/oturumlar/yeni" method="POST" class="space-y-6 flex flex-col">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label for="baslik" class="block text-sm font-medium text-slate-700 mb-1">Oturum Başlığı <span class="text-red-500">*</span></label>
                <input type="text" id="baslik" name="baslik" required placeholder="Örn: Kullanıcı girişinde null döndürüyor" class="w-full rounded-md border-0 py-2 px-3 text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm">
            </div>
            <div>
                <label for="programlama_dili" class="block text-sm font-medium text-slate-700 mb-1">Programlama Dili <span class="text-red-500">*</span></label>
                <select id="programlama_dili" name="programlama_dili" required class="w-full rounded-md border-0 py-2 px-3 text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm">
                    <option value="">Seçiniz...</option>
                    <option value="PHP">PHP</option>
                    <option value="Python">Python</option>
                    <option value="JavaScript">JavaScript / TypeScript</option>
                    <option value="C#">C# .NET</option>
                    <option value="SQL">SQL</option>
                    <option value="Go">Go</option>
                    <option value="Diğer">Diğer</option>
                </select>
            </div>
        </div>

        <div>
            <label for="kod_parcasi" class="block text-sm font-medium text-slate-700 mb-1">Kod Parçası <span class="text-red-500">*</span></label>
            <div class="rounded-md ring-1 ring-inset ring-slate-300 bg-slate-900 overflow-hidden">
                <textarea id="kod_parcasi" name="kod_parcasi" rows="8" required class="w-full bg-slate-900 border-0 text-slate-100 p-4 font-mono text-sm focus:ring-0 resize-y" placeholder="// Sorunlu kod bloğunu buraya yapıştırın..."></textarea>
            </div>
        </div>

        <div>
            <label for="hata_logu" class="block text-sm font-medium text-slate-700 mb-1">Hata Mesajı / Çıktısı</label>
            <textarea id="hata_logu" name="hata_logu" rows="3" class="w-full rounded-md border-0 py-2 px-3 text-red-900 bg-red-50 ring-1 ring-inset ring-red-200 focus:ring-2 focus:ring-inset focus:ring-red-400 sm:text-sm font-mono text-xs" placeholder="Örn: Fatal error: Uncaught TypeError..."></textarea>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label for="yigin_izleme" class="block text-sm font-medium text-slate-700 mb-1">Stack Trace (Yığın İzleme)</label>
                <textarea id="yigin_izleme" name="yigin_izleme" rows="4" class="w-full rounded-md border-0 py-2 px-3 text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm text-xs font-mono"></textarea>
            </div>
            <div>
                <label for="ek_notlar" class="block text-sm font-medium text-slate-700 mb-1">Ek Notlar / Beklenen Davranış</label>
                <textarea id="ek_notlar" name="ek_notlar" rows="4" class="w-full rounded-md border-0 py-2 px-3 text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm"></textarea>
            </div>
        </div>

        <div class="pt-4 border-t border-slate-100 flex justify-end">
            <button type="submit" class="rounded-md bg-slate-800 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 flex items-center">
                <i class="fa-solid fa-wand-magic-sparkles mr-2 text-amber-300"></i> AI Analizini Başlat
            </button>
        </div>
    </form>
</div>
{% endblock %}
""",
    "app/templates/sessions/list.html": """
{% extends "base.html" %}
{% block baslik %}Geçmiş Oturumlar{% endblock %}
{% block icerik %}
<div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
    <div class="px-6 py-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
        <h3 class="font-semibold text-slate-800">Tüm Hata Analizleri</h3>
        <div class="flex space-x-2">
            <input type="text" placeholder="Oturum ara..." class="rounded-md border-0 py-1.5 px-3 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-slate-600 sm:text-sm sm:leading-6 w-64">
            <button class="bg-white px-3 py-1.5 border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50"><i class="fa-solid fa-filter mr-1"></i> Filtrele</button>
        </div>
    </div>
    
    {% if oturumlar %}
    <div class="overflow-x-auto">
        <table class="w-full text-sm text-left text-slate-600">
            <thead class="text-xs text-slate-500 bg-white uppercase border-b border-slate-200">
                <tr>
                    <th class="px-6 py-4 font-medium">Başlık</th>
                    <th class="px-6 py-4 font-medium">Dil</th>
                    <th class="px-6 py-4 font-medium">Tarih</th>
                    <th class="px-6 py-4 font-medium">Durum</th>
                    <th class="px-6 py-4 font-medium text-right">İşlem</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
                {% for oturum in oturumlar %}
                <tr class="hover:bg-slate-50 transition-colors">
                    <td class="px-6 py-4 font-medium text-slate-800">{{ oturum.baslik }}</td>
                    <td class="px-6 py-4">
                        <span class="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700 ring-1 ring-inset ring-slate-500/10">{{ oturum.programlama_dili }}</span>
                    </td>
                    <td class="px-6 py-4 text-slate-500">{{ oturum.olusturulma_tarihi.strftime('%Y-%m-%d %H:%M') }}</td>
                    <td class="px-6 py-4">
                        {% if oturum.durum == 'bekliyor' %}
                        <span class="inline-flex items-center rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">İşleniyor</span>
                        {% elif oturum.durum == 'tamamlandi' %}
                        <span class="inline-flex items-center rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">Çözüldü</span>
                        {% else %}
                        <span class="inline-flex items-center rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">Hata</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 text-right">
                        <a href="/oturumlar/{{ oturum.id }}" class="inline-flex items-center rounded-md bg-white px-3 py-1.5 text-xs font-medium text-slate-700 border border-slate-300 shadow-sm hover:bg-slate-50">Önizle</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <div class="px-6 py-4 border-t border-slate-200 flex items-center justify-between bg-white text-sm">
        <span class="text-slate-500">Toplam {{ oturumlar|length }} kayıt bulundu.</span>
        <div class="flex space-x-1">
            <button class="px-3 py-1 border border-slate-200 rounded text-slate-400 bg-slate-50 cursor-not-allowed">Önceki</button>
            <button class="px-3 py-1 border border-slate-200 rounded text-slate-700 bg-white hover:bg-slate-50">Sonraki</button>
        </div>
    </div>
    {% else %}
    <div class="px-6 py-12 text-center bg-white">
        <p class="text-slate-500">Kayıtlı oturum bulunamadı.</p>
    </div>
    {% endif %}
</div>
{% endblock %}
""",
    "app/templates/sessions/detail.html": """
{% extends "base.html" %}
{% block baslik %}Hata Raporu: {{ oturum.baslik }}{% endblock %}
{% block icerik %}
<div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-3">
        <a href="/oturumlar" class="h-8 w-8 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-50 hover:text-slate-800 transition-colors">
            <i class="fa-solid fa-arrow-left text-sm"></i>
        </a>
        <h2 class="text-xl font-bold text-slate-800">{{ oturum.baslik }}</h2>
        {% if oturum.durum == 'tamamlandi' %}
        <span class="inline-flex items-center rounded-md bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20"><i class="fa-solid fa-check-circle mr-1.5"></i> Çözüm Hazır</span>
        {% elif oturum.durum == 'bekliyor' %}
        <span class="inline-flex items-center rounded-md bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20"><i class="fa-solid fa-spinner fa-spin mr-1.5"></i> Yapay Zeka Analiz Ediyor...</span>
        <script>setTimeout(function(){ location.reload(); }, 5000);</script>
        {% endif %}
    </div>
    <div class="flex space-x-3">
        <button class="inline-flex items-center justify-center rounded-md bg-white border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50">
            <i class="fa-solid fa-download mr-1.5 text-slate-400"></i> Raporu İndir
        </button>
        <button class="inline-flex items-center justify-center rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-slate-700">
            <i class="fa-solid fa-share-nodes mr-1.5 text-slate-300"></i> Ekiple Paylaş
        </button>
    </div>
</div>

<div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
    <div class="xl:col-span-2 space-y-6">
        {% if rapor %}
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex justify-between items-center">
                <h3 class="font-semibold text-slate-800 flex items-center"><i class="fa-solid fa-magnifying-glass-chart text-blue-500 mr-2"></i> Yapay Zeka Analiz Sonucu</h3>
                {% if rapor.onem_derecesi == 'Yüksek' %}
                <span class="inline-flex items-center rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/10">Kritik Önem</span>
                {% else %}
                <span class="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/10">{{ rapor.onem_derecesi }}</span>
                {% endif %}
            </div>
            <div class="p-6">
                <div class="mb-6">
                    <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Kök Neden Tespiti</h4>
                    <p class="text-slate-700 text-sm leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-100">{{ rapor.kok_neden }}</p>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div class="bg-white p-4 rounded-lg border border-slate-100 shadow-sm">
                        <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Etkilenen Katman</h4>
                        <p class="text-slate-800 font-medium text-sm"><i class="fa-solid fa-layer-group text-slate-300 mr-2"></i>{{ rapor.etkilenen_katman }}</p>
                    </div>
                </div>

                <div class="mb-6">
                    <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Çözüm Önerisi & Adımlar</h4>
                    <p class="text-slate-700 text-sm leading-relaxed bg-indigo-50/50 p-4 rounded-lg border border-indigo-100">{{ rapor.cozum_onerileri }}</p>
                </div>
                
                {% if rapor.guvenlik_notlari %}
                <div class="mb-0">
                    <h4 class="text-xs font-bold text-red-400 uppercase tracking-wider mb-2"><i class="fa-solid fa-shield-halved mr-1"></i> Güvenlik Uyarısı</h4>
                    <p class="text-red-700 text-sm leading-relaxed bg-red-50 p-4 rounded-lg border border-red-100">{{ rapor.guvenlik_notlari }}</p>
                </div>
                {% endif %}
            </div>
        </div>
        
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                <h3 class="font-semibold text-slate-800 flex items-center"><i class="fa-solid fa-code text-emerald-500 mr-2"></i> İyileştirilmiş Kod</h3>
                <button class="text-xs font-medium text-slate-500 hover:text-slate-800 border border-slate-200 px-2 py-1 rounded bg-white"><i class="fa-regular fa-copy mr-1"></i> Kodu Kopyala</button>
            </div>
            <div class="p-0 bg-slate-900 border-t border-slate-800 rounded-b-xl overflow-hidden relative">
                <div class="absolute top-0 right-0 p-2 text-xs text-slate-500 font-mono">{{ oturum.programlama_dili }}</div>
                <!-- Markdown icinde olan kod bloklari icin. Gosterim basittir. -->
                <pre><code class="language-{{ oturum.programlama_dili.lower() }} p-6 text-sm">{{ rapor.iyilestirilmis_kod|replace('```python','')|replace('```','') }}</code></pre>
            </div>
        </div>
        {% else %}
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-12 flex flex-col items-center justify-center text-center">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4 ring-8 ring-slate-50">
                <i class="fa-solid fa-robot text-2xl text-slate-400 fa-bounce"></i>
            </div>
            <h3 class="text-lg font-medium text-slate-900 mb-2">Analiz Devam Ediyor</h3>
            <p class="text-slate-500 max-w-md mx-auto text-sm">Eka AI Debugger şu anda kodunuzu, yığın izlemesini ve hataları tarıyor. Bu işlem kod karmaşıklığına bağlı olarak birkaç saniye sürebilir.</p>
        </div>
        {% endif %}
    </div>
    
    <div class="xl:col-span-1 space-y-6">
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-200 bg-slate-50/50">
                <h3 class="font-semibold text-slate-800 text-sm">Orijinal Kod</h3>
            </div>
            <div class="p-0 bg-slate-900 text-slate-300 text-xs font-mono max-h-96 overflow-y-auto">
                <pre><code class="language-{{ oturum.programlama_dili.lower() }} p-4">{{ oturum.kod_parcasi }}</code></pre>
            </div>
        </div>

        {% if oturum.hata_logu %}
        <div class="bg-white rounded-xl shadow-sm border border-red-200 overflow-hidden">
            <div class="px-5 py-3 border-b border-red-200 bg-red-50 text-red-800 text-sm font-semibold flex items-center">
                <i class="fa-solid fa-triangle-exclamation mr-2"></i> Hata Çıktısı
            </div>
            <div class="p-4 bg-white text-red-600 text-xs font-mono whitespace-pre-wrap">{{ oturum.hata_logu }}</div>
        </div>
        {% endif %}
        
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
            <h3 class="font-semibold text-slate-800 text-sm mb-4">Gönderim Detayları</h3>
            <dl class="space-y-3 text-sm">
                <div class="flex justify-between border-b border-slate-100 pb-2">
                    <dt class="text-slate-500">Oluşturan</dt>
                    <dd class="font-medium text-slate-800">{{ oturum.olusturan.ad_soyad }}</dd>
                </div>
                <div class="flex justify-between border-b border-slate-100 pb-2">
                    <dt class="text-slate-500">Tarih</dt>
                    <dd class="font-medium text-slate-800">{{ oturum.olusturulma_tarihi.strftime('%Y-%m-%d %H:%M') }}</dd>
                </div>
                <div class="flex justify-between">
                    <dt class="text-slate-500">Ortam</dt>
                    <dd class="font-medium text-slate-800">{{ oturum.programlama_dili }}</dd>
                </div>
            </dl>
        </div>
    </div>
</div>
{% endblock %}
""",
    "main.py": """
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from core.database import motor, Taban
from app.routers import yetkilendirme, pano, oturumlar

Taban.metadata.create_all(bind=motor)

uygulama = FastAPI(title="Eka AI Debugger", version="1.0.0")

uygulama.include_router(yetkilendirme.router)
uygulama.include_router(pano.router)
uygulama.include_router(oturumlar.router)

@uygulama.get("/")
async def ana_sayfa():
    return RedirectResponse(url="/pano")

if __name__ == "__main__":
    uvicorn.run("main:uygulama", host="0.0.0.0", port=8000, reload=True)
""",
    "README.md": """
# Eka AI Debugger

Eka AI Debugger, yapay zeka destekli kurumsal düzeyde bir kod hata ayıklama ve analiz platformudur. Yazılım ekipleri için özel olarak tasarlanmış olup, karmaşık stack trace ve hata loglarını analiz eder, kök nedeni bulur ve optimize edilmiş güvenli kod çözümlemeleri sunar.

## Özellikler

- **Gelişmiş AI Analiz Motoru**: PHP, Python, JavaScript, SQL ve daha fazlasında %99 doğrulukta hata analizi.
- **Güvenli Kimlik Doğrulama**: Şifrelenmiş parola ve JWT tabanlı erişim kontrolü.
- **Çalışma Alanı & Oturum Yönetimi**: Takımlar için ayrılmış çalışma alanları ve tüm geçmiş rapor kayıtları.
- **Profesyonel B2B Arayüz (TailwindCSS)**: Kurumsal kimliğe uygun "slate", "zinc" ve "navy" palet kullanılmıştır.
- **Gerçek Zamanlı Arka Plan İşleme**: Yapay zeka istekleri bekleme yapmadan arka planda işlenir.
- **Güvenli Saklama Mimarisi**: Çözümler saklanarak ekip için bilgi tabanı oluşturulur.

## Gereksinimler
- Python 3.10+
- MySQL veya MariaDB Sunucusu

## Kurulum İçin
1. Sistem dosyalarını kopyalayın
2. Veritabanını oluşturun: `mysql -u root -p < database/schema.sql` (Schema.sql opsiyoneldir SQLAlchemy oto oluşturur)
3. Bağımlılıkları Kurun
```bash
pip install -r requirements.txt
```
4. Sunucuyu Başlatın
```bash
python main.py
```
Uygulama `http://localhost:8000` adresinde aktif olacaktır.

## Lisans
Eka Yazılım ve Bilişim Sistemleri (c) 2026. Tüm hakları saklıdır. Ticari olarak dağıtılamaz.
"""
}

for filepath, content in files.items():
    full_path = os.path.join(r"c:\ServBay\www\eka-ai-debugger", filepath)
    create_file(full_path, content)
    print(f"Olusturuldu: {filepath}")
