import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import requests
import json
from env import BOT_NAME

logger = logging.getLogger(__name__)


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text.replace("/answer ", "").replace(f"@{BOT_NAME}", "").replace("  ", " ").strip()
    
    recommend_url = "https://api.lalam.xyz/public/" + "social_signal/qa_chat"
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
        await update.message.reply_text(text=f"answer:\n{resp_text['answer']}")
    else:
        logger.error(f"error query AI. {r.status_code} {r.text}")

handler = CommandHandler('answer', answer)