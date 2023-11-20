import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
from binascii import a2b_hex

from wallet import wallet
from db.db import DB
from env import *

logger = logging.getLogger(__name__)

logger.info(f"aes key: {AES_KEY}")

msg_db_inst_cache = {}
export_addrs_cache = {}

# Stages
WALLET_ROUTES, END_ROUTES, MENU_ROUTES, WALLET_NUM_ROUTES, WALLET_DELETE_ROUTES, WALLET_SET_DEFAULT_ROUTES, SIGNAL_ROUTES, IMPORT_WALLET_ROUTES = range(8)
CHANNEL, SIGNAL, TRADE, CLOSE = range(4)
COPYTRADE, WALLET, LAN, CLOSE = range(4)
MENU, VIEW, CREATE, IMPORT, EXPORT, DELETE, SETDEFAULT, END, CANCEL, FINISH = range(10)

async def menu_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.insert_user(user_id=update.effective_user.id)
    db_inst.get_conn().commit()
    db_inst.get_conn().close()
    logger.info(f"menu config msg id: {update.effective_message.message_id}")
    keyboard = [
        [ InlineKeyboardButton("Channels", callback_data=str(CHANNEL)) ],
        [ InlineKeyboardButton("My Groups", callback_data=str(TRADE)) ],
        [ InlineKeyboardButton("My Signal", callback_data=str(SIGNAL)) ],
        [ InlineKeyboardButton("Close", callback_data=str(CLOSE)) ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Please choose how to do."
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='html')
    return MENU_ROUTES


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    logger.info(f"menu msg id: {update.effective_message.message_id}")

    # 数据库回滚
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().close()
        del msg_db_inst_cache[update.effective_user.id]
    else:
        logger.warn(f"Cancel Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

    keyboard = [
        [ InlineKeyboardButton("Channels", callback_data=str(CHANNEL)) ],
        [ InlineKeyboardButton("My Groups", callback_data=str(TRADE)) ],
        [ InlineKeyboardButton("My Signal", callback_data=str(SIGNAL)) ],
        [ InlineKeyboardButton("Close", callback_data=str(CLOSE)) ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Please choose how to do"
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='html')
    return MENU_ROUTES


async def view_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("My Copy Trading", callback_data=str(COPYTRADE))
        ],
        [
            InlineKeyboardButton("Wallet Settings", callback_data=str(WALLET))
        ],
        [
            InlineKeyboardButton("Language Settings", callback_data=str(LAN))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(CLOSE))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Please choose how to do."

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return SIGNAL_ROUTES


async def wallet_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    logger.info(f"wallet id: {update.message.from_user.id}")
    logger.info(f"start msg id: {update.effective_message.message_id}")
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
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    db_inst.get_conn().close()
    logger.info(f"user id: {update.effective_user.id}")
    addrs = [addr[0] for addr in addrs]
    logger.info(addrs)
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    text += "Please choose how to do with your wallet, you can also send command /cancel to cancel current config <strong>or you can press 'Finish' to Store your config and exit.</strong>"
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='html')
    return WALLET_ROUTES


async def view_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Set Default Wallet", callback_data=str(SETDEFAULT))
        ],
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
            InlineKeyboardButton("Commit", callback_data=str(FINISH))
        ],
        [
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]
    if default_addr:
        text += f"Default Wallet: <code>{default_addr}</code>\n"
    else:
        text += f"Default Wallet: <code>None.</code>\nPlease select your default wallet.\n"
    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs]
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    text += "Please choose how to do with your wallet.\n<strong>Commit:</strong> to Store your config.\n<strong>Back Main Menu:</strong> to return to main menu.\n<strong>Close:</strong> to close menu.\n"

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return WALLET_ROUTES


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
        logger.info(f"pri key: {key}, addr: {addr}")

        # 加密
        (ciphertext, nonce) = wallet.encrypt_wallet_key(key, AES_KEY)
        logger.info(f"ct: {ciphertext}, nonce: {nonce}")

        # 存储到数据库
        if msg_db_inst_cache.get(update.effective_user.id, None):
            db_inst = msg_db_inst_cache[update.effective_user.id]
        else:
            logger.info((msg_db_inst_cache, update.effective_user.id))
            db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
            msg_db_inst_cache[update.effective_user.id] = db_inst
        db_inst.insert_wallet(user_id=update.effective_user.id, private_key_e=ciphertext, nonce=nonce, address=addr)

        keyboard = [
            [ InlineKeyboardButton("OK", callback_data=str(FINISH)) ],
            [ InlineKeyboardButton("Cancel", callback_data=str(CANCEL)), ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=f"Create Wallet Success!\nYour wallet private key: <code>{key}</code>\nYour wallet address: <code>{addr}</code>\n<strong>If you have remembered the key and address, I will hide them!</strong>", reply_markup=reply_markup, parse_mode='html')

        return WALLET_ROUTES


async def import_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Please input your private key:", parse_mode='html')

    return IMPORT_WALLET_ROUTES


async def import_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pri_key = update.effective_message.text
    logger.info(f"text: {pri_key}")

    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst

    err_text=f"Incorrect private key format!"
    notify_text = f"Please input correct private key again:\nIf you want to cancel this, please press <strong>cancel</strong>"

    keyboard = [
        [ InlineKeyboardButton("OK", callback_data=str(FINISH)) ],
        [ InlineKeyboardButton("Cancel", callback_data=str(CANCEL)), ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if pri_key.startswith("0x"):
        pri_key = pri_key[2:]
    if len(pri_key) == 64:
        try:
            a2b_hex(pri_key)
        except:
            await update.effective_user.send_message(text=err_text+'\n'+notify_text, parse_mode='html')
            return IMPORT_WALLET_ROUTES
        (key, addr) = wallet.import_wallet(pri_key)
        (ciphertext, nonce) = wallet.encrypt_wallet_key(private_key=key, aes_key=AES_KEY)
        db_inst.insert_wallet(user_id=update.effective_user.id, private_key_e=ciphertext, nonce=nonce, address=addr)
        success_text = f"Import Success.\nImport wallet address:\n<code>{addr}</code>\nIf you confirm the wallet import, please press <strong>'OK'</strong>. If you want to cancel this, please press <strong>cancel</strong>"
        await update.message.reply_text(text=success_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES
    else:
        await update.effective_user.send_message(text=err_text+'\n'+notify_text, parse_mode='html')
        return IMPORT_WALLET_ROUTES


async def export_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs_keys_nonces]

    export_addrs_cache[update.effective_message.message_id] = addrs_keys_nonces

    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
            keyboard.append([InlineKeyboardButton(f"{i}: {addrs[i][:6]}", callback_data=str(i))])
        text += "Please choose which wallet to export, you can also send command /cancel to cancel current config"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_NUM_ROUTES
    else:
        text += "None.\n"
        text += "You have no wallets to export."
        keyboard.append([InlineKeyboardButton("OK", callback_data=str(VIEW))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def set_default_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs_keys_nonces]

    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]
    if default_addr:
        text += f"Current Default Wallet:\n <code>{default_addr}</code>\n"
    else:
        text += f"Current Default Wallet: <code>None.</code>\n"

    export_addrs_cache[update.effective_message.message_id] = addrs_keys_nonces

    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
            keyboard.append([InlineKeyboardButton(f"{i}: {addrs[i][:6]}", callback_data=addrs[i])])
        text += "Please choose which wallet to be your new default wallet, you can also send command /cancel to cancel current config"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_SET_DEFAULT_ROUTES
    else:
        text += "None.\n"
        text += "You have no wallets to set."
        keyboard.append([InlineKeyboardButton("OK", callback_data=str(VIEW))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def delete_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs_keys_nonces]

    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]

    if addrs:
        for i in range(len(addrs)):
            if addrs[i] == default_addr:
                continue
            text += f"{i}: <code>{addrs[i]}</code>\n"
            keyboard.append([InlineKeyboardButton(f"{i}: {addrs[i][:6]}", callback_data=addrs[i])])
        text += "Please choose which wallet to delete, you can also send command /cancel to cancel current config"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_DELETE_ROUTES
    else:
        text += "None.\n"
        text += "You have no wallets to delete."
        keyboard.append([InlineKeyboardButton("OK", callback_data=str(VIEW))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES
    

async def delete_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []

    address = query.data
    
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    if address:
        res = db_inst.delete_address_from_wallet(address=address)
        logger.info(res)
        logger.info(address)
        keyboard = [
            [InlineKeyboardButton("OK", callback_data=str(FINISH))],
            [InlineKeyboardButton("Cancel", callback_data=str(CANCEL))],
        ]
        new_text = f"Delete Success.\Delete wallet address:\n<code>{address}</code>\n<strong>If you confirm, please press 'OK'.</strong>"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=new_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def set_default_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []

    address = query.data
    
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst

    if address:
        if not update.effective_user.id:
            logger.error("user id not found!")
        db_inst.set_address_from_user_by_user_id(user_id=update.effective_user.id, address=address)
        logger.info(address)
        keyboard = [
            [InlineKeyboardButton("OK", callback_data=str(FINISH))],
            [InlineKeyboardButton("Cancel", callback_data=str(CANCEL))],
        ]
        new_text = f"Set Default Wallet Success.\nDefault wallet address:\n<code>{address}</code>\n<strong>If you confirm, please press 'OK'.</strong>"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=new_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []

    num = int(query.data)
    
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    if export_addrs_cache.get(update.effective_message.message_id, None):
        addrs_keys_nonces = export_addrs_cache[update.effective_message.message_id]
    else:
        logger.info((export_addrs_cache, update.effective_message.message_id))
        addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
        export_addrs_cache[update.effective_message.message_id] = addrs_keys_nonces

    logger.info(addrs_keys_nonces)

    if addrs_keys_nonces:
        logger.info(query.data)
        keyboard = [
            [InlineKeyboardButton("OK", callback_data=str(FINISH))],
            [InlineKeyboardButton("Cancel", callback_data=str(CANCEL))],
        ]
        # db
        cipher = addrs_keys_nonces[num][1]
        nonce = addrs_keys_nonces[num][2]
        pri_key = wallet.decrypt_wallet_key(a2b_hex(cipher), AES_KEY, a2b_hex(nonce))
        new_text = f"Export Success.\nExport wallet address:\n<code>{addrs_keys_nonces[num][0]}</code>\nPrivate Key:\n<code>{pri_key}</code>\n<strong>If you confirm, please press 'OK' and then I will hide them.</strong>"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=new_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()

    # 数据库commit
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().commit()
    else:
        logger.warn(f"Finish Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

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
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Commit wallet config success!\n"

    text += "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]
    if default_addr:
        text += f"Current Default Wallet: <code>{default_addr}</code>\n"
    else:
        text += f"Current Default Wallet: <code>None.</code>\n"

    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs]
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return WALLET_ROUTES


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    query = update.callback_query
    await query.answer()

    # 数据库rollback
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().rollback()
    else:
        logger.warn(f"Cancel Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

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
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Wallet config canceled!\n"
    text += "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs]
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')

    return WALLET_ROUTES


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    
    user = update.effective_user
    logger.info("User %s canceled the conversation.", user.username)

    # 数据库close
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().close()
        del msg_db_inst_cache[update.effective_user.id]
    else:
        logger.warn(f"Close Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="Menu Close.")
    else:
        await update.message.reply_text(text="Menu Close.")

    return ConversationHandler.END


handler = ConversationHandler(
    entry_points=[CommandHandler("menu", menu_config)],
    states={
        MENU_ROUTES: [
            CallbackQueryHandler(view_signal, pattern="^" + str(SIGNAL) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(CLOSE) + "$"),
        ],
        WALLET_NUM_ROUTES: [
            # 数字
            CallbackQueryHandler(show_wallet, pattern="^[0-9]*$")
        ],
        WALLET_DELETE_ROUTES: [
            CallbackQueryHandler(delete_wallet_address)
        ],
        WALLET_SET_DEFAULT_ROUTES: [
            CallbackQueryHandler(set_default_wallet_address)
        ],
        SIGNAL_ROUTES: [
            CallbackQueryHandler(view_wallet, pattern="^" + str(WALLET) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(CLOSE) + "$"),
        ],
        IMPORT_WALLET_ROUTES: [
            CommandHandler("cancel", cancel), 
            MessageHandler(filters.TEXT, import_wallet_address)
        ],
        WALLET_ROUTES: [
            CallbackQueryHandler(view_wallet, pattern="^" + str(VIEW) + "$"),
            CallbackQueryHandler(set_default_wallet, pattern="^" + str(SETDEFAULT) + "$"),
            CallbackQueryHandler(create_wallet, pattern="^" + str(CREATE) + "$"),
            CallbackQueryHandler(import_wallet, pattern="^" + str(IMPORT) + "$"),
            CallbackQueryHandler(export_wallet, pattern="^" + str(EXPORT) + "$"),
            CallbackQueryHandler(delete_wallet, pattern="^" + str(DELETE) + "$"),
            CallbackQueryHandler(finish, pattern="^" + str(FINISH) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            CallbackQueryHandler(cancel, pattern="^" + str(CANCEL) + "$"),
            CallbackQueryHandler(menu, pattern="^" + str(MENU) + "$"),
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)