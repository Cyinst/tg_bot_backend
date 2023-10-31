import schedule
from schedule import every, repeat, run_pending
import asyncio
from db.db import DB
from env import *
from service import quote
from notify import notify
import logging

logger = logging.getLogger(__name__)


def get_quote(coin_addr, chain):
    res = None
    event_loop = asyncio.get_event_loop()
    try:
        coro = quote.quote_token(token=coin_addr, chain=chain)
        res = event_loop.run_until_complete(coro)
    finally:
        event_loop.close()
    return res


def get_notify(text, chat_id):
    event_loop = asyncio.get_event_loop()
    try:
        coro = notify.notify(text=text, chat_id=chat_id)
        res = event_loop.run_until_complete(coro)
    finally:
        event_loop.close()
    return res


def run_settle_predict():
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)

    results = db_inst.fetch_from_poll_by_settle_time()

    results = db_inst.fetch_from_poll()
    print(results)

    for res in results:
        poll_id: str = res[0]
        chat_id: int = res[1]
        msg_id: int = res[2]
        coin_addr: str = res[3]
        chain: str = res[4]
        start_price: float = float(res[5])
        res = asyncio.run(quote.quote_token(coin_addr, chain))
        if not res:
            logger.error(f"sched quote fail. coin: {coin_addr}, chain: {chain}, poll_id: {poll_id}")
            continue
        end_price = res['price']
        rise = (end_price / start_price - 1) * 100
        win_option = None
        
        questions = ["0～2%", "↑2～5%", "↑5～10%", "↑10～20%", "↑20%+", "↓2～5%", "↓5～10%", "↓10～20%", "↓20%+"]
        if rise >= -2 and rise <= 2:
            win_option = 0
        elif rise >= 2 and rise <= 5:
            win_option = 1
        elif rise >= 5 and rise <= 10:
            win_option = 2
        elif rise >= 10 and rise <= 20:
            win_option = 3
        elif rise >= 20:
            win_option = 4
        elif rise <= -2 and rise >= -5:
            win_option = 5
        elif rise <= -5 and rise >= -10:
            win_option = 6
        elif rise <= -10 and rise >= -20:
            win_option = 7
        elif rise <= -20:
            win_option = 8
        
        poll_result = questions[win_option]
        asyncio.run(notify.notify(text=f"🎉Prediction Poll End!\nPrice at {'%.6g'%start_price}.\nNow current price: {'%.6g'%end_price}\nRise: {'%.2g'%rise}%\nWin Prediction: {poll_result}💐", chat_id=chat_id))

        # TODO: db 删除
        # db_inst.delete_from_poll()

    db_inst.get_conn().commit()
    db_inst.get_conn().close()