import os
import discord
import requests
from discord.ext import tasks
from discord import app_commands

# Load .env variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 900))  # 15min default

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

API_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = ["bitcoin", "ethereum", "solana"]


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
        f"🪙 **Cours des principales cryptos (Spot - conforme à la Sharia)**\n\n"
        f"💰 **BTC**: ${prices['BTC_USD']:,} / {prices['BTC_EUR']:,}€ "
        f"({prices['BTC_CHANGE']:.2f}% sur 24h)\n\n"
        f"💎 **ETH**: ${prices['ETH_USD']:,} / {prices['ETH_EUR']:,}€ "
        f"({prices['ETH_CHANGE']:.2f}% sur 24h)\n\n"
        f"🔥 **SOL**: ${prices['SOL_USD']:,} / {prices['SOL_EUR']:,}€ "
        f"({prices['SOL_CHANGE']:.2f}% sur 24h)\n\n"
        f"_Mise à jour automatique toutes les {UPDATE_INTERVAL // 60} minutes._"
    )

    # Clear previous bot messages for a clean look
    async for message in channel.history(limit=10):
        if message.author == client.user:
            await message.delete()

    await channel.send(msg)


# ✅ Slash Command: /price
@tree.command(name="price", description="Get the current price of any cryptocurrency")
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

    data = r.json()[coin]
    usd = data["usd"]
    eur = data["eur"]
    change = data.get("usd_24h_change", 0.0)

    await interaction.followup.send(
        f"📈 **{coin.upper()}**\n"
        f"💰 ${usd:,} / {eur:,}€\n"
        f"📊 Changement 24h : {change:.2f}%\n\n"
        f"💬 *Spot market only — conforme à la Sharia (pas de leverage ni futures).*"
    )


client.run(TOKEN)
