
from wallet import wallet
from db.db import DB
from env import *
import time
from web3_helper import Web3Helper
from binascii import a2b_hex
logger = logging.getLogger(__name__)


async def join_strategy(user_id:int, strategy_id:int,address:str):
    logger.info(f"join :user_id:{user_id} strategy_id:{strategy_id} address:{address}")
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.set_used_address(user_id=user_id,address=address,joined_strategy_id=strategy_id)
    strategy = db_inst.execute_with_result(f"select * from strategy where strategy_id={strategy_id} for update")
    joined_wallets_str = strategy[0][3]
    import json

    joined_wallet = json.loads(joined_wallets_str)
    logger.info(f"joined wallet = {joined_wallet}")
    join_info = {}
            # JOINED_WALLETS = [{"wallet_id":235,"address":"0xAD1...."，"user_id":134}]

    join_info['user_id'] = user_id
    join_info['address'] = address
    join_info['timestamp'] = int(time.time())
    joined_wallet.append(join_info)
    joined_wallet_after_update = json.dumps(joined_wallet)
    db_inst.execute(f"update strategy set JOINED_WALLETS='{joined_wallet_after_update}' where strategy_id={strategy_id}")
    db_inst.execute("commit")
    logger.info(f"user_id:{user_id} wallet{address} join strategy{strategy_id}")
    pass


async def follow_exec(strategy_id:int,in_token_symbol:str,in_token_address:str,out_token_symbol:str,out_token_address:str,percent:int):
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    datas = db_inst.query(f"select chain,dex,base_coin,quote_coin,kol_wallet_address,JOINED_WALLETS,base_coin_address,quote_coin_address from strategy where strategy_id={strategy_id}")
    strategy = datas[0]
    chain = str.strip(strategy[0])
    dex = str.strip(strategy[1])
    base_coin = str.strip(strategy[2])
    quote_coin = str.strip(strategy[3])
    kol_wallet_address = "0x"+strategy[4]
    joined_wallet_str = strategy[5]
    base_coin_address = strategy[6]
    quote_coin_address = strategy[7]
    import json
    logger.info(f"try exec kol_wallet_address = {kol_wallet_address}")
    if chain != 'ARB':
        raise ValueError('Only Support ARB')
    if dex != 'UniswapV3':
        raise ValueError('Only Support UniswapV3')
        
    router =  "0xE592427A0AEce92De3Edee1F18E0157C05861564"
    import time
    # def swap_exact_in(self, uniV3RouterAddress, tokenIn: str, tokenOut: str, fee: int, recipient: str, deadline: int, amountIn: int, amountOutMin: int, sqrtPriceLimitX96=None):
    # if __name__ == "__main__":
    # helper = Web3Helper(path="https://rpc.mevblocker.io", priv_key=PRIVATE_KEY)
    # weth = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    # usdc = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    # fee = 0x1f4
    # recipient = "0xF5c12b5b6aB5aFbD87a5BE34f1f7a6473b7eAb0F"
    # deadline = 0x1617e3003
    # amountIn = 1000000000000000
    # amountOutMin = 1500000
    # # helper.approve(weth, uniV3RouterAddressETH, 0)
    # helper.swap_exact_in(uniV3RouterAddressETH, weth, usdc, fee, recipient, deadline, amountIn, amountOutMin)
    sqrtPriceLimitX96 = 0
    joined_wallets = json.loads(joined_wallet_str)
    for joined_wallet in joined_wallets:
        address = joined_wallet['address']
        res = db_inst.fetch_key_by_address(address)
        cipher = res[0][0]
        nonce = res[0][1]
        pri_key = wallet.decrypt_wallet_key(a2b_hex(cipher), AES_KEY, a2b_hex(nonce))
        w3h = Web3Helper(id='arbi', priv_key=pri_key)
         # 查询gas余额
        if w3h.get_balance(account=w3h.wallet_address) < 21000 * 300e9:
            raise ValueError("{address} Walletgas balance less than 0.007 ETH.")
    # 查询付款余额
        balance = w3h.get_balance(account=w3h.wallet_address, token=in_token_address)
        exec_amount = balance *  int(percent) / 100
        logger.info(f"follow wallet exec token = {in_token_symbol}->{out_token_symbol} in_balance = {balance}  exec_amount = {exec_amount}")
        if exec_amount < 100:
            logger.info(f"{address} Balance too small to exchange balance = {balance} exec balance = {exec_amount}")
            continue
        w3h.approve(in_token_address, router, None)
        w3h.swap_exact_in(router,in_token_address,out_token_address,fee = 0x1f4,recipient=kol_wallet_address,deadline=int(time.time()+60),amountIn=exec_amount,amountOutMin=10,sqrtPriceLimitX96=sqrtPriceLimitX96)
    return
   


async def stop_follow(user_id:int,strategy_id:int,address:str):
    logger.info(f"join :user_id:{user_id} strategy_id:{strategy_id} address:{address}")
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.set_unused_address(user_id=user_id,address=address,joined_strategy_id=strategy_id)
    strategy = db_inst.execute_with_result(f"select * from strategy where strategy_id={strategy_id} for update")
    joined_wallets_str = strategy[0][3]
    import json

    joined_wallet = json.loads(joined_wallets_str)
    logger.info(f"joined wallet = {joined_wallet}")
    join_info = {}
            # JOINED_WALLETS = [{"wallet_id":235,"address":"0xAD1...."，"user_id":134}]

    join_info['user_id'] = user_id
    join_info['address'] = address
    join_info['timestamp'] = int(time.time())
    index = None
    for (i,wallet) in enumerate(joined_wallet):
        if wallet['user_id'] == user_id and wallet['address'] == address:
            index = i
    if index:
        list.pop(joined_wallet,index)
    
    joined_wallet_after_update = json.dumps(joined_wallet)
    db_inst.execute(f"update strategy set JOINED_WALLETS='{joined_wallet_after_update}' where strategy_id={strategy_id}")
    db_inst.execute("commit")
    logger.info(f"user_id:{user_id} wallet{address} leave strategy{strategy_id}")