from handlers import wallet_handler
from handlers import start_handler
from handlers import signal_handler
from handlers.group import summary_handler
from handlers.group import answer_handler
from handlers.group import greet_handler
from handlers.group import quote_handler

reg_handlers = [start_handler.handler, signal_handler.handler, wallet_handler.handler, summary_handler.handler, answer_handler.handler, greet_handler.handler, quote_handler.handler]