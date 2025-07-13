import random
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

API_URL = "https://lookup.binlist.net/"

# ---------- Luhn ----------
def luhn_checksum(card_number):
    def digits_of(n): return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_sum = sum(digits[-1::-2])
    even_sum = sum(sum(digits_of(d*2)) for d in digits[-2::-2])
    return (odd_sum + even_sum) % 10

def generate_card(bin_input):
    while True:
        card = bin_input
        while len(card) < 15:
            card += str(random.randint(0, 9))
        for i in range(10):
            check_digit = str(i)
            if luhn_checksum(card + check_digit) == 0:
                return card + check_digit

def generate_cards(bin_input, amount=10):
    cards = []
    for _ in range(amount):
        card = generate_card(bin_input)
        expiry_month = str(random.randint(1, 12)).zfill(2)
        expiry_year = str(random.randint(25, 30))
        cvv = str(random.randint(100, 999))
        cards.append(f"{card} | {expiry_month}/{expiry_year} | {cvv}")
    return cards

# ---------- Bot Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Chào bạn! Gửi lệnh:\n/gen <BIN> để:\n- Tra thông tin BIN\n- Đồng thời sinh thẻ test\n\nVí dụ:\n/gen 515462"
    )

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Nhập BIN. Ví dụ: /gen 515462")
        return

    bin_input = context.args[0]
    if not bin_input.isdigit() or not (6 <= len(bin_input) <= 11):
        await update.message.reply_text("⚠️ BIN phải là số và dài từ 6 đến 11 chữ số.")
        return

    try:
        # Lấy thông tin BIN từ API
        res = requests.get(API_URL + bin_input[:6])
        if res.status_code != 200:
            await update.message.reply_text("❌ Không tìm thấy thông tin BIN.")
            return
        data = res.json()

        bin_info = f"""🔍 **Thông tin BIN: `{bin_input[:6]}`**
💳 Loại thẻ: {data.get('scheme', 'N/A').upper()} - {data.get('type', 'N/A').capitalize()}
🏦 Ngân hàng: {data.get('bank', {}).get('name', 'N/A')}
🌍 Quốc gia: {data.get('country', {}).get('name', 'N/A')} {data.get('country', {}).get('emoji', '')}
"""

        # Luôn sinh thẻ test từ BIN nhập vào
        cards = generate_cards(bin_input, amount=10)
        card_text = "\n".join(cards)

        await update.message.reply_text(f"{bin_info}\n🎴 **Thẻ test:**\n```{card_text}```", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("❗ Có lỗi khi xử lý. Vui lòng thử lại sau.")

# ---------- Khởi tạo bot ----------
app = ApplicationBuilder().token("8011153654:AAGu4cxGjmGw4SEerARME6PPDtSKcE9sE4I").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("gen", gen))

print("🤖 Bot đang chạy...")
app.run_polling()
