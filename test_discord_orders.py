import os
import asyncio
import discord

from trader.discord_orders import send_order


TOKEN = os.getenv("DISCORD_BOT_TOKEN")


if not TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN belum diset."
    )


class TestBot(discord.Client):

    async def on_ready(self):

        print()
        print("================================")
        print("     DISCORD ORDER TEST")
        print("================================")
        print()

        print("Login sebagai:", self.user)
        print()

        print("Mengirim TEST BUY...")

        await send_order(
            self,
            "BUY",
            "FARTCOIN_IDR",
            3190.0,
            0.8834,
            [
                "harga dekat high",
                "volume tinggi",
                "volatilitas aktif"
            ]
        )

        print("Mengirim TEST SELL...")

        await send_order(
            self,
            "SELL",
            "FARTCOIN_IDR",
            3210.0,
            0.7125,
            [
                "take profit tercapai"
            ]
        )

        print()
        print("================================")
        print("        TEST SELESAI")
        print("================================")
        print()

        await self.close()


intents = discord.Intents.default()

bot = TestBot(
    intents=intents
)

bot.run(TOKEN)
