import os
import asyncio
import threading

import discord

from trader.discord_orders import send_order
from trader.discord_storage import (
    sync_memory,
    sync_state,
    sync_model,
)


TOKEN = os.getenv("DISCORD_BOT_TOKEN")


if not TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN belum diset."
    )


class DiscordBridge:

    def __init__(self):

        self.client = discord.Client(
            intents=discord.Intents.default()
        )

        self.loop = None
        self.thread = None
        self.ready = threading.Event()

        @self.client.event
        async def on_ready():

            self.loop = asyncio.get_running_loop()

            print(
                f"Discord bridge aktif: "
                f"{self.client.user}"
            )

            self.ready.set()

    def start(self):

        if self.thread is not None:
            return

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()

        self.ready.wait(
            timeout=30
        )

    def _run(self):

        asyncio.run(
            self.client.start(TOKEN)
        )

    def _run_async(self, coroutine):

        if self.loop is None:
            return False

        try:

            future = asyncio.run_coroutine_threadsafe(
                coroutine,
                self.loop
            )

            future.result(
                timeout=30
            )

            return True

        except Exception as e:

            print(
                f"Discord bridge error: {e}"
            )

            return False

    def order(
        self,
        order_type,
        pair,
        price,
        score,
        reasons=None
    ):

        if not self.ready.wait(
            timeout=30
        ):

            print(
                "Discord belum siap."
            )

            return False

        return self._run_async(
            send_order(
                self.client,
                order_type,
                pair,
                price,
                score,
                reasons
            )
        )

    def sync_memory(self):

        if not self.ready.wait(
            timeout=30
        ):
            return False

        return self._run_async(
            sync_memory(
                self.client
            )
        )

    def sync_state(self):

        if not self.ready.wait(
            timeout=30
        ):
            return False

        return self._run_async(
            sync_state(
                self.client
            )
        )

    def sync_model(self):

        if not self.ready.wait(
            timeout=30
        ):
            return False

        return self._run_async(
            sync_model(
                self.client
            )
        )


discord_bridge = DiscordBridge()
