from google import genai

from job_search_automation.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

for model in MODELS:
    print("=" * 80)
    print(f"Testing: {model}")

    try:
        response = client.models.generate_content(
            model=model,
            contents="Reply with ONLY OK",
        )

        print("SUCCESS")
        print(response.text)

    except Exception as e:
        print("FAILED")
        print(type(e).__name__)
        print(e)