import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME
import requests
import json

logger = logging.getLogger(__name__)


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/summary ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    
    summary_url = "https://api.lalam.xyz/public/" + "social_signal/summary_opinion"
    data = {
        "content": text,
        "secret": "social",
        "quick": False
    }
    r = requests.post(summary_url, data=json.dumps(data))
    resp_text = r.text
    if r.status_code == 200:
        resp = json.loads(resp_text)
        await update.message.reply_text(text=f"summary:\n{resp['answer']}")
    else:
        logger.error(f"error query AI. {r.status_code} {r.text}")
    


handler = CommandHandler('summary', summary)