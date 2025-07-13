import os
import random
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

API_URL = "https://lookup.binlist.net/"

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Gõ /gen <BIN> để tra cứu và sinh thẻ test.\nVí dụ: /gen 515462")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Cách dùng:\n"
        "/gen <BIN> – tra thông tin và sinh số thẻ\n"
        "VD: /gen 457173\n"
        "BIN là 6–11 chữ số đầu của số thẻ.",
        parse_mode="Markdown"
    )

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Nhập BIN. VD: /gen 457173")
        return

    bin_input = context.args[0]
    if not bin_input.isdigit() or not (6 <= len(bin_input) <= 11):
        await update.message.reply_text("⚠️ BIN không hợp lệ (6–11 số).")
        return

    try:
        res = requests.get(API_URL + bin_input[:6])
        if res.status_code != 200:
            await update.message.reply_text("❌ Không tìm thấy BIN.")
            return
        data = res.json()

        bin_info = f"""🔍 **BIN `{bin_input[:6]}`**
💳 Loại: {data.get('scheme', 'N/A').upper()} - {data.get('type', 'N/A').capitalize()}
🏦 Ngân hàng: {data.get('bank', {}).get('name', 'N/A')}
🌍 Quốc gia: {data.get('country', {}).get('name', 'N/A')} {data.get('country', {}).get('emoji', '')}
"""

        cards = generate_cards(bin_input, amount=10)
        card_text = "\n".join(cards)

        await update.message.reply_text(f"{bin_info}\n🎴 **Thẻ test:**\n```{card_text}```", parse_mode="Markdown")

    except Exception:
        await update.message.reply_text("❗ Có lỗi, thử lại sau.")

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("gen", gen))
app.run_polling()
