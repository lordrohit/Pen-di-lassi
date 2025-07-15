from telegram import Bot
from dotenv import load_dotenv
import os

# Load .env if you use environment variables
load_dotenv()

# Replace this if not using .env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "PASTE-YOUR-TOKEN-HERE"

bot = Bot(token=BOT_TOKEN)
bot.delete_webhook()

print("✅ Webhook deleted — polling will now work without conflict.")