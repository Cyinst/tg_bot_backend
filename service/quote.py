from env import DEX_TOOL_KEY
from aiohttp import ClientSession
import json
import logging

coin_dict = {
    'btc': {
        'chain': 'ether', 
        'addr': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'
    },
    'eth': {
        'chain': 'ether', 
        'addr': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    },
}

headers = {
    "accept": "application/json",
    "X-API-Key": DEX_TOOL_KEY,
}

async def quote_token(token, chain=None):
    # TODO: 进一步处理干净text文本
    token = token.lower()
    chain = chain.lower() if chain else None
    if token in coin_dict:
        chain = coin_dict[token]['chain']
        coin_addr = coin_dict[token]['addr']
        return await quote_token_from_dex_tool(coin_addr, chain)
    else:
        coin_addr = token
        if not coin_addr.startswith("0x"):
            return None
        else:
            return await quote_token_from_dex_tool(coin_addr, chain)



async def quote_token_from_dex_tool(token_addr, chain):
    url = f'https://api.dextools.io/v1/token?chain={chain}&address={token_addr}'
    async with ClientSession() as session:
        async with session.get(url=url, headers=headers) as response:
            status = response.status
            if status != 200:
                return None
            res = await response.text()
            res = json.loads(res)
            data = res['data']
            reprPair = data.get('reprPair', {})
            return {'chain': data['chain'], 'address': data['address'], 'name': data['name'], 'symbol': data['symbol'], 'totalSupply': data['totalSupply'], 'decimals': data['decimals'], 'price': reprPair.get('price', None)}