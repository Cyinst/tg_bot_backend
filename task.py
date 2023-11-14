import logging
import asyncio
from aiohttp import ClientSession
import schedule
import threading
import time
from sched_task import predict_price
from env import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


# def run_threaded(job_func):
#     job_thread = threading.Thread(target=job_func)
#     job_thread.start()


# async def task():
#     # schedule.every(5).seconds.do(run_threaded, predict_price.run_settle_predict)
#     # scheduler_thread = threading.Thread(target=run_scheduler)
#     # scheduler_thread.start()
#     while True:
#         schedule.run_pending()
#         time.sleep(1)
#         # await asyncio.sleep(1)
#     # while True:
#         # schedule.run_pending()


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(task())
    schedule.every(5).seconds.do(predict_price.run_settle_predict)
    while True:
        schedule.run_pending()
        time.sleep(1)