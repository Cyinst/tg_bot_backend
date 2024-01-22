import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import *
from db.db import DB

logger = logging.getLogger(__name__)


async def wake(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = []
    for arg in context.args:
        if f"@{BOT_NAME}" in arg:
            continue
        else:
            args.append(arg)

    print(args)
    try:
        ticket_payment = args[0]
        kol_address = args[1]
        ticket_payment = float(ticket_payment)

        # check bot is admin and user is operater.
        isBotAdmin = False
        isKOLAdmin = False
        users = await update.effective_chat.get_administrators()
        for user in users:
            if user.user.id == (await update._bot.get_me()).id:
                isBotAdmin = True
            if user.user.id == update.effective_user.id:
                isKOLAdmin = True
                
        # if update.effective_user.id not in OPS:
        if not isKOLAdmin:
            await update.effective_message.reply_text(text="Wake Failed. Only Admin KOL can wake.")
            return None
        if not isBotAdmin:
            await update.effective_message.reply_text(text="Wake Failed. You should add bot as Admin at first.")
            return None
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        try:
            db_inst.insert_group(chat_id=update.effective_chat.id, kol_id=update.effective_user.id, ticket=ticket_payment)
            db_inst.insert_strategy(kol_id=update.effective_user.id, kol_address=kol_address, group_id=update.effective_chat.id)
            db_inst.get_conn().commit()
            db_inst.get_conn().close()
            await update.message.reply_text(text=f"Wake Success.")
        except Exception as e:
            logger.exception(e)
            db_inst.get_conn().commit()
            db_inst.get_conn().close()
            await update.message.reply_text(text=f"Wake Failed. Group waked already or something wrong.")
            return None
    except:
        await update.message.reply_text(text=f"Wake Failed. Please Check Your Input Format! Example: /wake @{BOT_NAME} [Ticket Price] [KOL_ADDRESS]")
        return


handler = CommandHandler('wake', wake)