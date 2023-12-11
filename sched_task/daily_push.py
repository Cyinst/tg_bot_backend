import schedule
from schedule import every, repeat, run_pending
import asyncio
from db.db import DB
from env import *
from service import quote
from notify import notify
import logging
import html
from web3_helper import Web3Helper

logger = logging.getLogger(__name__)


def push_top_groups():
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)

    results = db_inst.fetch_user_from_top_groups_user()
    with open("top_groups.txt", 'r') as f:
        text = f.read()

    for res in results:
        user: int = res[0]
        chat_id: int = res[1]
        asyncio.run(notify.notify(text=text, chat_id=chat_id))
