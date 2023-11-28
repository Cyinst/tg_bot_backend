import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME
import requests
import json

logger = logging.getLogger(__name__)


async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/recommend ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    
    recommend_url = "https://api.lalam.xyz/public/" + "rick/recommendation_chat"
    data = {
        "messages_list": [
            {
                "content": text,
                "role": "user"
            }
        ]
    }
    r = requests.post(recommend_url, data=json.dumps(data))
    resp_text = r.text.replace("\\n", "\n").replace("\\t", "\t").replace("\\t", "\t").replace("\\r", "\r").replace(f'"', '')
    if r.status_code == 200:
        await update.message.reply_text(text=f"recommend:\n{resp_text}")
    else:
        logger.error(f"error query AI. {r.status_code} {r.text}")
    


handler = CommandHandler('recommend', recommend)