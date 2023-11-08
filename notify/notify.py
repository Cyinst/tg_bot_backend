import logging
from aiohttp import ClientSession
from env import BOT_TOKEN

logger = logging.getLogger(__name__)

# url
url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

# TG chat id
example_chat_id = -4016425542

async def notify(text, chat_id, parse_mode=None):
    d = {'chat_id': chat_id, 'text': text}
    if parse_mode:
        d['parse_mode'] = parse_mode
    async with ClientSession() as session:
        async with session.post(url=url, data=d) as response:
            return 200 == response.status