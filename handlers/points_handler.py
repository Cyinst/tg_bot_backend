import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from telegram.constants import ParseMode
from db.db import DB
from env import *
from datetime import datetime as dt

logger = logging.getLogger(__name__)

from functools import cmp_to_key
def desc(a, b):
    if a[1] > b[1]:
        return -1
    else:
        return 1


async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id > 0:
        # private query
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        results = db_inst.fetch_point_by_user_id(user_id=update.effective_user.id)
        total_point = 0
        point_detail = {}
        for res in results:
            amount = int(res[0])
            total_point += amount
            point_type = res[1]
            if point_type in point_detail:
                point_detail[point_type] += amount
            else:
                point_detail[point_type] = amount
        
        user = update.effective_user.mention_html()
        text = f"Lifetime Points Summary for {user}\n"
        for t in point_detail:
            text += f"{t}: {point_detail[t]}\n"
        text += f"Total Lifetime Points: {total_point}\n"
        text += f"Points Settlement Date: {dt.now()} UTC\n"
    else:
        # group query
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        results = db_inst.fetch_group_user_point()
        user_point = {}
        my_point = 0
        for res in results:
            point = int(res[0])
            user_id = int(res[1])
            if user_id == update.effective_user.id:
                my_point = point
            if user_id in user_point:
                user_point[user_id] += point
            else:
                user_point[user_id] = point
        user_point = list(user_point.items())
        user_point.sort(key=cmp_to_key(desc))
        
        text = f"Group: {update.effective_chat.mention_html()}\n"
        text += "Private Group Points Ranking\n"
        text += "Top Members:\n"
        for i in user_point[:5]:
            text += f"{i[0]} - {i[1]} points"
        text += "Your Current Rank:\n"
        rank = -1
        for id in range(len(user_point)):
            if user_point[id][0] == update.effective_user.id:
                rank = id + 1
                break
        if rank == -1:
            text += f"You have {my_point} points.\n"
        else:
            text += f"#{rank} - You have {my_point} points.\n"

        text += f"Points Settlement Date: {dt.now()} UTC\n"

    await update.effective_message.reply_text(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)

handler = CommandHandler('points', points)