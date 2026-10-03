import os
import asyncio
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise SystemExit(
        "DISCORD_BOT_TOKEN belum diatur. "
        "Contoh: export DISCORD_BOT_TOKEN='TOKEN'"
    )

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

STRUCTURE = {
    "STORAGE": ["ai-memory", "ai-state", "ai-model"],
    "OPEN ORDERS": ["open-orders"],
    "CLOSE ORDERS": ["close-orders"],
    "SYSTEM": ["bot-status"],
}

WEBHOOK_CHANNELS = {
    "open-orders": "AI-OPEN-ORDER",
    "close-orders": "AI-CLOSE-ORDER",
}

async def find_category(guild, name):
    for category in guild.categories:
        if category.name.lower() == name.lower():
            return category
    return None

async def find_channel(guild, name, category):
    for channel in guild.text_channels:
        if channel.name.lower() == name.lower() and channel.category == category:
            return channel
    return None

async def ensure_webhook(channel, name):
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == name:
            return webhook
    return await channel.create_webhook(name=name)

@bot.event
async def on_ready():
    print(f"Login sebagai: {bot.user}")

    guilds = bot.guilds
    if not guilds:
        print("Bot belum masuk ke server mana pun.")
        await bot.close()
        return

    if len(guilds) > 1:
        print("Bot berada di beberapa server. Menggunakan server pertama.")

    guild = guilds[0]
    print(f"Server: {guild.name}")

    main_category = await find_category(guild, "🤖 AI TRADER")
    if main_category is None:
        main_category = await guild.create_category("🤖 AI TRADER")

    webhook_results = {}

    for category_name, channels in STRUCTURE.items():
        category = await find_category(guild, category_name)
        if category is None:
            category = await guild.create_category(category_name)

        for channel_name in channels:
            channel = await find_channel(guild, channel_name, category)
            if channel is None:
                channel = await guild.create_text_channel(
                    channel_name,
                    category=category
                )

            if channel_name in WEBHOOK_CHANNELS:
                webhook = await ensure_webhook(
                    channel,
                    WEBHOOK_CHANNELS[channel_name]
                )
                webhook_results[channel_name] = webhook.url

    print("\n=== SERVER SIAP ===")
    print(f"Server ID: {guild.id}")
    print("\nWebhook:")
    for channel, url in webhook_results.items():
        print(f"{channel}: {url}")

    print("\nJANGAN membagikan webhook URL/token bot ke orang lain.")
    await bot.close()

bot.run(TOKEN)
