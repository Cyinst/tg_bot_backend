import logging
import requests
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Tuple

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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

chat_id = None
nowpaymentsapi_key = None
price = None

CHECK_STARTED = False

PAYMENT_URL = 'https://api.nowpayments.io/v1/payment'

JOIN_ROUTES = range(1)
JOIN, CLOSE, PAID = range(3)


async def join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global chat_id
    global price

    if context.chat_data.get('payment_started'):
        await update.message.reply_text('Payment is being processed, please do not create duplicate payments')
        return

    if False == CHECK_STARTED:
        pass
        # CHECK_STARTED = True
    else:
        await update.message.reply_text('There is already a payment being processed, please refrain from entering the information again.')
        await asyncio.sleep(0)
        return

    # 回复一个带有付款链接的按钮
    keyboard = [
        [ InlineKeyboardButton(f"Pay with {price} USDT(BSC-BRC20)", callback_data=str(JOIN)) ],
        [ InlineKeyboardButton("Cancel", callback_data=str(CLOSE)) ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please click the button below to proceed with the payment:', reply_markup=reply_markup)
    return JOIN_ROUTES


async def button(update: Update, context: CallbackContext) -> None:
    global nowpaymentsapi_key
    global price

    query = update.callback_query
    if query.data == str(JOIN):
        if context.chat_data.get('payment_started'):
            await query.message.reply_text('Payment is being processed, please do not create duplicate payments.')
            return

        payload = json.dumps({
            "price_amount": price,
            "price_currency": "usd",
            "pay_currency": "usdtbsc",
            "ipn_callback_url": "https://api.nowpayments.io",
            "order_id": str(query.from_user.id) + '_' + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "order_description": "Apple Macbook Pro 2019 x 1",
            "case": "success"
        })
        headers = {
            'x-api-key': nowpaymentsapi_key,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", PAYMENT_URL, headers=headers, data=payload)
        # Define payment address and amount

        if response.status_code != 201:
            context.chat_data['payment_started'] = False
            await query.message.reply_text('Error processing, please re-send the command<strong>\join</strong>.', parse_mode='html')
            return

        payment_address = response.json()['pay_address']
        payment_amount = response.json()['pay_amount']
        payment_id = response.json()["payment_id"]
        order_id = response.json()["order_id"]

        # 存储 payment_id 到 chat_data 字典中
        context.chat_data["payment_id"] = payment_id

        context.chat_data["order_id"] = order_id

        message = await query.message.reply_text(f"Receiving address: {payment_address}, Receiving amount: {payment_amount}, <strong>Please make the payment using the BSC network.</strong>", parse_mode='html')
        context.chat_data['message_id'] = message.message_id
        keyboard = [
            [ InlineKeyboardButton("Payment has been made.", callback_data=str(PAID)) ],
            [ InlineKeyboardButton("Cancel", callback_data=str(CLOSE)) ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Please click the button below to confirm that the payment has been completed:", reply_markup=reply_markup)
        context.chat_data['payment_started'] = True


async def paid(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    wait_time = 60
    payment_id = context.chat_data.get("payment_id")
    payment_url = f'https://api.nowpayments.io/v1/payment/{payment_id}'

    headers = {'x-api-key': nowpaymentsapi_key}

    await query.edit_message_text("Order Processing...")

    while True:
        response = requests.get(payment_url, headers=headers)

        if response.status_code != 200:
            context.chat_data['payment_started'] = False
            await query.message.reply_text('Error processing, please re-send the command<strong>\join</strong>.', parse_mode='html')
            return

        payment_status = response.json()['payment_status']

        # Check payment status and handle accordingly
        if payment_status == 'finished':

            context.chat_data['payment_started'] = False

            invite_link = await update.get_bot.cr.bot.  create_chat_invite_link(chat_id=chat_id, expire_date=0, member_limit=1)

            order_id = context.chat_data["order_id"]
            
            # 您已经成功支付，点击链接加入群组：{invite_link}。您的订单id是:{order_id} ,有疑问请使用订单id联系群主
            await query.message.reply_text(f"You have successfully made the payment. Click the link to join the group:\n{invite_link}\nYour order ID is: <strong>{order_id}</strong>, If you have any questions, please contact the staff using the order ID.", parse_mode='html')
            # CHECK_STARTED = False
            return ConversationHandler.END
        elif payment_status == 'partially_paid':
            # Handle unpaid status
            await query.message.reply_text("You have paid a partial amount, please complete the payment.")
            time.sleep(wait_time)  # Wait for 3 minutes before querying status again
            continue
        elif payment_status == 'expired' or payment_status == 'failed':
            context.chat_data['payment_started'] = False
            await query.message.reply_text("Payment timeout or unsuccessful. Please enter <strong>/join</strong> to complete the payment again.", parse_mode='html')
            break
        else:
            await query.message.reply_text("Payment is being processed. Please be patient...")
            time.sleep(wait_time)  # Wait for 3 minutes before querying status again
            continue


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


def read_config_file(file_path):
    with open(file_path, "r") as file:
        for line in file:
            key_value_pair = line.strip().split(":")
            if key_value_pair[0] == "bottoken":
                bottoken = ":".join(key_value_pair[1:])
            elif key_value_pair[0] == "chat_id":
                chat_id = key_value_pair[1]
            elif key_value_pair[0] == "nowpaymentsapi_key":
                nowpaymentsapi_key = key_value_pair[1]
            elif key_value_pair[0] == "user":
                user = key_value_pair[1]
            elif key_value_pair[0] == "password":
                password = key_value_pair[1]
            elif key_value_pair[0] == "price":
                price = key_value_pair[1]

    return chat_id, nowpaymentsapi_key, price


chat_id, nowpaymentsapi_key, price = read_config_file("config.txt")

"""Run the bot."""

handler = ConversationHandler(
    entry_points=[CommandHandler("join", join)],
    states={
        JOIN_ROUTES: [
            CallbackQueryHandler(button, pattern="^" + str(JOIN) + "$"),
            CallbackQueryHandler(paid, pattern="^" + str(PAID) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(CLOSE) + "$"),
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)