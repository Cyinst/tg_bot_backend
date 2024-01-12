import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db.db import DB
from telegram.constants import ParseMode
from web3 import Web3
from service import equity
from env import *

logger = logging.getLogger(__name__)


async def kolistats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id < 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The command used only in private chat.")
        return 
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)

    # groups
    groups = []
    results = db_inst.fetch_group_from_groups(kol_id=update.effective_user.id)
    for res in results:
        groups.append(res[0])
    
    # strategy
    st = []
    wallets = []
    results = db_inst.fetch_strategy_id_and_address_from_strategy(kol_id=update.effective_user.id)
    for res in results:
        st.append(res[0])
        address = Web3.to_checksum_address('0x' + res[1])
        wallets.append(address)

    e_list = await equity.async_equity_list(address_list=wallets)
    total_equity = 0
    for e in e_list:
        total_equity += e

    today_total_equity = 0
    for wallet in wallets:
        results = db_inst.fetch_today_equity(address=wallet)
        if not results or len(results) == 0:
            logger.error(f"wallet not found in db")
        else:
            today_balance = res[0][0]
            today_total_equity += today_balance
    
    current_profit = total_equity - today_total_equity
    
    estimate_7d_profit = today_total_equity * ((1 + (current_profit / (today_total_equity + 0.01))) ** 7 - 1)

    text = f"Here are the stats for you.\n"
    text += f"Current Profit: ${current_profit}\n"
    text += f"Estimate 7D Profit: ${estimate_7d_profit}\n"

    text += f"Strategies: {len(st)}\n"
    for i in st:
        text += f"{i}\n"
    
    text += f"Groups: {len(groups)}\n"
    for i in groups:
        text += f"{i}\n"
        
    # TODO follow user
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.HTML)

    

handler = CommandHandler('kolistats', kolistats)