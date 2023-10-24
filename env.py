import sys
import logging

assert len(sys.argv) == 9, "Args!"
AES_KEY = str(sys.argv[1])
DB_HOST = str(sys.argv[2])
DB_PORT = str(sys.argv[3])
DB_USER = str(sys.argv[4])
DB_NAME = str(sys.argv[5])
DB_PASSWD = str(sys.argv[6])
BOT_NAME = str(sys.argv[7])
BOT_TOKEN = str(sys.argv[8])

DEX_TOOL_KEY = '9f06d7b0e49bcc65c63234d8a1f17954'