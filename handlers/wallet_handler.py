import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
from binascii import a2b_hex
import html

from wallet import wallet
from db.db import DB
from env import *
from web3_helper import Web3Helper
from service.quote import quote_token

logger = logging.getLogger(__name__)

logger.info(f"aes key: {AES_KEY}")

msg_db_inst_cache = {}
export_addrs_cache = {}

# Stages
WALLET_ROUTES, END_ROUTES, MENU_ROUTES, WALLET_NUM_ROUTES, WALLET_DELETE_ROUTES, WALLET_SET_DEFAULT_ROUTES, SIGNAL_ROUTES, IMPORT_WALLET_ROUTES ,STRATEGY_ROUTERS = range(9)
CHANNEL, SIGNAL, TRADE, CLOSE,MY_STRATEGY,MY_FOLLOW,STRATEGY_LIST,EXEC_MY_STRATEGY = range(8)
COPYTRADE, WALLET, LAN, CLOSE = range(4)
MENU, VIEW, CREATE, IMPORT, EXPORT, DELETE, SETDEFAULT, END, CANCEL, FINISH = range(10)

async def menu_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_chat.id < 0:
        text = "The command used only in private chat."
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='html')
        return ConversationHandler.END
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.insert_user(user_id=update.effective_user.id)
    db_inst.insert_user_to_top_groups_user(user_id=update.effective_user.id, chat_id=update.effective_chat.id)
    db_inst.get_conn().commit()
    db_inst.get_conn().close()
    logger.info(f"menu config msg id: {update.effective_message.message_id}")
    logger.info(f"menu config user_id: {update.effective_user.id}")
    keyboard = [
        [ InlineKeyboardButton("Channels", callback_data=str(CHANNEL)) ],
        [ InlineKeyboardButton("My Groups", callback_data=str(TRADE)) ],
        [ InlineKeyboardButton("My Signal", callback_data=str(SIGNAL)) ],
        [ InlineKeyboardButton("Close", callback_data=str(CLOSE)) ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Please choose how to do."
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='html')
    return MENU_ROUTES


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    logger.info(f"menu msg id: {update.effective_message.message_id}")

    # 数据库回滚
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().close()
        del msg_db_inst_cache[update.effective_user.id]
    else:
        logger.warn(f"Cancel Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

    keyboard = [
        [ InlineKeyboardButton("Channels", callback_data=str(CHANNEL)) ],
        [ InlineKeyboardButton("My Groups", callback_data=str(TRADE)) ],
        [ InlineKeyboardButton("My Signal", callback_data=str(SIGNAL)) ],
        [ InlineKeyboardButton("Close", callback_data=str(CLOSE)) ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Please choose how to do"
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='html')
    return MENU_ROUTES


async def view_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    res = db_inst.fetch_groups_tickets_by_user_id(user_id=update.effective_user.id)
    text = 'Here are the groups you have access to and their ticket info:\n'
    if len(res) == 0:
        text += 'None.'
    else:
        for group_ticket in res:
            group_id = group_ticket[0]
            ticket = group_ticket[1]
            kol_id = group_ticket[2]
            kol = f'<a href="tg://user?id={kol_id}">{html.escape(str(kol_id))}</a>'
            group = f'[{group_id}](https://t.me/joinchat/{group_id})'
            text += f"Group: {group}\nKOL: @{kol}\nTicket: ${ticket}\n"

    await query.edit_message_text(text=text, parse_mode='markdown')
    return ConversationHandler.END


async def view_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst

    res = db_inst.fetch_point_by_user_id(user_id=update.effective_user.id)
    point = 0
    for r in res:
        point += r[0]
    text = f"Total Points: {point}\n"

    res = db_inst.fetch_groups_tickets_by_user_id(user_id=update.effective_user.id)
    text += 'Groups joined:\n'
    if len(res) == 0:
        text += 'None.'
    else:
        for group_ticket in res:
            group_id = group_ticket[0]
            group = f'[{group_id}](https://t.me/joinchat/{group_id})'
            text += f"{group}\n"
    
    # wallet
    text += 'Default Wallet:\n'
    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    if len(res) == 0:
        text += 'Not set yet.\n'
    else:
        wallet = res[0][0]
        text += f'{wallet}\n'
        w3 = Web3Helper(path=W3_PATH, id=CHAIN_ALAIS)

        btc_balance = w3.get_balance(account=wallet, token=BTC) / 10**8
        text += f'BTC: {btc_balance:.4f}\n'
        token_info = await quote_token(token='btc')
        if token_info:
            btc_usdc = btc_balance * token_info['price']

        eth_balance = w3.get_balance(account=wallet) / 10**18
        text += f'ETH: {eth_balance:.4f}\n'
        token_info = await quote_token(token='eth')
        if token_info:
            eth_usdc = eth_balance * token_info['price']
        
        usdc_balance = w3.get_balance(account=wallet, token=USDC) / 10**6
        text += f'USDC: {usdc_balance:.4f}\n'
        
        usdt_balance = w3.get_balance(account=wallet, token=USDT) / 10**6
        text += f'USDT: {usdt_balance:.4f}\n'
        
        total_balance = btc_usdc + eth_usdc + usdc_balance + usdt_balance
        text += f'Total Balance: ${total_balance:.4f}\n'
        
        res = db_inst.fetch_balance_by_address(address=wallet)
        if len(res) != 0:
            day0_balance = res[0][0]
            increase = total_balance - day0_balance
            rate = increase / day0_balance * 100
            symbol = '+' if rate > 0 else ''
            text += f"Today's P/L: {symbol}{increase:.4f} ({symbol}{rate:.2f}%)"

    keyboard = [
        [
            InlineKeyboardButton("My Copy Trading", callback_data=str(COPYTRADE))
        ],
        [
            InlineKeyboardButton("Wallet Settings", callback_data=str(WALLET))
        ],
        [
            InlineKeyboardButton("Language Settings", callback_data=str(LAN))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(CLOSE))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='markdown')
    return SIGNAL_ROUTES


async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    text = 'None'
    with open("channel_overview.txt", 'r') as f:
        text = f.read()

    await query.edit_message_text(text=text, parse_mode='html')
    return ConversationHandler.END


async def view_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    # TODO
    db_inst.fetch_strategy_id_and_address_from_strategy

    keyboard = [
        [
            InlineKeyboardButton("StrategyList", callback_data=str(STRATEGY_LIST))
        ],
        [
            InlineKeyboardButton("MyStrategy", callback_data=str(MY_STRATEGY))
        ],
        [
            InlineKeyboardButton("MyFollow", callback_data=str(MY_FOLLOW))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(CLOSE))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Please choose how to do."

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return STRATEGY_ROUTERS


async def trigger_exec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # res = db_inst.fetch_key_by_address(default_address)
    # cipher = res[0][0]
    # nonce = res[0][1]
    # pri_key = wallet.decrypt_wallet_key(a2b_hex(cipher), AES_KEY, a2b_hex(nonce))

    # w3h = Web3Helper(path=web3_path, id='arbi', priv_key=pri_key)
    # # 查询gas余额
    # if w3h.get_balance(account=w3h.wallet_address) < 21000 * 300e9:
    #     await query.message.reply_text(f"Please make your default wallet gas balance more than 0.007 ETH.")
    #     return ConversationHandler.END
    # # 查询付款余额
    # if w3h.get_balance(account=w3h.wallet_address, token=token_address) < payment_amount * 10**token_decimal:
    #     await query.message.reply_text(f"Please make your default wallet pay token balance more than {payment_amount}.")
    #     return ConversationHandler.END
    pass


async def use_wallet_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    logger.info(f"use wallet strategy query :{query}")
    await query.answer()
    data = str.split(query.data,'-')
    prefix = data[0]
    address = data[1]
    strategy_id = data[2]
    user_id=update.effective_user.id
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    db_inst.set_used_address(user_id=user_id,address=address,joined_strategy_id=strategy_id)
    strategy = db_inst.execute_with_result(f"select * from strategy where strategy_id={strategy_id} for update")
    logger.info(f"strategy = {strategy}")
    joined_wallets_str = strategy[0][3]
    import json

    joined_wallet = json.loads(joined_wallets_str)
    logger.info(f"joined wallet = {joined_wallet}")
    text = "success"
    join_info = {}
            # JOINED_WALLETS = [{"wallet_id":235,"address":"0xAD1...."，"user_id":134}]

    join_info['user_id'] = user_id
    join_info['address'] = address
    joined_wallet.append(join_info)
    joined_wallet_after_update = json.dumps(joined_wallet)
    db_inst.execute(f"update strategy set JOINED_WALLETS='{joined_wallet_after_update}' where strategy_id={strategy_id}")
    db_inst.execute("commit")
    logger.info(f"user_id:{user_id} wallet{address} join strategy{strategy_id}")
    await query.edit_message_text(text=text, reply_markup=None, parse_mode='html')
    return ConversationHandler.END

async def join_strategy_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    logger.info(f"join strategy query :{query.data}")
    await query.answer()
    data = str.split(query.data,'-')
    prefix = data[0]
    strategy_id = data[1]
    user_id=update.effective_user.id
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    wallets = db_inst.fetch_unused_address_from_user_id(user_id)
    text = "Please Choose One To Join"
    keyboard = []
    logger.info(f"wallets = {wallets}")
    for (i,wallet) in enumerate(wallets):
        address = wallet[0]
        button_text = f"Use Wallet {address}"
        logger.info(f"button_text = {button_text}")
        keyboard.append(
            [
                InlineKeyboardButton(button_text, callback_data=f"UseWallet-{address}-{strategy_id}")
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
   
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return STRATEGY_ROUTERS

async def view_my_join_strategy_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id=update.effective_user.id
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    datas = db_inst.query(f"select wallet.address,strategy.chain,strategy.dex,strategy.base_coin,strategy.quote_coin from wallet,strategy where wallet.joined_strategy_id=strategy.strategy_id and wallet.user_id={user_id} and wallet.used=true and wallet.joined_strategy_id is not null")
    text = "You Join Strategy"
    
    for (i,data) in enumerate(datas):
        address = data[0]
        chain=data[1].strip()
        dex=data[2].strip()
        base=data[3].strip()
        quote=data[4].strip()
       
        text+=f"\n wallet:{address} {chain}-{dex}-{base}-{quote} "
   
    await query.edit_message_text(text=text, reply_markup=None, parse_mode='html')
    return ConversationHandler.END


async def view_my_strategy_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id=update.effective_user.id
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    datas = db_inst.query(f"select strategy_id,chain,dex,base_coin,quote_coin,kol_wallet_address,rate from strategy where kol_user_id={user_id}")
    text = "You Have Strategy"
    
    for (i,data) in enumerate(datas):
        strategy_id = data[0]
        chain=data[1].strip()
        dex=data[2].strip()
        base=data[3].strip()
        quote=data[4].strip()
        wallet=data[5]
        rate=data[6]
        text+=f"\n {strategy_id} wallet:{wallet} {chain}-{dex}-{base}-{quote} {rate}% "
        
    keyboard = []
    for (i,data) in enumerate(datas):
        strategy_id = data[0]
        
        keyboard.append(
            [
                InlineKeyboardButton("B 10%", callback_data=f"Exec-Buy-10-{strategy_id}"),
                InlineKeyboardButton("B 50%", callback_data=f"Exec-Buy-50-{strategy_id}"),
                InlineKeyboardButton("B 100%", callback_data=f"Exec-Buy-100-{strategy_id}"),
                
                InlineKeyboardButton("S 10%", callback_data=f"Exec-Sell-10-{strategy_id}"),
                InlineKeyboardButton("S 50%", callback_data=f"Exec-Sell-50-{strategy_id}"),
                InlineKeyboardButton("S 100%", callback_data=f"Exec-Sell-100-{strategy_id}"),
            
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
   
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return STRATEGY_ROUTERS


async def exec_my_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id=update.effective_user.id
    data = query.data
    command = str.split(data,'-')
    side = command[1]
    percent = command[2]
    strategy_id = command[3]
    logger.info(f"exe my strategy side = {side} percent = {percent} strategy_id={strategy_id}")
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
    res = db_inst.fetch_key_by_address(kol_wallet_address)
    cipher = res[0][0]
    nonce = res[0][1]
    pri_key = wallet.decrypt_wallet_key(a2b_hex(cipher), AES_KEY, a2b_hex(nonce))
    
    w3h = Web3Helper(id='arbi', priv_key=pri_key)
         # 查询gas余额
    if w3h.get_balance(account=w3h.wallet_address) < 21000 * 300e9:
        await query.message.reply_text(f"Please make your default wallet gas balance more than 0.007 ETH.")
        return ConversationHandler.END 
    # 查询付款余额
    in_token_symbol = quote_coin
    in_token_address = quote_coin_address
    out_token_symbol = base_coin
    out_token_address = base_coin_address
    if side =='Sell':
        in_token_address = base_coin_address
        in_token_symbol = base_coin
        out_token_address = quote_coin_address
        out_token_symbol = quote_coin
        
    in_token_address = "0x"+in_token_address
    out_token_address = "0x"+out_token_address
    balance = w3h.get_balance(account=w3h.wallet_address, token=in_token_address)
    exec_amount = balance *  int(percent) / 100
    if chain != 'ARB':
        await query.message.reply_text(f"Only Support ARB")
        return ConversationHandler.END 
    if dex != 'UniswapV3':
        await query.message.reply_text(f"Only Support UniswapV3")
        return ConversationHandler.END 
        
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
    await query.message.reply_text(f"kol wallet exec token:{in_token_symbol}->{out_token_symbol} in_balance = {balance} side = {side} exec_amount = {exec_amount}")
    w3h.approve(in_token_address, router, None)
    if exec_amount < 100:
        await query.message.reply_text(f"Balance too small")
        return ConversationHandler.END 
    w3h.swap_exact_in(router,in_token_address,out_token_address,fee = 3000,recipient=kol_wallet_address,deadline=int(time.time()+60),amountIn=int(exec_amount),amountOutMin=10,sqrtPriceLimitX96=sqrtPriceLimitX96)
    await query.message.reply_text(text=f"doing exec {kol_wallet_address}")
    
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
            await query.message.reply_text(f"{address} Walletgas balance less than 0.007 ETH.")
            continue
    # 查询付款余额
        balance = w3h.get_balance(account=w3h.wallet_address, token=in_token_address)
        exec_amount = balance *  int(percent) / 100
        await query.message.reply_text(f"follow wallet exec token = {in_token_symbol}->{out_token_symbol} in_balance = {balance} side = {side} exec_amount = {exec_amount}")
        if exec_amount < 100:
            await query.message.reply_text(f"{address} Balance too small to exchange balance = {balance} exec balance = {exec_amount}")
            continue
        w3h.approve(in_token_address, router, None)
        w3h.swap_exact_in(router,in_token_address,out_token_address,fee = 0x1f4,recipient=kol_wallet_address,deadline=int(time.time()+60),amountIn=exec_amount,amountOutMin=10,sqrtPriceLimitX96=sqrtPriceLimitX96)

    await query.message.reply_text(text=f"all exec done", reply_markup=None, parse_mode='html')
    return ConversationHandler.END




async def view_strategy_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    strategy_list = db_inst.fetch_all_strategy()
    
    keyboard = [
        
    ]
    
    from prettytable import PrettyTable
    x = PrettyTable()
    x.field_names = ["ID", "PAIR","KOL","RATE"]
    
    for (i,strategy) in enumerate(strategy_list):
        logger.info(f"strategy_list:[{i}] = {strategy}")
        id = strategy[0]
        kol_user_id = strategy[1]
        kol_wallet = strategy[2]
        joined_wallet = strategy[3]
        rate = strategy[4]
        dex = strategy[5]
        dex = dex.strip()
        chain = strategy[6]
        chain = chain.strip()
        #
        base_coin = strategy[8]
        base_coin = base_coin.strip()
        base_coin_address = strategy[9]
        quote_coin = strategy[10]
        quote_coin = quote_coin.strip()
        quote_coin_address = strategy[11]
        
        x.add_row([id, base_coin+"-"+quote_coin+"-"+dex,kol_user_id,rate])
        
    text = x.get_string()
    
    for (i,strategy) in enumerate(strategy_list):
        keyboard.append(
            [
                InlineKeyboardButton(f"Join Startegy {i+1}", callback_data="JoinStrategy-"+str(i+1))
            ]
        )
 
    reply_markup = InlineKeyboardMarkup(keyboard)
   
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return STRATEGY_ROUTERS


async def wallet_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    logger.info(f"wallet id: {update.message.from_user.id}")
    logger.info(f"start msg id: {update.effective_message.message_id}")
    keyboard = [
        [
            InlineKeyboardButton("Create Wallet", callback_data=str(CREATE))
        ],
        [
            InlineKeyboardButton("Import Wallet", callback_data=str(IMPORT))
        ],
        [
            InlineKeyboardButton("Export Wallet", callback_data=str(EXPORT))
        ],
        [
            InlineKeyboardButton("Delete Wallet", callback_data=str(DELETE))
        ],
        [
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    db_inst.get_conn().close()
    logger.info(f"user id: {update.effective_user.id}")
    addrs = [addr[0] for addr in addrs]
    logger.info(addrs)
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    text += "Please choose how to do with your wallet, you can also send command /cancel to cancel current config <strong>or you can press 'Finish' to Store your config and exit.</strong>"
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='html')
    return WALLET_ROUTES


async def view_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Set Default Wallet", callback_data=str(SETDEFAULT))
        ],
        [
            InlineKeyboardButton("Create Wallet", callback_data=str(CREATE))
        ],
        [
            InlineKeyboardButton("Import Wallet", callback_data=str(IMPORT))
        ],
        [
            InlineKeyboardButton("Export Wallet", callback_data=str(EXPORT))
        ],
        [
            InlineKeyboardButton("Delete Wallet", callback_data=str(DELETE))
        ],
        [
            InlineKeyboardButton("Commit", callback_data=str(FINISH))
        ],
        [
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]
    if default_addr:
        text += f"Default Wallet: <code>{default_addr}</code>\n"
    else:
        text += f"Default Wallet: <code>None.</code>\nPlease select your default wallet.\n"
    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs]
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    text += "Please choose how to do with your wallet.\n<strong>Commit:</strong> to Store your config.\n<strong>Back Main Menu:</strong> to return to main menu.\n<strong>Close:</strong> to close menu.\n"

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return WALLET_ROUTES


async def create_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    # TODO: 检查是否已经有wallet和口令，如果没有设置6位口令
    logger.info(f"user: {update.effective_user.id}")
    logger.info(f"msg id: {update.effective_message.message_id}")
    if False:
        pass
    else:
        # 已经有口令了，新增wallet
        # TODO: 验证口令

        # 口令验证通过，创建私钥和地址
        (key, addr) = wallet.create_wallet(extra=update.effective_message.message_id)
        logger.info(f"pri key: {key}, addr: {addr}")

        # 加密
        (ciphertext, nonce) = wallet.encrypt_wallet_key(key, AES_KEY)
        logger.info(f"ct: {ciphertext}, nonce: {nonce}")

        # 存储到数据库
        if msg_db_inst_cache.get(update.effective_user.id, None):
            db_inst = msg_db_inst_cache[update.effective_user.id]
        else:
            logger.info((msg_db_inst_cache, update.effective_user.id))
            db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
            msg_db_inst_cache[update.effective_user.id] = db_inst
        db_inst.insert_wallet(user_id=update.effective_user.id, private_key_e=ciphertext, nonce=nonce, address=addr)

        keyboard = [
            [ InlineKeyboardButton("OK", callback_data=str(FINISH)) ],
            [ InlineKeyboardButton("Cancel", callback_data=str(CANCEL)), ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=f"Create Wallet Success!\nYour wallet private key: <code>{key}</code>\nYour wallet address: <code>{addr}</code>\n<strong>If you have remembered the key and address, I will hide them!</strong>", reply_markup=reply_markup, parse_mode='html')

        return WALLET_ROUTES


async def import_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Please input your private key:", parse_mode='html')

    return IMPORT_WALLET_ROUTES


async def import_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pri_key = update.effective_message.text
    logger.info(f"text: {pri_key}")

    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst

    err_text=f"Incorrect private key format!"
    notify_text = f"Please input correct private key again:\nIf you want to cancel this, please press <strong>cancel</strong>"

    keyboard = [
        [ InlineKeyboardButton("OK", callback_data=str(FINISH)) ],
        [ InlineKeyboardButton("Cancel", callback_data=str(CANCEL)), ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if pri_key.startswith("0x"):
        pri_key = pri_key[2:]
    if len(pri_key) == 64:
        try:
            a2b_hex(pri_key)
        except:
            await update.effective_user.send_message(text=err_text+'\n'+notify_text, parse_mode='html')
            return IMPORT_WALLET_ROUTES
        (key, addr) = wallet.import_wallet(pri_key)
        (ciphertext, nonce) = wallet.encrypt_wallet_key(private_key=key, aes_key=AES_KEY)
        db_inst.insert_wallet(user_id=update.effective_user.id, private_key_e=ciphertext, nonce=nonce, address=addr)
        success_text = f"Import Success.\nImport wallet address:\n<code>{addr}</code>\nIf you confirm the wallet import, please press <strong>'OK'</strong>. If you want to cancel this, please press <strong>cancel</strong>"
        await update.message.reply_text(text=success_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES
    else:
        await update.effective_user.send_message(text=err_text+'\n'+notify_text, parse_mode='html')
        return IMPORT_WALLET_ROUTES


async def export_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs_keys_nonces]

    export_addrs_cache[update.effective_message.message_id] = addrs_keys_nonces

    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
            keyboard.append([InlineKeyboardButton(f"{i}: {addrs[i][:6]}", callback_data=str(i))])
        text += "Please choose which wallet to export, you can also send command /cancel to cancel current config"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_NUM_ROUTES
    else:
        text += "None.\n"
        text += "You have no wallets to export."
        keyboard.append([InlineKeyboardButton("OK", callback_data=str(VIEW))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def set_default_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs_keys_nonces]

    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]
    if default_addr:
        text += f"Current Default Wallet:\n <code>{default_addr}</code>\n"
    else:
        text += f"Current Default Wallet: <code>None.</code>\n"

    export_addrs_cache[update.effective_message.message_id] = addrs_keys_nonces

    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
            keyboard.append([InlineKeyboardButton(f"{i}: {addrs[i][:6]}", callback_data=addrs[i])])
        text += "Please choose which wallet to be your new default wallet, you can also send command /cancel to cancel current config"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_SET_DEFAULT_ROUTES
    else:
        text += "None.\n"
        text += "You have no wallets to set."
        keyboard.append([InlineKeyboardButton("OK", callback_data=str(VIEW))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def delete_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []
    text = "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs_keys_nonces]

    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]

    if addrs:
        for i in range(len(addrs)):
            if addrs[i] == default_addr:
                continue
            text += f"{i}: <code>{addrs[i]}</code>\n"
            keyboard.append([InlineKeyboardButton(f"{i}: {addrs[i][:6]}", callback_data=addrs[i])])
        text += "Please choose which wallet to delete, you can also send command /cancel to cancel current config"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_DELETE_ROUTES
    else:
        text += "None.\n"
        text += "You have no wallets to delete."
        keyboard.append([InlineKeyboardButton("OK", callback_data=str(VIEW))])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES
    

async def delete_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []

    address = query.data
    
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    if address:
        res = db_inst.delete_address_from_wallet(address=address)
        logger.info(res)
        logger.info(address)
        keyboard = [
            [InlineKeyboardButton("OK", callback_data=str(FINISH))],
            [InlineKeyboardButton("Cancel", callback_data=str(CANCEL))],
        ]
        new_text = f"Delete Success.\Delete wallet address:\n<code>{address}</code>\n<strong>If you confirm, please press 'OK'.</strong>"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=new_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def set_default_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []

    address = query.data
    
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst

    if address:
        if not update.effective_user.id:
            logger.error("user id not found!")
        db_inst.set_address_from_user_by_user_id(user_id=update.effective_user.id, address=address)
        logger.info(address)
        keyboard = [
            [InlineKeyboardButton("OK", callback_data=str(FINISH))],
            [InlineKeyboardButton("Cancel", callback_data=str(CANCEL))],
        ]
        new_text = f"Set Default Wallet Success.\nDefault wallet address:\n<code>{address}</code>\n<strong>If you confirm, please press 'OK'.</strong>"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=new_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = []

    num = int(query.data)
    
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    if export_addrs_cache.get(update.effective_message.message_id, None):
        addrs_keys_nonces = export_addrs_cache[update.effective_message.message_id]
    else:
        logger.info((export_addrs_cache, update.effective_message.message_id))
        addrs_keys_nonces = db_inst.fetch_all_address_and_key_from_user_id(user_id=update.effective_user.id)
        export_addrs_cache[update.effective_message.message_id] = addrs_keys_nonces

    logger.info(addrs_keys_nonces)

    if addrs_keys_nonces:
        logger.info(query.data)
        keyboard = [
            [InlineKeyboardButton("OK", callback_data=str(FINISH))],
            [InlineKeyboardButton("Cancel", callback_data=str(CANCEL))],
        ]
        # db
        cipher = addrs_keys_nonces[num][1]
        nonce = addrs_keys_nonces[num][2]
        pri_key = wallet.decrypt_wallet_key(a2b_hex(cipher), AES_KEY, a2b_hex(nonce))
        new_text = f"Export Success.\nExport wallet address:\n<code>{addrs_keys_nonces[num][0]}</code>\nPrivate Key:\n<code>{pri_key}</code>\n<strong>If you confirm, please press 'OK' and then I will hide them.</strong>"
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=new_text, reply_markup=reply_markup, parse_mode='html')
        return WALLET_ROUTES


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()

    # 数据库commit
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().commit()
    else:
        logger.warn(f"Finish Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

    keyboard = [
        [
            InlineKeyboardButton("Set Default Wallet", callback_data=str(SETDEFAULT))
        ],
        [
            InlineKeyboardButton("Create Wallet", callback_data=str(CREATE))
        ],
        [
            InlineKeyboardButton("Import Wallet", callback_data=str(IMPORT))
        ],
        [
            InlineKeyboardButton("Export Wallet", callback_data=str(EXPORT))
        ],
        [
            InlineKeyboardButton("Delete Wallet", callback_data=str(DELETE))
        ],
        [
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Commit wallet config success!\n"

    text += "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    
    res = db_inst.fetch_address_from_user_by_id(user_id=update.effective_user.id)
    default_addr = None
    if res:
        default_addr = res[0][0]
    if default_addr:
        text += f"Current Default Wallet: <code>{default_addr}</code>\n"
    else:
        text += f"Current Default Wallet: <code>None.</code>\n"

    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs]
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"

    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='html')
    return WALLET_ROUTES


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    query = update.callback_query

    # 数据库rollback
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().rollback()
    else:
        logger.warn(f"Cancel Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

    keyboard = [
        [
            InlineKeyboardButton("Set Default Wallet", callback_data=str(SETDEFAULT))
        ],
        [
            InlineKeyboardButton("Create Wallet", callback_data=str(CREATE))
        ],
        [
            InlineKeyboardButton("Import Wallet", callback_data=str(IMPORT))
        ],
        [
            InlineKeyboardButton("Export Wallet", callback_data=str(EXPORT))
        ],
        [
            InlineKeyboardButton("Delete Wallet", callback_data=str(DELETE))
        ],
        [
            InlineKeyboardButton("Back Main Menu", callback_data=str(MENU))
        ],
        [
            InlineKeyboardButton("Close", callback_data=str(END))
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Wallet config canceled!\n"
    text += "Your wallet address:\n"
    # 检索数据库
    if msg_db_inst_cache.get(update.effective_user.id, None):
        db_inst = msg_db_inst_cache[update.effective_user.id]
    else:
        logger.info((msg_db_inst_cache, update.effective_user.id))
        db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
        msg_db_inst_cache[update.effective_user.id] = db_inst
    addrs = db_inst.fetch_all_address_from_user_id(user_id=update.effective_user.id)
    addrs = [addr[0] for addr in addrs]
    if addrs:
        for i in range(len(addrs)):
            text += f"{i}: <code>{addrs[i]}</code>\n"
    else:
        text += "None.\n"
    
    if query:
        await query.answer()
        await query.edit_message_text(text="Menu Close.")
    else:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode='html')

    return WALLET_ROUTES


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    
    user = update.effective_user
    logger.info("User %s canceled the conversation.", user.username)

    # 数据库close
    if update.effective_user.id in msg_db_inst_cache:
        msg_db_inst_cache[update.effective_user.id].get_conn().close()
        del msg_db_inst_cache[update.effective_user.id]
    else:
        logger.warn(f"Close Not Found user id: {update.effective_user.id}, cache: {msg_db_inst_cache}")

    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="Menu Close.")
    else:
        await update.message.reply_text(text="Menu Close.")

    return ConversationHandler.END


handler = ConversationHandler(
    entry_points=[CommandHandler("menu", menu_config)],
    states={
        MENU_ROUTES: [
            CallbackQueryHandler(view_signal, pattern="^" + str(SIGNAL) + "$"),
            CallbackQueryHandler(view_group, pattern="^" + str(TRADE) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(CLOSE) + "$"),
            CallbackQueryHandler(channel, pattern="^" + str(CHANNEL) + "$"),
        ],
        WALLET_NUM_ROUTES: [
            # 数字
            CallbackQueryHandler(show_wallet, pattern="^[0-9]*$")
        ],
        WALLET_DELETE_ROUTES: [
            CallbackQueryHandler(delete_wallet_address)
        ],
        WALLET_SET_DEFAULT_ROUTES: [
            CallbackQueryHandler(set_default_wallet_address)
        ],
        SIGNAL_ROUTES: [
            CallbackQueryHandler(view_wallet, pattern="^" + str(WALLET) + "$"),
            CallbackQueryHandler(view_strategy, pattern="^" + str(COPYTRADE) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(CLOSE) + "$"),
        ],
        STRATEGY_ROUTERS:[
            CallbackQueryHandler(view_my_strategy_list, pattern="^" + str(MY_STRATEGY) + "$"),
            CallbackQueryHandler(exec_my_strategy, pattern="^Exec.*$"),
            CallbackQueryHandler(view_my_join_strategy_list, pattern="^" + str(MY_FOLLOW) + "$"),
            CallbackQueryHandler(view_strategy_list, pattern="^" + str(STRATEGY_LIST) + "$"),
            CallbackQueryHandler(join_strategy_list, pattern="^JoinStrategy.*$"),
            CallbackQueryHandler(use_wallet_join, pattern="^UseWallet.*$"),
        ],
        IMPORT_WALLET_ROUTES: [
            CommandHandler("cancel", cancel), 
            MessageHandler(filters.TEXT, import_wallet_address)
        ],
        WALLET_ROUTES: [
            CallbackQueryHandler(view_wallet, pattern="^" + str(VIEW) + "$"),
            CallbackQueryHandler(set_default_wallet, pattern="^" + str(SETDEFAULT) + "$"),
            CallbackQueryHandler(create_wallet, pattern="^" + str(CREATE) + "$"),
            CallbackQueryHandler(import_wallet, pattern="^" + str(IMPORT) + "$"),
            CallbackQueryHandler(export_wallet, pattern="^" + str(EXPORT) + "$"),
            CallbackQueryHandler(delete_wallet, pattern="^" + str(DELETE) + "$"),
            CallbackQueryHandler(finish, pattern="^" + str(FINISH) + "$"),
            CallbackQueryHandler(end, pattern="^" + str(END) + "$"),
            CallbackQueryHandler(cancel, pattern="^" + str(CANCEL) + "$"),
            CallbackQueryHandler(menu, pattern="^" + str(MENU) + "$"),
        ],
    },
    fallbacks=[CommandHandler("close", end)]
)