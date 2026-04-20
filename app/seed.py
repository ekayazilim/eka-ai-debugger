import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import OturumYerel, Taban, motor
from app.models.base import YapayZekaSaglayicisi

Taban.metadata.create_all(bind=motor)

saglayicilar = [
    {
        "ad": "NVIDIA Build",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "api_key": "YOUR_NVIDIA_API_KEY",
        "modeller": [
            "meta/llama-3.1-8b-instruct",
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-405b-instruct",
            "mistralai/mixtral-8x22b-instruct-v0.1",
            "google/gemma-2-27b-it"
        ]
    },
    {
        "ad": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "YOUR_OPENROUTER_API_KEY",
        "modeller": [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "anthropic/claude-3-haiku",
            "meta-llama/llama-3.1-405b-instruct:free",
            "mistralai/mistral-large-2411",
            "google/gemini-pro-1.5",
            "deepseek/deepseek-chat"
        ]
    },
    {
        "ad": "Hugging Face",
        "base_url": "https://router.huggingface.co/v1",
        "api_key": "YOUR_HUGGINGFACE_API_KEY",
        "modeller": [
            "gpt2",
            "HuggingFaceH4/zephyr-7b-beta",
            "microsoft/phi-2",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        ]
    },
    {
        "ad": "Cloudflare AI",
        "base_url": "https://api.cloudflare.com/client/v4/accounts/adad21f819ba7fa0a6fe478013db4684/ai/v1",
        "api_key": "YOUR_CLOUDFLARE_API_KEY",
        "modeller": [
            "@cf/meta/llama-3-8b-instruct",
            "@cf/meta/llama-3.2-11b-vision-instruct",
            "@cf/black-forest-labs/flux-1-schnell"
        ]
    },
    {
        "ad": "LM Studio (Yerel)",
        "base_url": "http://localhost:1234/v1",
        "api_key": "lm-studio",
        "modeller": [
            "auto"
        ]
    }
]

def seed_db():
    vt = OturumYerel()
    try:
        for veri in saglayicilar:
            mevcut = vt.query(YapayZekaSaglayicisi).filter(YapayZekaSaglayicisi.ad == veri["ad"]).first()
            if mevcut:
                mevcut.base_url = veri["base_url"]
                mevcut.api_key = veri["api_key"]
                mevcut.modeller = json.dumps(veri["modeller"])
                print(f"Güncellendi: {veri['ad']}")
            else:
                yeni = YapayZekaSaglayicisi(
                    ad=veri["ad"],
                    base_url=veri["base_url"],
                    api_key=veri["api_key"],
                    modeller=json.dumps(veri["modeller"])
                )
                vt.add(yeni)
                print(f"Eklendi: {veri['ad']}")
        
        vt.commit()
        print("Tüm veriler başarıyla eklendi/güncellendi.")
    except Exception as e:
        vt.rollback()
        print(f"Hata oluştu: {e}")
    finally:
        vt.close()

if __name__ == "__main__":
    seed_db()
