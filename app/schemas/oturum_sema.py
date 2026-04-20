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