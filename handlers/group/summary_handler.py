import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME

logger = logging.getLogger(__name__)


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/summary ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    await update.message.reply_text(text=f"summary: {text}")
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=f"summary: {text}")


handler = CommandHandler('summary', summary)