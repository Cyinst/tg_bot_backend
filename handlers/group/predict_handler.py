from notify.notify import notify
from service import quote
import logging
from db.db import DB
from telegram import (
    KeyboardButton,
    KeyboardButtonPollType,
    Poll,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    filters,
)
from env import *
from datetime import datetime as dt
import datetime

logger = logging.getLogger(__name__)

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a predefined poll"""
    # TODO: 查看是否是由管理员发起
    args = []
    for arg in context.args:
        if f"@{BOT_NAME}" in arg:
            continue
        else:
            args.append(arg)
    
    # TODO: fetch from db
    tz = 3
    chain = 'ether'

    if len(args) == 4 and len(args) >= 3:
        coin = args[0]
        if len(coin) > 42:
            logger.warn(f"coin name too long.")
            update.effective_message.reply_text(text="Poll failed. Coin name too long.")
            return None
        chain = args[1]
        expire_poll_hours = int(args[2])
        expire_poll_time = dt.now(tz=datetime.timezone(datetime.timedelta(hours=tz))) + datetime.timedelta(hours=expire_poll_hours)
        settle_poll_hours = int(args[3])
        settle_poll_time = dt.now(tz=datetime.timezone(datetime.timedelta(hours=tz))) + datetime.timedelta(hours=settle_poll_hours)
        res = await quote.quote_token(coin, chain)
        if not res:
            logger.warn(f"quote fail. res: {res}. coin: {coin}. chain: {chain}")
            update.effective_message.reply_text(text="Poll failed. Please check your input format.")
            return None
    elif len(args) == 3:
        coin = args[0]
        if len(coin) > 42:
            logger.warn(f"coin name too long.")
            update.effective_message.reply_text(text="Poll failed. Coin name too long.")
            return None
        expire_poll_hours = int(args[1])
        expire_poll_time = dt.now(tz=datetime.timezone(datetime.timedelta(hours=tz))) + datetime.timedelta(hours=expire_poll_hours)
        settle_poll_hours = int(args[2])
        settle_poll_time = dt.now(tz=datetime.timezone(datetime.timedelta(hours=tz))) + datetime.timedelta(hours=settle_poll_hours)
        res = await quote.quote_token(coin)
        if not res:
            logger.warn(f"quote fail. res: {res}. coin: {coin}")
            update.effective_message.reply_text(text="Poll failed. Please check your input format.")
            return None
    else:
        await update.effective_message.reply_text(text="Poll failed. Please check your input format.")
        return None
    
    coin_name = res['name']
    coin_price = res['price']
    coin_addr = res['address']
    if float(coin_price) < 1e-12 or float(coin_price) > 1e12:
        logger.warn(f"quote fail. Precision Err. res: {res}. coin: {coin}")
        update.effective_message.reply_text(text=f"Poll failed. Price: {coin_price}, Precision out of format.")
        return None

    questions = ["0～2%", "↑2～5%", "↑5～10%", "↑10～20%", "↑20%+", "↓2～5%", "↓5～10%", "↓10～20%", "↓20%+"]
    message = await context.bot.send_poll(
        update.effective_chat.id,
        f"Predict {coin_name} price at {settle_poll_time.strftime('%Y-%m-%d %H:%M:%S%z')}.\nNow current price: {'%.6g'%coin_price}\nPrediction end at {expire_poll_time.strftime('%Y-%m-%d %H:%M:%S%z')}, so please vote in a hurry!",
        questions,
        is_anonymous=False,
        allows_multiple_answers=False,
    )
    if not await update.effective_chat.pin_message(message_id=message.id):
        logger.warn("pin poll failed!")
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "message_id": message.message_id,
            "chat_id": update.effective_chat.id,
        }
    }
    context.bot_data.update(payload)
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.insert_poll(poll_id=message.poll.id, chat_id=update.effective_chat.id, message_id=update.effective_message.id, start_price=coin_price, coin=coin_addr, chain=chain, settle_poll_time=settle_poll_time, expire_poll_time=expire_poll_time)
    db_inst.get_conn().commit()
    db_inst.get_conn().close()


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    # try:
    #     questions = answered_poll["questions"]
    # # this means this poll answer update is from an old poll, we can't do our answering then
    # except KeyError:
    #     return
    # tz = 3
    # curr_time = dt.now(tz=datetime.timezone(datetime.timedelta(hours=tz)))
    selected_options = answer.option_ids
    # answer_string = ""
    # for question_id in selected_options:
    #     if question_id != selected_options[-1]:
    #         answer_string += questions[question_id] + " and "
    #     else:
    #         answer_string += questions[question_id]
    # await context.bot.send_message(
    #     answered_poll["chat_id"],
    #     f"{update.effective_user.mention_html()} feels {answer_string}!",
    #     parse_mode=ParseMode.HTML,
    # )
    # Close poll after three participants voted
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    # (expire_poll_time, chat_id) = db_inst.
    # if curr_time > expire_poll_time:
    #     await context.bot.stop_poll(chat_id=answered_poll['chat_id'], answered_poll["message_id"])
    res = db_inst.fetch_expire_and_chat_and_msg_from_poll_by_poll_id(poll_id=answer.poll_id)
    expire_poll_time = res[0][0]
    chat_id = res[0][1]
    msg_id = res[0][2]
    if dt.now() <= expire_poll_time:
        db_inst.insert_predict(poll_id=answer.poll_id, chat_id=chat_id, user_id=update.effective_user.id, first_name=update.effective_user.first_name, answer=selected_options[0])
        db_inst.get_conn().commit()
        db_inst.get_conn().close()
    else:
        await context.bot.stop_poll(chat_id=chat_id, message_id=msg_id)
        return


async def receive_poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """On receiving polls, reply to it by a closed poll copying the received poll"""
    actual_poll = update.effective_message.poll
    # Only need to set the question and options, since all other parameters don't matter for
    # a closed poll
    print("poll test")
    await update.effective_message.reply_poll(
        question=actual_poll.question,
        options=[o.text for o in actual_poll.options],
        # with is_closed true, the poll/quiz is immediately closed
        is_closed=True,
        reply_markup=ReplyKeyboardRemove(),
    )


# poll_msg = MessageHandler(filters.POLL, receive_poll)
poll_answer = PollAnswerHandler(receive_poll_answer)
poll_cmd = CommandHandler("predict", poll)