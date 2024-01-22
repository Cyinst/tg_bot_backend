import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
from binascii import a2b_hex

from wallet import wallet
from db.db import DB
from env import *

logger = logging.getLogger(__name__)

PUSH_ROUTES, CHANNEL_ROUTES = range(2)


def check_ops(user_id):
    return user_id in OPS


async def push_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # 运营人员权限检测
    if not check_ops(update.effective_user.id):
        await update.message.reply_text("Only Operator.", parse_mode='html')
        return ConversationHandler.END
    text = "Please send your post."
    await update.message.reply_text(text, parse_mode='html')
    return PUSH_ROUTES


async def push_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # 运营人员权限检测
    if not check_ops(update.effective_user.id):
        await update.message.reply_text("Only Operator.", parse_mode='html')
        return ConversationHandler.END
    text = "Please send the channel id:"
    await update.message.reply_text(text, parse_mode='html')
    return CHANNEL_ROUTES


async def wait_for_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    text = "Please send your post."
    
    try:
        channel_id = int(update.effective_message.text)
        payload = {
            f"push+{update.effective_user.id}": channel_id,
        }
        context.bot_data.update(payload)
    except:
        await update.message.reply_text(f"Channel id err: {update.effective_message.text}", parse_mode='html')
        return ConversationHandler.END
    await update.message.reply_text(text, parse_mode='html')
    return PUSH_ROUTES


async def push_channel_overview_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.effective_message

    html_text = convert_to_html(message)

    with open("channel_overview.txt", 'w') as f:
        f.write(html_text)
    print(f"user id: {update.effective_user.id}")
    # print(f"overview: {text}")
    await update.effective_message.reply_text("Push Success.")
    return ConversationHandler.END


async def push_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    channel_id = context.bot_data.get(f"push+{update.effective_user.id}", None)
    context.bot_data.pop(f"push+{update.effective_user.id}", None)
    if channel_id:
        print(f"channel_id: {channel_id}")
        try:
            await update._bot.copy_message(chat_id=channel_id, from_chat_id=update.effective_chat.id, message_id=update.effective_message.id)
            query = update.callback_query
            await update.effective_message.reply_text("Push Success.")
            return ConversationHandler.END
        except Exception as e:
            await update.message.reply_text(f"push err.", parse_mode='html')
            logger.exception(e)
            return ConversationHandler.END
    else:
        await update.message.reply_text(f"Channel id not found.", parse_mode='html')
        return ConversationHandler.END


async def push_top_groups_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.effective_message.text
    with open("top_groups.txt", 'w') as f:
        f.write(text)
    await update.effective_message.reply_text("Push Success.")
    return ConversationHandler.END


async def push_my_groups_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.effective_message.text
    with open("my_groups.txt", 'w') as f:
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


def convert_to_html(message):
    if not message.entities:
        return message.text

    result = ""
    last_offset = 0
    for entity in message.entities:
        start = entity.offset
        end = entity.offset + entity.length
        if entity.type == "url":
            url = message.text[start:end]
            result += message.text[last_offset:start] + f'<a href="{url}">{url}</a>'
        elif entity.type == "text_link":
            linked_text = message.text[start:end]
            result += message.text[last_offset:start] + f'<a href="{entity.url}">{linked_text}</a>'
        last_offset = end

    result += message.text[last_offset:]
    return result


def convert_to_markdown(message):
    if not message.entities:
        return message.text

    result = ""
    last_offset = 0
    for entity in message.entities:
        start = entity.offset
        end = entity.offset + entity.length
        if entity.type == "url":
            url = message.text[start:end]
            result += message.text[last_offset:start] + f'[{url}]({url})'
        elif entity.type == "text_link":
            linked_text = message.text[start:end]
            result += message.text[last_offset:start] + f'[{linked_text}]({entity.url})'
        last_offset = end

    result += message.text[last_offset:]
    return result


push_channel_handler = ConversationHandler(
    entry_points=[CommandHandler("push_channel", push_channel_cmd)],
    states={
        PUSH_ROUTES: [
            CommandHandler("cancel", end),
            MessageHandler(filters.TEXT, push_to_channel)
        ],
        CHANNEL_ROUTES: [
            CommandHandler("cancel", end),
            MessageHandler(filters.TEXT, wait_for_post)
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

push_my_groups_handler = ConversationHandler(
    entry_points=[CommandHandler("push_my_groups", push_cmd)],
    states={
        PUSH_ROUTES: [
            CommandHandler("cancel", end),
            MessageHandler(filters.TEXT, push_my_groups_and_save)
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)