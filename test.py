import time
from service.equity import set_wallet_equity_snap,get_wallet_equity_snap
from service.equity import equity_list
from service.swap_tracer import find_swaps
from notify import notify
import asyncio


async def main():
    await set_wallet_equity_snap(int(time.time())/(60 * 60 * 24),"test_address",435.0)
    await get_wallet_equity_snap(int(time.time())/(60 * 60 * 24),"test_address")

if __name__ == '__main__':
    # import asyncio
    # loop = asyncio.get_event_loop()
    # res = loop.run_until_complete(main())
    # loop.close()
    
    # e_lst = equity_list(address_list= ['0xE4eDb277e41dc89aB076a1F049f4a3EfA700bCE8', '0x673A2265730EAA1AFA987d43F0EE46E48A5d4308'])
    # print(e_lst)
    # print(find_swaps(154898413))
    asyncio.run(notify.notify(text="@测试机器人", chat_id=-4016425542))
