import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_chat.send_message(text=await context.bot.export_chat_invite_link(chat_id=-4016425542))

handler = CommandHandler('join', join)