import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from env import BOT_NAME
import requests
import json

logger = logging.getLogger(__name__)


async def recommend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/recommend ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    
    recommend_url = "https://api.lalam.xyz/public/" + "social_signal/recommendation_chat"
    data = {
        "messageslist": {
            "messages_list": [
                {
                    "content": text,
                    "role": "user"
                }
            ]
        },
        "secret": "social",
        "quick": False
    }
    r = requests.post(recommend_url, data=json.dumps(data))
    if r.status_code == 200:
        resp_text = json.loads(r.text)
        if "recommendation" in resp_text:
            await update.message.reply_text(text=f"{resp_text['answer']}\nrecommend:\n{resp_text['recommendation']}")
        else:
            await update.message.reply_text(text=f"{resp_text['answer']}")
    else:
        logger.error(f"error query AI. {r.status_code} {r.text}")
    


handler = CommandHandler('recommend', recommend)