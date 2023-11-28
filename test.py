import time
from service.equity import set_wallet_equity_snap,get_wallet_equity_snap



async def main():
    await set_wallet_equity_snap(int(time.time())/(60 * 60 * 24),"test_address",435.0)
    await get_wallet_equity_snap(int(time.time())/(60 * 60 * 24),"test_address")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(main())
    loop.close()
    