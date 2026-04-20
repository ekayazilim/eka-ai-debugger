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