from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Chỉ BOT_TOKEN lấy từ biến môi trường
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Danh sách Chat ID nhận thông báo
CHAT_IDS = [
    "-5091908465",
    "-3976180576",
]

def send_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message
                },
                timeout=10
            )
        except Exception as e:
            print(f"Send failed ({chat_id}): {e}")

@app.route("/")
def home():
    return "Webhook Online"

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)