from handlers import wallet_handler
from handlers import start_handler
from handlers import signal_handler

reg_handlers = [start_handler.handler, signal_handler.handler, wallet_handler.handler]