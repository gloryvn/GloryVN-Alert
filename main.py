from flask import Flask, request
import requests
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Webhook Online"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    print(data)
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)