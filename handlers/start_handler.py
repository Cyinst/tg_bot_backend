import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db.db import DB
from env import *

logger = logging.getLogger(__name__)


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.insert_user(user_id=update.effective_user.id)
    db_inst.get_conn().commit()
    db_inst.get_conn().close()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=
"""
Welcome to Social Signal! We are a social platform focused on building high-quality crypto trading communities.
Retail traders can buy entry keys to join these exclusive communities and interact directly with top traders.
Our platform facilitates the creation of expert trading circles and a social ecosystem around valuable signals.

Get started with: 
/start - Start to Use.
/menu - Bot Menu.

Join our community:
community_name: community_link
community_name: community_link
community_name: community_link
"""
                                   )

handler = CommandHandler('start', hello)