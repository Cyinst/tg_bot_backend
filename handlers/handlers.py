from handlers import wallet_handler
from handlers import start_handler
from handlers import signal_handler
from handlers import join_handler
from handlers import push_handler
from handlers.group import summary_handler
from handlers.group import answer_handler
from handlers.group import greet_handler
from handlers.group import quote_handler
from handlers.group import predict_handler
from handlers.group import wake_handler

reg_handlers = [
    start_handler.handler,
    signal_handler.handler,
    wallet_handler.handler,
    summary_handler.handler,
    answer_handler.handler,
    greet_handler.handler,
    quote_handler.handler,
    predict_handler.poll_cmd,
    predict_handler.poll_answer,
    join_handler.handler,
    push_handler.push_channel_handler,
    push_handler.push_channel_overview_handler,
    wake_handler.handler
]