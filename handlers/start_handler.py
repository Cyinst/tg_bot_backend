import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db.db import DB
from env import *

logger = logging.getLogger(__name__)


from telegram import MessageEntity


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"hello, {update.effective_user.id}")
    if not update.message.entities:
        return

    for entity in update.message.entities:
        if entity.type == MessageEntity.TEXT_MENTION:
            user_id = entity.user.id
            print(user_id)
            # Do something with user_id

    if update.effective_chat.id < 0:
        text = "The command used only in private chat."
        await update.message.reply_text(text, parse_mode='html')
        return
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.insert_user(user_id=update.effective_user.id)
    db_inst.insert_user_to_top_groups_user(user_id=update.effective_user.id, chat_id=update.effective_chat.id)
    db_inst.get_conn().commit()
    db_inst.get_conn().close()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=
"""
🎉 Welcome to Social Signal!
👥 We are an all-new Web3 social crypto trading platform, dedicated to building professional, high-quality communities for crypto traders via Telegram.
🔑 Users can join exclusive paid groups and interact directly with top traders.
⚙️ We facilitate expert-level trading ecosystems and social systems around valuable investment opportunities, seamlessly connecting information flows with trading signals.
🤹Here, retail investors can also obtain professional digital asset trading experiences in a socialized way.

Get started with:
/menu - Learn more and connect wallet

Join our community:
Telegram: https://t.me/signalswap
Discord: https://discord.gg/signalswap
Twitter: https://twitter.com/signalswap
"""
                                   )

handler = CommandHandler('start', hello)