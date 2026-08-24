import requests
from job_search_automation.config import settings

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{settings.GEMINI_MODEL}:generateContent"
)

params = {
    "key": settings.GEMINI_API_KEY,
}

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Say hello in one sentence."
                }
            ]
        }
    ]
}

print("=" * 80)
print("URL:")
print(url)
print("=" * 80)
print("Model:", settings.GEMINI_MODEL)
print("Key Length:", len(settings.GEMINI_API_KEY))
print("=" * 80)

response = requests.post(
    url,
    params=params,
    json=payload,
    timeout=30,
)

print("Status:", response.status_code)
print(response.text)