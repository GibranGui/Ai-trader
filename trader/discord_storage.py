import os
import json
import discord


TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN belum diset."
    )


# Nama channel Discord
CHANNELS = {
    "memory": "ai-memory",
    "state": "ai-state",
    "model": "ai-model",
}


async def get_channel(client, name):

    for guild in client.guilds:

        for channel in guild.text_channels:

            if channel.name == name:
                return channel

    return None


async def delete_old_file(channel, filename):

    async for message in channel.history(
        limit=None
    ):

        for attachment in message.attachments:

            if attachment.filename == filename:

                try:
                    await message.delete()

                except Exception as e:

                    print(
                        "Gagal menghapus file lama:",
                        e
                    )


async def upload_file(
    client,
    channel_name,
    filepath,
    filename
):

    channel = await get_channel(
        client,
        channel_name
    )

    if channel is None:

        print(
            f"Channel #{channel_name} "
            "tidak ditemukan."
        )

        return False

    if not os.path.exists(filepath):

        print(
            f"File tidak ditemukan: {filepath}"
        )

        return False

    # Hapus file versi lama
    await delete_old_file(
        channel,
        filename
    )

    # Upload file terbaru
    await channel.send(
        content=f"UPDATE: `{filename}`",
        file=discord.File(
            filepath,
            filename=filename
        )
    )

    print(
        f"Upload berhasil: "
        f"{filename} -> #{channel_name}"
    )

    return True


async def download_latest_file(
    client,
    channel_name,
    filename,
    destination
):

    channel = await get_channel(
        client,
        channel_name
    )

    if channel is None:

        print(
            f"Channel #{channel_name} "
            "tidak ditemukan."
        )

        return False

    async for message in channel.history(
        limit=None
    ):

        for attachment in message.attachments:

            if attachment.filename == filename:

                os.makedirs(
                    os.path.dirname(destination),
                    exist_ok=True
                )

                await attachment.save(
                    destination
                )

                print(
                    f"Download berhasil: "
                    f"{filename}"
                )

                return True

    print(
        f"File {filename} "
        f"belum ada di #{channel_name}"
    )

    return False


async def sync_memory(client):

    return await upload_file(
        client,
        CHANNELS["memory"],
        "data/ai_memory.json",
        "ai_memory.json"
    )


async def sync_state(client):

    return await upload_file(
        client,
        CHANNELS["state"],
        "data/ai_state.json",
        "ai_state.json"
    )


async def sync_model(client):

    return await upload_file(
        client,
        CHANNELS["model"],
        "models/model.json",
        "model.json"
    )


async def restore_memory(client):

    return await download_latest_file(
        client,
        CHANNELS["memory"],
        "ai_memory.json",
        "data/ai_memory.json"
    )


async def restore_state(client):

    return await download_latest_file(
        client,
        CHANNELS["state"],
        "ai_state.json",
        "data/ai_state.json"
    )


async def restore_model(client):

    return await download_latest_file(
        client,
        CHANNELS["model"],
        "model.json",
        "models/model.json"
    )
