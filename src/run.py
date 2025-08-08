from telethon_engine.client import Client
from telethon_engine.manager import ClientManager

import json

# получение всех акккаунтов
with open('accounts.json', 'r') as f:
    accounts = json.load(f)

# Создание и добавление клиентов
foxy_data = accounts[0]
foxy_bot = Client(
    foxy_data["name"],
    foxy_data["api_id"],
    foxy_data["api_hash"],
    foxy_data["phone"]
)

beer_data = accounts[1]
beer_bot = Client(
    beer_data["name"],
    beer_data["api_id"],
    beer_data["api_hash"],
    beer_data["phone"]
)

manager = ClientManager()
manager.add_client(foxy_bot)
manager.add_client(beer_bot)

manager.start_all()

# Получить список всех диалогов
dialogs = manager.list_dialogs_json()
print(dialogs)

print()

# Получение отфильтрованных диалогов
filtered_dialogs = manager.filtered_list_dialogs_by_keywords(dialogs)
print(filtered_dialogs)

print()

# сохранение списка диалогов
with open('data.json', 'w', encoding='utf-8') as file:
    json.dump(dialogs, file, ensure_ascii=False, indent=4)

manager.stop_all()