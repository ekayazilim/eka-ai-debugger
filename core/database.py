from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
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
