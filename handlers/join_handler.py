import logging
import requests
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple
from binascii import b2a_hex,a2b_hex

from telegram import  ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Chat, ChatMember, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
    CallbackContext,
    InlineQueryHandler,
    CallbackQueryHandler,
)

from db.db import DB
from env import *
from web3_helper import Web3Helper
from wallet import wallet

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CHECK_STARTED = False

JOIN_ROUTES = range(1)
JOIN, CLOSE, PAY = range(3)


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global payment_amount
    if False == CHECK_STARTED:
        pass
        # CHECK_STARTED = True
    else:
        await update.message.reply_text('There is already a payment being processed, please refrain from entering the information again.')
        await asyncio.sleep(0)
        return

    # 回复一个带有付款链接的按钮
    keyboard = [
        [ InlineKeyboardButton(f"Pay with {payment_amount} ETH(Arbitrum)", callback_data=str(PAY)) ],
        [ InlineKeyboardButton("Cancel", callback_data=str(CLOSE)) ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please click the button below to proceed with the payment:', reply_markup=reply_markup)
    return JOIN_ROUTES


async def pay(update: Update, context: CallbackContext) -> None:
    global payment_address
    global payment_amount
    global token_address
    global token_decimal
    global web3_path

    query = update.callback_query

    message = await query.edit_message_text(f"Receiving address: {payment_address}\nReceiving amount: {payment_amount}", parse_mode='html')
    
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    res = db_inst.fetch_address_from_user_by_id(query.from_user.id)
    default_address = res[0][0]
    if not default_address:
        query.edit_message_text(f"Please set your default wallet in [My Signal -> Wallet Settings] at first.")
        return ConversationHandler.END
    
    message = await query.edit_message_text(f"Your default wallet used for payment: {default_address}\nPayment is being processed. Please be patient...", parse_mode='html')

    res = db_inst.fetch_key_by_address(default_address)
    cipher = res[0][0]
    nonce = res[0][1]
    pri_key = wallet.decrypt_wallet_key(a2b_hex(cipher), AES_KEY, a2b_hex(nonce))

    w3h = Web3Helper(path=web3_path, id='arbi', priv_key=pri_key)
    # 查询gas余额
    if w3h.get_balance(account=w3h.wallet_address) < 21000 * 300e9:
        await query.message.reply_text(f"Please make your default wallet gas balance more than 0.007 ETH.")
        return ConversationHandler.END
    # 查询付款余额
    if w3h.get_balance(account=w3h.wallet_address, token=token_address) < payment_amount * 10**token_decimal:
        await query.message.reply_text(f"Please make your default wallet pay token balance more than {payment_amount}.")
        return ConversationHandler.END
    
    rc,success = w3h.transfer(recipient=payment_address, token=token_address, amount=int(payment_amount * 10**token_decimal))
    if success:
        invite_link = (await query._bot.create_chat_invite_link(chat_id=chat_id, expire_date=0, member_limit=1)).invite_link
        await query.message.reply_text(f"You have successfully made the payment. Click the link to join the group:\n{invite_link}", parse_mode='html')
    else:
        logger.error(f"transfer error. receipt: {rc}")
        await query.message.reply_text("Payment timeout or unsuccessful. Please enter <strong>/join</strong> to complete the payment again.", parse_mode='html')


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    
    user = update.effective_user
    logger.info("User %s canceled the conversation.", user.username)

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="Join Close.")
    else:
        await update.message.reply_text(text="Join Close.")

    # CHECK_STARTED = False
    return ConversationHandler.END


chat_id, web3_path, payment_amount, payment_address, token_address, token_decimal = -4016425542, 'https://arb1.arbitrum.io/rpc', 0.001, '0x9fbBf54BF8bE8B7c60Ecf3662CbE2Fe91d8198Fb', None, 18

"""Run the bot."""

handler = ConversationHandler(
    entry_points=[CommandHandler("join", join)],
    states={
        JOIN_ROUTES: [
            CallbackQueryHandler(pay, pattern="^" + str(PAY) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(CLOSE) + "$"),
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)