import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME

logger = logging.getLogger(__name__)


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/predict ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    msg_time = update.effective_message.date
    # TODO: text交给AI进行文本理解, time进行过期判断
    await update.message.reply_text(text=f"Predict Success!")


handler = CommandHandler('predict', predict)