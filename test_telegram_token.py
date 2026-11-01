import requests
from telegram_config import BOT_TOKEN

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"

response = requests.get(url, timeout=20)

print("Status:", response.status_code)
print("Response:")
print(response.text)
