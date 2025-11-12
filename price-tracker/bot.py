import os
import discord
import requests
from discord.ext import tasks
from discord import app_commands
from dotenv import load_dotenv
import re


# Load .env variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
HALAL_CRYPTOS_CHANNEL_ID = int(os.getenv("HALAL_CRYPTOS_CHANNEL_ID"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 900))  # 15min default

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

API_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = ["bitcoin", "ethereum", "solana"]


def clean_text(text: str) -> str:
    text = re.sub(r"<a?:\w+:\d+>", "", text)  # Discord custom emojis
    text = re.sub(r"[\U0001F600-\U0001F64F"
                  r"\U0001F300-\U0001F5FF"
                  r"\U0001F680-\U0001F6FF"
                  r"\U0001F1E0-\U0001F1FF"
                  r"\u2600-\u26FF\u2700-\u27BF]+", "", text, flags=re.UNICODE)
    text = text.replace("**", "")  # remove bold markdown
    text = text.strip()
    return text


def get_prices():
    params = {
        "ids": ",".join(COINS),
        "vs_currencies": "usd,eur",
        "include_24hr_change": "true"
    }
    response = requests.get(API_URL, params=params)
    data = response.json()
    return {
        "BTC_USD": data["bitcoin"]["usd"],
        "BTC_EUR": data["bitcoin"]["eur"],
        "BTC_CHANGE": data["bitcoin"]["usd_24h_change"],
        "ETH_USD": data["ethereum"]["usd"],
        "ETH_EUR": data["ethereum"]["eur"],
        "ETH_CHANGE": data["ethereum"]["usd_24h_change"],
        "SOL_USD": data["solana"]["usd"],
        "SOL_EUR": data["solana"]["eur"],
        "SOL_CHANGE": data["solana"]["usd_24h_change"],
    }


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    await tree.sync()
    update_prices.start()


@tasks.loop(seconds=UPDATE_INTERVAL)
async def update_prices():
    channel = client.get_channel(CHANNEL_ID)
    prices = get_prices()

    msg = (
        f"🪙 **Cours des principales cryptos (Spot - conforme à la Sharia)**\n"
        f"\n💰 **BTC**: ${prices['BTC_USD']:,} / {prices['BTC_EUR']:,}€ "
        f"({prices['BTC_CHANGE']:.2f}% sur 24h)\n\n"
        f"💎 **ETH**: ${prices['ETH_USD']:,} / {prices['ETH_EUR']:,}€ "
        f"({prices['ETH_CHANGE']:.2f}% sur 24h)\n\n"
        f"🔥 **SOL**: ${prices['SOL_USD']:,} / {prices['SOL_EUR']:,}€ "
        f"({prices['SOL_CHANGE']:.2f}% sur 24h)\n\n"
        f"_Mise à jour automatique toutes les {UPDATE_INTERVAL//60} minutes._"
    )

    # Clear previous bot messages for a clean look
    async for message in channel.history(limit=10):
        if message.author == client.user:
            await message.delete()

    await channel.send(msg)

# ✅ Slash Command: /ruling


@tree.command(name="ruling",
              description="Check the ruling of a specific coin")
async def ruling(interaction: discord.Interaction, coin: str):
    await interaction.response.defer(thinking=True, ephemeral=True)
    channel = client.get_channel(HALAL_CRYPTOS_CHANNEL_ID)

    if not channel:
        await interaction.followup.send("❌ Channel not found.")
        return

    coin_lower = coin.lower()
    found_messages = []

    async for message in channel.history(limit=1000):  # adjust limit if needed
        lines = message.content.splitlines()
        if len(lines) < 2:
            continue

        coin_name = clean_text(lines[0]).lower()
        coin_symbol = clean_text(lines[1]).lower()

        if coin_lower == coin_name or coin_lower == coin_symbol:
            found_messages.append(message)

    if not found_messages:
        await interaction.followup.send(f"🔍 No coin found: **{coin}**.")
        return

    response = "\n".join(
        [f"[{msg.content[:50]}...]"
         f"({msg.jump_url})" for msg in found_messages[:5]]
    )

    await interaction.followup.send(f"✅ Found {len(found_messages)}"
                                    f" result(s):\n{response}")


# ✅ Slash Command: /price
@tree.command(name="price",
              description="Get the current price of any cryptocurrency")
async def price(interaction: discord.Interaction, coin: str):
    await interaction.response.defer(ephemeral=True)
    coin = coin.lower()

    params = {
        "symbols": coin,
        "vs_currencies": "usd,eur",
        "include_24hr_change": "true"
    }
    r = requests.get(API_URL, params=params)

    if r.status_code != 200 or not r.json() or coin not in r.json():
        await interaction.followup.send(f"❌ Coin not found: `{coin}`")
        return

    try:
        data = r.json()[coin]
        usd = data["usd"]
        eur = data["eur"]
        change = data.get("usd_24h_change", 0.0)
        change_rounded = f"{change:.2f}"
    except Exception as e:
        print("Exception occured", str(e))
        await interaction.followup.send(f"❌ Coin not found: `{coin}`")
        return

    await interaction.followup.send(
        f"📈 **{coin.upper()}**\n"
        f"💰 ${usd:,} / {eur:,}€\n"
        f"📊 Changement 24h : {change_rounded}%\n\n"
        f"💬 *Spot market only — conforme à la"
        " Sharia (pas de leverage ni futures).*"
    )


client.run(TOKEN)
