import os

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())

files = {
    "database/schema.sql": """
CREATE DATABASE IF NOT EXISTS eka_ai_debugger CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eka_ai_debugger;

-- Şemalar SQLAlchemy ile otomatik olarak oluşturulabilir.
-- Güvenlik amacıyla bu dosya ham yedeklemeler veya manuel CI/CD entegrasyonu için sağlanmıştır.
""",
    "database/seed.sql": """
USE eka_ai_debugger;
INSERT INTO kullanicilar (ad_soyad, eposta, sifre_hash, rol) VALUES ('Admin Eka', 'admin@eka.com', '$2b$12$z2Z3.Qz0Z...', 'admin');
INSERT INTO calisma_alanlari (isim, sahip_id) VALUES ('Eka Kurumsal', 1);
""",
    "app/routers/bilgi_tabani.py": """
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import veritabani_al
from app.routers.pano import mevcut_kullanici
from app.models.base import IstemeSablonu

router = APIRouter(prefix="/bilgi-tabani", tags=["BilgiTabani"])
sablonlar = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def bilgi_tabani_sayfasi(request: Request, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    return sablonlar.TemplateResponse("knowledge/index.html", {"request": request, "kullanici": kullanici})
""",
    "app/routers/ayarlar.py": """
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import veritabani_al
from app.routers.pano import mevcut_kullanici

router = APIRouter(prefix="/ayarlar", tags=["Ayarlar"])
sablonlar = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def ayarlar_sayfasi(request: Request, vt: Session = Depends(veritabani_al)):
    kullanici = mevcut_kullanici(request, vt)
    if not kullanici:
        return RedirectResponse(url="/yetkilendirme/giris")
    return sablonlar.TemplateResponse("settings/index.html", {"request": request, "kullanici": kullanici})
""",
    "app/templates/knowledge/index.html": """
{% extends "base.html" %}
{% block baslik %}Bilgi Tabanı{% endblock %}
{% block icerik %}
<div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
    <div class="px-6 py-12 text-center bg-white">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4 p-8">
            <i class="fa-solid fa-book-open text-2xl text-slate-400"></i>
        </div>
        <h4 class="text-slate-800 font-medium mb-1">Kurumsal Bilgi Tabanı</h4>
        <p class="text-sm text-slate-500 mb-6">Geçmiş çözüm kayıtları burada kütüphane olarak listelenecektir.</p>
    </div>
</div>
{% endblock %}
""",
    "app/templates/settings/index.html": """
{% extends "base.html" %}
{% block baslik %}Sistem Ayarları{% endblock %}
{% block icerik %}
<div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
    <div class="px-6 py-12 text-center bg-white">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4 p-8">
            <i class="fa-solid fa-cogs text-2xl text-slate-400"></i>
        </div>
        <h4 class="text-slate-800 font-medium mb-1">Hesap & Prompt Yönetimi</h4>
        <p class="text-sm text-slate-500 mb-6">API Anahtarları, Promptları ve Profil bilgilerinizi bu sekmeden yapılandıracaksınız.</p>
    </div>
</div>
{% endblock %}
"""
}

main_icerigi = """
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from core.database import motor, Taban
from app.routers import yetkilendirme, pano, oturumlar, bilgi_tabani, ayarlar

Taban.metadata.create_all(bind=motor)

uygulama = FastAPI(title="Eka AI Debugger", version="1.0.0")

uygulama.include_router(yetkilendirme.router)
uygulama.include_router(pano.router)
uygulama.include_router(oturumlar.router)
uygulama.include_router(bilgi_tabani.router)
uygulama.include_router(ayarlar.router)

@uygulama.get("/")
async def ana_sayfa():
    return RedirectResponse(url="/pano")

if __name__ == "__main__":
    uvicorn.run("main:uygulama", host="0.0.0.0", port=8000, reload=True)
"""
files['main.py'] = main_icerigi.strip()

for filepath, content in files.items():
    full_path = os.path.join(r"c:\ServBay\www\eka-ai-debugger", filepath)
    create_file(full_path, content)
    print(f"Olusturuldu: {filepath}")
