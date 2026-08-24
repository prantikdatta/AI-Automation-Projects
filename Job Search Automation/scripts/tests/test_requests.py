import requests

try:
    r = requests.get("https://google.com", timeout=10)
    print("Status:", r.status_code)
except Exception as e:
    print(type(e).__name__)
    print(e)