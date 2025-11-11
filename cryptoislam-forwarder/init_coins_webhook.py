import json
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ───────────────────────────────────────────────
WEBHOOK_URL = os.getenv("WEBHOOK_HALAL_CRYPTOS_URL")
JSON_FILE = "coins.json"
DEFAULT_DELAY = 1.5
# ──────────────────────────────────────────────────────────


def send_message(coin):
    photo_path = coin.get("photo")
    coin_name = coin.get("coin")
    coin_symbol = coin.get("coin_sym")
    judgement = coin.get("judgement")
    source = coin.get("source")

    # Build message text
    message = f"💰 **{coin_name}**\n🔹 **{coin_symbol}**"
    if judgement:
        message += f"\n⚖️ **Judgment:** {judgement}"
    if source:
        message += f"\n🔗 Source: <{source}>"

    # Prepare file if photo exists
    files = None
    if os.path.exists(photo_path):
        files = {"file": open(photo_path, "rb")}

    # Send the message
    data = {"content": message}
    response = requests.post(WEBHOOK_URL, data=data, files=files)

    if response.status_code == 200:
        print(f"✅ Sent: {coin_name}")
    else:
        print(
            f"❌ Failed for {coin_name} ({response.status_code}):"
            f" {response.text}")

    # Close file if opened
    if files:
        files["file"].close()

    time.sleep(DEFAULT_DELAY)


def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        coins = json.load(f)

    for coin in coins:
        send_message(coin)


if __name__ == "__main__":
    main()
