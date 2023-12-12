import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
from binascii import a2b_hex

from wallet import wallet
from db.db import DB
from env import *

logger = logging.getLogger(__name__)

PUSH_ROUTES = range(1)

channel_id = -4016425542


async def push_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # TODO 运营人员权限检测
    text = "Please send your post."
    await update.message.reply_text(text, parse_mode='html')
    return PUSH_ROUTES


async def push_channel_overview_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.effective_message.text
    with open("channel_overview.txt", 'w') as f:
        f.write(text)
    await update.effective_message.reply_text("Push Success.")
    return ConversationHandler.END


async def push_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global channel_id
    await update._bot.copy_message(chat_id=channel_id, from_chat_id=update.effective_chat.id, message_id=update.effective_message.id)
    query = update.callback_query
    await update.effective_message.reply_text("Push Success.")
    return ConversationHandler.END


async def push_top_groups_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.effective_message.text
    with open("top_groups.txt", 'w') as f:
        f.write(text)
    await update.effective_message.reply_text("Push Success.")
    return ConversationHandler.END


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    
    user = update.effective_user
    logger.info("User %s canceled the conversation.", user.username)

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="Push Close.")
    else:
        await update.message.reply_text(text="Push Close.")

    return ConversationHandler.END


push_channel_handler = ConversationHandler(
    entry_points=[CommandHandler("push_channel", push_cmd)],
    states={
        PUSH_ROUTES: [
            CommandHandler("cancel", end),
            MessageHandler(filters.TEXT, push_to_channel)
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)

push_channel_overview_handler = ConversationHandler(
    entry_points=[CommandHandler("push_channel_overview", push_cmd)],
    states={
        PUSH_ROUTES: [
            CommandHandler("cancel", end),
            MessageHandler(filters.TEXT, push_channel_overview_and_save)
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)

push_top_groups_handler = ConversationHandler(
    entry_points=[CommandHandler("push_top_groups", push_cmd)],
    states={
        PUSH_ROUTES: [
            CommandHandler("cancel", end),
            MessageHandler(filters.TEXT, push_top_groups_and_save)
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)