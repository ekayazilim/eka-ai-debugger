import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.routers import ayarlar, bilgi_tabani, oturumlar, pano, yetkilendirme
from core.database import Taban, motor
from core.migration import ayarlar_semasini_yukselt

Taban.metadata.create_all(bind=motor)
ayarlar_semasini_yukselt()

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
