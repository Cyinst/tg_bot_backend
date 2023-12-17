import schedule
from schedule import every, repeat, run_pending
import asyncio
from db.db import DB
from env import *
from service import quote
from notify import notify
from web3 import Web3
import logging
import html
from web3_helper import Web3Helper

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


def update_daily_pnl():
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)

    results = db_inst.fetch_all_address()

    btc_price = asyncio.run(quote.quote_token('btc'))['price']
    eth_price = asyncio.run(quote.quote_token('eth'))['price']

    w3 = Web3Helper(path=W3_PATH, id=CHAIN_ALAIS)

    for res in results:
        wallet: str = Web3.to_checksum_address(res[0])
        user: int = res[1]
        eth_b = round(w3.get_balance(account=wallet) / 10**18, 6)
        btc_b = round(w3.get_balance(account=wallet, token=BTC) / 10**8, 6)
        usdc_b = round(w3.get_balance(account=wallet, token=USDC) / 10**6, 6)
        usdt_b = round(w3.get_balance(account=wallet, token=USDT) / 10**6, 6)
        total_balance = eth_price * eth_b + btc_price * btc_b + usdc_b + usdt_b
        total_balance = float(f'{total_balance:.6f}')
        db_inst.insert_balance(user_id=user, address=wallet, balance=total_balance, eth_balance=eth_b, btc_balance=btc_b, usdc_balance=usdc_b, usdt_balance=usdt_b)

    db_inst.get_conn().commit()
    db_inst.get_conn().close()