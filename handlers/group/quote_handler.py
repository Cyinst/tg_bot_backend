import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME
from service import quote as quote_service

logger = logging.getLogger(__name__)


async def quote_by_text(text: str):
    # TODO: 进一步处理干净text文本
    text = text.lower()
    text = text.split(" ")
    if len(text) == 2:
        coin_addr = text[0]
        chain = text[1]
    elif len(text) == 1:
        coin_addr = text[0]
        chain = None
    else:
        return None
    return await quote_service.quote_token_from_dex_tool(coin_addr, chain)


async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/quote ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    res = await quote_by_text(text)
    if res:
        price = '%.6g'%res['price'] if res['price'] else None
        await update.message.reply_text(text=f"Name: {res['name']}\nChain: {res['chain']}\nSymbol: {res['symbol']}\nDecimal: {res['decimals']}\nTotal Supply: {res['totalSupply']}\nAddress: {res['address']}\nPrice: {price}", parse_mode='html')
    else:
        await update.message.reply_text(text=f"No Token Information Found. Please Check Your Input.")


handler = CommandHandler('quote', quote)