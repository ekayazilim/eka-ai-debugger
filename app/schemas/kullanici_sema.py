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