# Discord AI Trader Server Template

Discord tidak menyediakan fitur untuk meng-upload ZIP lalu otomatis membuat server.
Template ini dibuat agar server dapat dibangun otomatis menggunakan bot Discord.

## Struktur yang dibuat

🤖 AI TRADER
├── STORAGE
│   ├── ai-memory
│   ├── ai-state
│   └── ai-model
├── OPEN ORDERS
│   └── open-orders
├── CLOSE ORDERS
│   └── close-orders
└── SYSTEM
    └── bot-status

## Cara pakai

1. Buat Discord Application/Bot di Discord Developer Portal.
2. Invite bot ke server dengan permission:
   - Manage Channels
   - Manage Webhooks
   - View Channels
   - Send Messages
   - Attach Files
   - Read Message History
   - Manage Messages
3. Install dependency:
   pip install -r requirements.txt
4. Masukkan token bot:
   Linux/Termux:
   export DISCORD_BOT_TOKEN="TOKEN_BOT_ANDA"
5. Jalankan:
   python setup_server.py
6. Bot akan membuat kategori, channel, dan webhook yang diperlukan.
7. Simpan hasil webhook URL dengan aman. Jangan kirim token bot atau webhook URL ke chat publik.

Catatan:
- Script tidak menghapus channel yang sudah ada.
- Jika struktur sudah ada, script akan mencoba menggunakannya kembali.
- Webhook dibuat hanya jika belum ditemukan webhook dengan nama yang sama.
