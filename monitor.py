import logging
import asyncio
from aiohttp import ClientSession
from env import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

# url
url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

# TG chat id
example_chat_id = -4016425542

async def notify(text, chat_id):
    d = {'chat_id': chat_id, 'text': text}
    async with ClientSession() as session:
        async with session.post(url=url, data=d) as response:
            return 200 == response.status


async def main():
    await notify("策略数据推送", chat_id=example_chat_id)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())