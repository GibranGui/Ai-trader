import asyncio
import os
import discord

from trader.discord_storage import (
    sync_memory,
    sync_state,
    sync_model,
    restore_memory,
    restore_state,
    restore_model
)


TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()


class TestBot(discord.Client):

    async def on_ready(self):

        print()
        print("================================")
        print("   DISCORD STORAGE TEST")
        print("================================")
        print()
        print("Login sebagai:", self.user)
        print()

        print("[1] Upload memory...")
        await sync_memory(self)

        print("[2] Upload state...")
        await sync_state(self)

        print("[3] Upload model...")
        await sync_model(self)

        print()
        print("[4] Test restore memory...")
        await restore_memory(self)

        print("[5] Test restore state...")
        await restore_state(self)

        print("[6] Test restore model...")
        await restore_model(self)

        print()
        print("================================")
        print("       TEST SELESAI")
        print("================================")

        await self.close()


bot = TestBot(
    intents=intents
)

bot.run(TOKEN)
