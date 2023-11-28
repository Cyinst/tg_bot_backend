
from db.db import DB
from env import *
import time
from web3_helper import Web3Helper
from binascii import a2b_hex
logger = logging.getLogger(__name__)


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
    
    
