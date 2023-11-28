
from db.db import DB
from env import *
import asyncio
from service.quote import quote_token, coin_dict
from web3_helper import Web3Helper

logger = logging.getLogger(__name__)

chain_token_dict = {
    'btc': {
        'chain': 'arbi', 
        'addr': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f',
        'dec': 8
    },
    'eth': {
        'chain': 'arbi', 
        'addr': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
        'dec': 18
    },
    'usdt': {
        'chain': 'arbi',
        'addr': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
        'dec': 6,
        'price': 1
    },
    'usdc': {
        'chain': 'arbi', 
        'addr': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
        'dec': 6,
        'price': 1
    },
    'usdce': {
        'chain': 'arbi', 
        'addr': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
        'dec': 6,
        'price': 1
    },
}


def equity_list(address_list):
    """
    prams: address must be Checksum address. 
    returns address total equity list (usd).
    example. [0.2, 0.345, 100.2390]
    """
    # calculate token price
    coin_price = {}
    for c in list(coin_dict.keys()):
        try:
            coin_price[c] = asyncio.run(quote_token(c))['price']
        except:
            coin_price[c] = 0
        print(f"{c} {coin_price[c]}")
    
    # calculate token balance
    w3 = Web3Helper()
    equity_list = []
    for addr in address_list:
        total_equity = w3.get_balance(account=addr) / 10 ** 18 * coin_price['eth']
        for i in chain_token_dict:
            balance = w3.get_balance(account=addr, token=chain_token_dict[i]['addr']) / 10 ** chain_token_dict[i]['dec']
            total_equity = total_equity + balance * chain_token_dict[i].get("price", None) if chain_token_dict[i].get("price", None) else total_equity + balance * coin_price[i]
        equity_list.append(total_equity)
    return equity_list


async def equity(wallet_address:str,token_address:str,decimal:int,value:int):
    w3h = Web3Helper(id='arbi', priv_key=None)
    # 查询gas余额
    return w3h.get_balance(account=wallet_address,token_address=token_address) * value / pow(10,decimal)
    
    
async def set_wallet_equity_snap(date:int,address:str,equity:float):
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.create_wallet_equity_snapshot(date,address,equity)
    db_inst.execute('commit')
    

async def get_wallet_equity_snap(date:int,address:str):
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    datas = db_inst.get_wallet_equity_snapshot(date,address)
    data = datas[0]
            # results = self.query(f"select SNAP_SHOT_ID,WALLET_ADDRESS,DATE_TIMESTAMP,EQUITY,COINS from EQUITY_SNAPSHOT where wallet_address = '{address}'")
    id = data[0]
    wallet_address = data[1]
    date_timestamp = data[2]
    equity = data[3]
    coins = data[4]
    logger.info(f"wallet :{wallet_address} date:{date} equity = {equity} coins = {coins}")
    
    
