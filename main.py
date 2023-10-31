import logging
from telegram import Update
from telegram.ext import ApplicationBuilder
from handlers.handlers import reg_handlers
from env import BOT_TOKEN
from sched_task import predict_price
import schedule

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    for h in reg_handlers:
        application.add_handler(h)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)