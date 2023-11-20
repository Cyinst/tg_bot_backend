import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME

logger = logging.getLogger(__name__)


async def wake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = []
    for arg in context.args:
        if f"@{BOT_NAME}" in arg:
            continue
        else:
            args.append(arg)

    print(args)
    ticket_payment = args[0]
    if type(ticket_payment, float) or type(ticket_payment, int):
        await update.message.reply_text(text=f"Wake Success.")
    else:
        await update.message.reply_text(text=f"Wake Failed. Please Check Your Input Format! Example: /wake @{BOT_NAME} 0.08")
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=f"summary: {text}")


handler = CommandHandler('wake', wake)