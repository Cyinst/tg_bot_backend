import logging
from telegram.ext import ApplicationBuilder
from handlers.handlers import reg_handlers

token = '6365184358:AAFyv7I9osL04I_otUOREtgyoDRx5JvrPsE'

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()

    for h in reg_handlers:
        application.add_handler(h)
    
    application.run_polling()