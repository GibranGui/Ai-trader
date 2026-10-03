import discord


OPEN_CHANNEL = "open-orders"
CLOSE_CHANNEL = "close-orders"

OPEN_WEBHOOK_NAME = "AI-Trader-Open"
CLOSE_WEBHOOK_NAME = "AI-Trader-Close"


async def get_channel(client, channel_name):

    for guild in client.guilds:

        for channel in guild.text_channels:

            if channel.name == channel_name:
                return channel

    return None


async def get_or_create_webhook(
    channel,
    webhook_name
):

    webhooks = await channel.webhooks()

    for webhook in webhooks:

        if webhook.name == webhook_name:
            return webhook

    return await channel.create_webhook(
        name=webhook_name,
        reason="AI Trader order notification"
    )


async def send_order(
    client,
    order_type,
    pair,
    price,
    score,
    reasons=None
):

    if order_type.upper() == "BUY":

        channel_name = OPEN_CHANNEL
        webhook_name = OPEN_WEBHOOK_NAME
        title = "🟢 PAPER BUY"

    elif order_type.upper() == "SELL":

        channel_name = CLOSE_CHANNEL
        webhook_name = CLOSE_WEBHOOK_NAME
        title = "🔴 PAPER SELL"

    else:

        return False

    channel = await get_channel(
        client,
        channel_name
    )

    if channel is None:

        print(
            f"Channel #{channel_name} tidak ditemukan."
        )

        return False

    webhook = await get_or_create_webhook(
        channel,
        webhook_name
    )

    reason_text = ""

    if reasons:

        reason_text = "\n".join(
            f"• {reason}"
            for reason in reasons
        )

    embed = discord.Embed(
        title=title,
        description=f"**{pair.upper()}**",
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="Harga",
        value=f"Rp{price:,.8f}",
        inline=False
    )

    embed.add_field(
        name="AI Score",
        value=f"{score * 100:.2f}%",
        inline=True
    )

    if reason_text:

        embed.add_field(
            name="Reason",
            value=reason_text[:1024],
            inline=False
        )

    embed.set_footer(
        text="AI Trader • PAPER TRADING"
    )

    await webhook.send(
        embed=embed,
        username="AI Trader",
        avatar_url=None
    )

    print(
        f"Discord order notification: "
        f"{order_type.upper()} {pair}"
    )

    return True
