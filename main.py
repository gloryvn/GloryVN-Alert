from flask import Flask, request
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHAT_IDS = [
    "6851056890",
    "-1003976180576",
    "-5091908465"
]

def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=10
    )

def send_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            send_message(chat_id, message)
        except Exception as e:
            print(f"Send failed ({chat_id}): {e}")

@app.route("/")
def home():
    return "Webhook Online"

# Webhook của TradingView hoặc dịch vụ khác
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        message = request.get_data(as_text=True)

        if not message:
            message = "Webhook received"

        send_telegram(message)

        return "OK", 200

    except Exception as e:
        print(e)
        return "ERROR", 500

# Webhook Telegram
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()

        if not data or "message" not in data:
            return "OK", 200

        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text == "/start":
            send_message(
                chat_id,
                "✅ Bot đã kết nối thành công.\nBạn sẽ nhận được thông báo từ webhook."
            )

        return "OK", 200

    except Exception as e:
        print(e)
        return "ERROR", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)