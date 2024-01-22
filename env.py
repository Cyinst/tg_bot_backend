import sys
import logging

assert len(sys.argv) == 8, "Args!"
AES_KEY = str(sys.argv[1])
DB_HOST = str(sys.argv[2])
DB_PORT = str(sys.argv[3])
DB_USER = str(sys.argv[4])
DB_NAME = str(sys.argv[5])
DB_PASSWD = str(sys.argv[6])
BOT_TOKEN = str(sys.argv[7])
BOT_NAME = "SocialSignal"

DEX_TOOL_KEY = '9f06d7b0e49bcc65c63234d8a1f17954'

W3_PATH = "https://arb1.arbitrum.io/rpc"
CHAIN_ALAIS = 'arbi'

USDC = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831'
USDT = '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9'
BTC = '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f'

DEV_ADDR = "0xb8Cf4B76eBF4Ece05B18b7B0f6DcE13AF2BD7412"

with open("operater.txt", "r") as f:
    OPS = [int(id.strip()) for id in f.readlines()]


# 6826683306:AAEU5K-8EaV-nXzUrULpL9VecmFVgotN-jU

# TEST
# 6365184358:AAFyv7I9osL04I_otUOREtgyoDRx5JvrPsE
