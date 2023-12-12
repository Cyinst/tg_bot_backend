import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db.db import DB
from env import *

logger = logging.getLogger(__name__)


async def top_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id < 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The /topgroups command only use in private chat.")
        return 
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    results = db_inst.fetch_user_from_top_groups_user(user_id=update.effective_user.id)
    if not results or len(results) == 0:
        db_inst.insert_user_to_top_groups_user(user_id=update.effective_user.id, chat_id=update.effective_chat.id)
        db_inst.get_conn().commit()
        db_inst.get_conn().close()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The daily group list has been turned on for you, to turn it off enter the /topgroups command again.")
    else:
        db_inst.delete_user_from_top_groups_user(user_id=update.effective_user.id)
        db_inst.get_conn().commit()
        db_inst.get_conn().close()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The daily group list has been closed for you and will not be pushed the next day, to open it please enter the /topgroups command again.")

    

handler = CommandHandler('topgroups', top_groups)