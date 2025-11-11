import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_HALAL_CRYPTOS_URL = os.getenv("WEBHOOK_HALAL_CRYPTOS_URL")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "468879302"))

# ────────────────────────────────────────────────
# Send a coin message to Discord webhook
# ────────────────────────────────────────────────


def send_to_discord(photo_path, coin_name, coin_symbol, source,
                    judgement=None):
    message = f"💰 **{coin_name}**\n🔹 **{coin_symbol}**"
    if judgement:
        message += f"\n⚖️ **Judgment:** {judgement}"
    if source:
        message += f"\n🔗 Source: <{source}>"

    files = None
    if photo_path and os.path.exists(photo_path):
        files = {"file": open(photo_path, "rb")}

    data = {"content": message}
    response = requests.post(WEBHOOK_HALAL_CRYPTOS_URL, data=data, files=files)
    if response.status_code == 200:
        print(f"✅ Sent {coin_name} to Discord")
    else:
        print(f"❌ Failed ({response.status_code}): {response.text}")

    if files:
        files["file"].close()


# ────────────────────────────────────────────────
# Handle forwarded Telegram messages
# ────────────────────────────────────────────────
async def handle_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg:
        return

    # 🚫 Restrict access
    user_id = msg.from_user.id
    if user_id != ALLOWED_USER_ID:
        await msg.reply_text("❌ You’re not authorized to use this bot.")
        return

    photo_path = None
    if msg.photo:
        photo = msg.photo[-1]
        file = await photo.get_file()
        photo_path = f"photo_{msg.message_id}.jpg"
        await file.download_to_drive(photo_path)

    text = msg.caption or msg.text or ""
    lines = text.splitlines()
    coin_name = lines[0].strip() if len(lines) >= 1 else "Unknown"
    coin_symbol = lines[1].strip() if len(lines) >= 2 else ""
    source = next((word for word in text.split() if "t.me/" in word), None)

    send_to_discord(photo_path, coin_name, coin_symbol, source)

    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

    await msg.reply_text(f"✅ Sent {coin_name} to Discord!")


if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_forward))
    print("🤖 Bot running...")
    app.run_polling()
