# authorization.py
from telethon.sync import TelegramClient
import os

api_id   = int(os.getenv('TG_API_ID', '0'))
api_hash = os.getenv('TG_API_HASH', '')
phone    = os.getenv('TG_PHONE', '')

client = TelegramClient(phone, api_id, api_hash)
client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    code = input('Enter code: ')
    client.sign_in(phone, code)
print('OK')
