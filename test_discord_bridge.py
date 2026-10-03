from trader.discord_bridge import discord_bridge


print("================================")
print("      DISCORD BRIDGE TEST")
print("================================")

discord_bridge.start()

print()
print("Test BUY...")

discord_bridge.order(
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

print()
print("Test SELL...")

discord_bridge.order(
    "SELL",
    "FARTCOIN_IDR",
    3210.0,
    0.7125,
    [
        "take profit tercapai"
    ]
)

print()
print("Test storage memory...")

discord_bridge.sync_memory()

print()
print("================================")
print("        BRIDGE TEST SELESAI")
print("================================")
