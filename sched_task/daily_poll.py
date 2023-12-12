from telegram import Bot, Message, Chat
from env import *
import asyncio
import time
from db.db import DB

def send_poll(user_id):
    bot_token = BOT_TOKEN

    bot = Bot(token=bot_token)

    question = 'Which topic would you like to vote for today that interests you the most?'
    options = ['DeFi', 'NFTs', 'Metaverse', 'Payments', 'Crypto']
    
    msg = None

    msg = asyncio.run(bot.send_poll(chat_id=user_id, question=question, options=options, is_anonymous=True))


def send_polls():
    db_inst = DB(host=DB_HOST, user=DB_USER, password=DB_PASSWD, database=DB_NAME)
    results = db_inst.fetch_all_user()

    bot_token = BOT_TOKEN
    bot = Bot(token=bot_token)

    question = 'Which topic would you like to vote for today that interests you the most?'
    options = ['DeFi', 'NFTs', 'Metaverse', 'Payments', 'Crypto']
    
    user_polls = {}

    # TEST
    results = [[1938113516]]

    for res in results:
        user_id = int(res[0])
        msg: Message = asyncio.run(bot.send_poll(chat_id=user_id, question=question, options=options, is_anonymous=True))
        user_polls[user_id] = msg.poll.id
        time.sleep(0.5)
    
    return user_polls


def settle_polls(user_poll):
    bot_token = BOT_TOKEN
    bot = Bot(token=bot_token)

    for user in user_poll:
        messages: Chat = asyncio.run(bot.get_chat(chat_id=user))
        print("msg")
        print(messages)

        for message in messages:
            if 'poll' in message:
                poll = message['poll']
                if poll['id'] == user_poll[user]:
                    print("投票问题:", poll['question'])
                    print("选项及结果:")
                    for option in poll['options']:
                        print(f"{option['text']}: {option['voter_count']}")