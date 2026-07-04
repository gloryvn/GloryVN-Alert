from flask import Flask, request, jsonify
import requests
import os
import re

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN","8584322410:AAFRp9mb-lzXDFuRQ679TycskX0O6NNfrrE")

# Giữ nguyên danh sách CHAT_IDS mới của bạn
CHAT_IDS = [
    "6851056890",
    "-1004392601315"
]

# Khởi tạo hàng đợi trung chuyển lệnh lưu trên RAM cho MT5
order_queue = []

def send_message(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10
        )
    except Exception as e:
        print(f"❌ Send message failed ({chat_id}): {e}")

def send_telegram(message):
    for chat_id in CHAT_IDS:
        try:
            send_message(chat_id, message)
        except Exception as e:
            print(f"Send failed ({chat_id}): {e}")

def parse_signal_text(text):
    """
    Hàm Regex bóc tách chính xác cấu trúc text từ file chiến lược GloryVN.txt
    """
    try:
        # 1. Tìm hướng lệnh BUY/SELL và mã sản phẩm (Ví dụ: 🟢 BUY GBPUSD hoặc 🔴 SELL EURUSD)
        action_match = re.search(r'(BUY|SELL)\s+([A-Z0-9_\.]+)', text, re.IGNORECASE)
        
        # 2. Tìm các mức giá dựa theo ký tự đặc trưng 📍 Entry, 🛑 SL, và mục tiêu TP1
        entry_match = re.search(r'📍\s*Entry:\s*([0-9\.]+)', text)
        sl_match = re.search(r'🛑\s*SL:\s*([0-9\.]+)', text)
        tp1_match = re.search(r'TP1:\s*([0-9\.]+)', text)
        
        if action_match:
            action = action_match.group(1).lower()  # "buy" hoặc "sell"
            symbol = action_match.group(2).upper()  # Ví dụ: "GBPUSD"
            entry = float(entry_match.group(1)) if entry_match else 0.0
            sl = float(sl_match.group(1)) if sl_match else 0.0
            tp = float(tp1_match.group(1)) if tp1_match else 0.0
            
            return {
                "symbol": symbol,
                "action": action,
                "entry": entry,
                "sl": sl,
                "tp": tp
            }
    except Exception as e:
        print(f"⚠️ Lỗi bóc tách chuỗi văn bản tín hiệu: {e}")
    return None

@app.route("/")
def home():
    return "Webhook & MT5 Bridge System Online"

# Webhook nhận tín hiệu từ TradingView gửi sang
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        message = request.get_data(as_text=True)

        if not message:
            message = "Webhook received"

        # Phân luồng: Auto Bot Signal chỉ vào queue, Telegram signal làm cả hai
        if "Auto Bot Signal" in message:
            parsed_order = parse_signal_text(message)
            if parsed_order:
                order_queue.append(parsed_order)
                print(f"🤖 Đã nạp lệnh AUTO BOT vào hàng đợi MT5: {parsed_order}")
            else:
                print("ℹ️ Auto Bot signal không chứa cấu trúc lệnh hợp lệ.")
        else:
            # 1. Gửi tin nhắn đến toàn bộ danh sách nhóm Telegram
            send_telegram(message)

            # 2. Phân tích và nạp vào hàng đợi cho MT5
            parsed_order = parse_signal_text(message)
            if parsed_order:
                order_queue.append(parsed_order)
                print(f"📥 Đã nạp lệnh mới vào hàng đợi MT5: {parsed_order}")
            else:
                print("ℹ️ Nhận được thông báo nhưng không chứa cấu trúc lệnh trade hợp lệ.")

        return "OK", 200

    except Exception as e:
        print(e)
        return "ERROR", 500

# API End-point dành riêng cho Bot EA trên MT5 kết nối lên lấy lệnh (Polling)
@app.route("/get-order", methods=["GET"])
def get_order():
    # Nếu trong hàng đợi có lệnh mới chưa xử lý
    if len(order_queue) > 0:
        next_order = order_queue.pop(0)  # Lấy lệnh cũ nhất ra xử lý và xóa khỏi hàng đợi
        
        # --- ĐOẠN CODE TỰ ĐỘNG KHẮC PHỤC LỖI DUÔI "m" CỦA SÀN EXNESS ---
        symbol = next_order["symbol"]
        # Nếu tài khoản của bạn dùng đuôi m (như XAUUSDm, EURUSDm) thì tự động chèn thêm vào
        if not symbol.endswith("m"):
            symbol = symbol + "m"
        # -------------------------------------------------------------
        
        return jsonify({
            "has_order": True,
            "symbol": symbol,         # Sẽ trả về XAUUSDm thay vì XAUUSD
            "action": next_order["action"],
            "sl": next_order["sl"],
            "tp": next_order["tp"]
        }), 200
        
    # Nếu không có lệnh nào trong hàng đợi
    return jsonify({"has_order": False}), 200

# Webhook tương tác ngược từ phía Telegram của bạn
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
                "✅ Bot đã kết nối thành công.\nBạn sẽ nhận được thông báo từ webhook và lệnh đã sẵn sàng cấp cho MT5."
            )

        return "OK", 200

    except Exception as e:
        print(e)
        return "ERROR", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)