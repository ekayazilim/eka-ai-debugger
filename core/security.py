from base64 import urlsafe_b64encode
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
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


def _fernet_uret() -> Fernet:
    anahtar_ozeti = sha256(ayarlar.etkili_sifreleme_anahtari.encode("utf-8")).digest()
    return Fernet(urlsafe_b64encode(anahtar_ozeti))


fernet = _fernet_uret()


def metni_sifrele(deger: str) -> str:
    if not deger:
        return ""
    return fernet.encrypt(deger.encode("utf-8")).decode("utf-8")



def metni_coz(deger: str) -> str:
    if not deger:
        return ""
    try:
        return fernet.decrypt(deger.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""



def anahtar_maskele(deger: str) -> str:
    if not deger:
        return ""
    if len(deger) <= 8:
        return "*" * len(deger)
    return f"{deger[:4]}{'*' * (len(deger) - 8)}{deger[-4:]}"
