import requests

from telegram_config import BOT_TOKEN, CHAT_ID


url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

message = """📰 TEST MESSAGE

Your personal news bot is successfully connected to Telegram! 🤖

Indian Express
+
Llama 3.2
+
Telegram

Everything is ready for the news briefing 🚀
"""

response = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=20
)

print("Status:", response.status_code)
print("Response:")
print(response.text)
