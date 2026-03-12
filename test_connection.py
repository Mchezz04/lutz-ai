import requests

try:
    response = requests.get("https://www.google.com", timeout=5)
    print("✅ Интернет работает!")
except Exception as e:
    print(f"❌ Нет доступа к интернету: {e}")