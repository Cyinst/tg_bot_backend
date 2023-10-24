import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME, DEX_TOOL_KEY
import asyncio
from aiohttp import ClientSession
import json

logger = logging.getLogger(__name__)

coin_dict = {
    'btc': {
        'chain': 'ether', 
        'addr': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'
    },
    'eth': {
        'chain': 'ether', 
        'addr': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    },
}

headers = {
    "accept": "application/json",
    "X-API-Key": DEX_TOOL_KEY,
}


async def quote_token_from_dex_tool(chain, token_addr):
    url = f'https://api.dextools.io/v1/token?chain={chain}&address={token_addr}'
    async with ClientSession() as session:
        async with session.get(url=url, headers=headers) as response:
            status = response.status
            if status != 200:
                return None
            res = await response.text()
            res = json.loads(res)
            data = res['data']
            reprPair = data.get('reprPair', {})
            return {'chain': data['chain'], 'address': data['address'], 'name': data['name'], 'symbol': data['symbol'], 'totalSupply': data['totalSupply'], 'decimals': data['decimals'], 'price': reprPair.get('price', None)}


async def quote_by_text(text: str):
    # TODO: 进一步处理干净text文本
    text = text.lower()
    if text in coin_dict:
        chain = coin_dict[text]['chain']
        coin_addr = coin_dict[text]['addr']
        return await quote_token_from_dex_tool(chain, coin_addr)
    else:
        text = text.split(" ")
        if len(text) != 2:
            return None
        chain = text[0]
        coin_addr = text[1]
        if not coin_addr.startswith("0x"):
            return None
        else:
            return await quote_token_from_dex_tool(chain, coin_addr)


async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/quote ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    res = await quote_by_text(text)
    if res:
        price = '%.6g'%res['price'] if res['price'] else None
        await update.message.reply_text(text=f"Name: {res['name']}\nChain: {res['chain']}\nSymbol: {res['symbol']}\nDecimal: {res['decimals']}\nTotal Supply: {res['totalSupply']}\nAddress: {res['address']}\nPrice: {price}", parse_mode='html')
    else:
        await update.message.reply_text(text=f"No Token Information Found. Please Check Your Input.")
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=f"summary: {text}")


handler = CommandHandler('quote', quote)