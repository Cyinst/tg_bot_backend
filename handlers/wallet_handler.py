import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
from binascii import a2b_hex, b2a_hex

from wallet import wallet
from env import AES_KEY

logger = logging.getLogger(__name__)

logger.info(f"aes key: {AES_KEY}")

# Stages
START_ROUTES, END_ROUTES = range(2)
VIEW, CREATE, IMPORT, EXPORT, DELETE, END= range(6)
async def wallet_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # TODO:数据库commit
    logger.info(f"wallet id: {update.message.from_user.id}")
    keyboard = [
        [
            InlineKeyboardButton("Create Wallet", callback_data=str(CREATE))
        ],
        [
            InlineKeyboardButton("Import Wallet", callback_data=str(IMPORT))
        ],
        [
            InlineKeyboardButton("Export Wallet", callback_data=str(EXPORT))
        ],
        [
            InlineKeyboardButton("Delete Wallet", callback_data=str(DELETE))
        ],
        [
            InlineKeyboardButton("Exit", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Your wallet address:\n"
    # TODO: 检索数据库
    addrs = []
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    text += "Please choose how to do with your wallet, you can also send command /cancel to cancel current config"
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='html')
    return START_ROUTES


async def view_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Create Wallet", callback_data=str(CREATE))
        ],
        [
            InlineKeyboardButton("Import Wallet", callback_data=str(IMPORT))
        ],
        [
            InlineKeyboardButton("Export Wallet", callback_data=str(EXPORT))
        ],
        [
            InlineKeyboardButton("Delete Wallet", callback_data=str(DELETE))
        ],
        [
            InlineKeyboardButton("Exit", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Your wallet address:\n"
    # TODO: 检索数据库
    addrs = []
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    text += "Please choose how to do with your wallet, you can also send command /cancel to cancel current config"

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return START_ROUTES


async def create_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    # TODO: 检查是否已经有wallet和口令，如果没有设置6位口令
    logger.info(f"user: {update.effective_user.id}")
    logger.info(f"msg id: {update.effective_message.message_id}")
    if False:
        pass
    else:
        # 已经有口令了，新增wallet
        # TODO: 验证口令

        # 口令验证通过，创建私钥和地址
        (key, addr) = wallet.create_wallet(extra=update.effective_message.message_id)
        logger.info(f"pri key must 0x: {key}, addr: {addr}")

        # 加密
        (ciphertext, nonce) = wallet.encrypt_wallet_key(key, AES_KEY)
        logger.info(f"ct: {ciphertext}, nonce: {nonce}")

        # TODO: 存储


        keyboard = [
            [
                InlineKeyboardButton("OK", callback_data=str(VIEW))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=f"Create Wallet Success!\nYour wallet private key: <code>{key}</code>\nYour wallet address: <code>{addr}</code>\n<strong>If you have remembered the key and address, I will hide them!</strong>", reply_markup=reply_markup, parse_mode='html')

        return START_ROUTES


async def import_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(text=f"Please input your private key:", parse_mode='html')

    while True:
        err_text=f"Incorrect private key format! Please input correct private key."
        new_update = await context.bot.get_updates()
        pri_key = new_update.effective_message.text
        if pri_key.startswith("0x"):
            pri_key = pri_key[2:]
        if len(pri_key) == 64:
            try:
                a2b_hex(pri_key)
            except:
                context.bot.send_message(chat_id=update.effective_chat.id, text=err_text)
                continue
            (key, addr) = wallet.import_wallet('0x'+pri_key)
            # TODO: 存储到数据库中

            break
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text=err_text)

        keyboard = [
            [
                InlineKeyboardButton("OK", callback_data=str(VIEW))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        success_text = f"Import Success. Import wallet address:\n<code>{addr}</code>\n<strong>If you confirm the wallet import, please press 'OK'. If you want to cancel this, please send command /cancel!</strong>"
        await query.edit_message_text(text=success_text, parse_mode='html', reply_markup=reply_markup)

    return START_ROUTES


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Finish wallet config!")

    # TODO:数据库commit
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.username)
    await update.message.reply_text(
        "Wallet config canceled!"
    )
    return ConversationHandler.END


handler = ConversationHandler(
    entry_points=[CommandHandler("wallet", wallet_config)],
    states={
        START_ROUTES: [
            CallbackQueryHandler(view_wallet, pattern="^" + str(VIEW) + "$"),
            CallbackQueryHandler(create_wallet, pattern="^" + str(CREATE) + "$"),
            CallbackQueryHandler(import_wallet, pattern="^" + str(IMPORT) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
        ],
        END_ROUTES: [

        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)