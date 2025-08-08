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

# Запустить клиентов
manager.start_all()

# Получаем все диалоги
dialogs = manager.list_dialogs(include_channels=True)

# Фильтруем по ключевым словам
filtered_dialogs = manager.filtered_list_dialogs_by_keywords(dialogs)

# Сохраняем в JSON
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(manager.dialogs_to_json(filtered_dialogs), f, ensure_ascii=False, indent=2)

# Скрап участников из первого найденного чата
if filtered_dialogs:
    manager.scrape_chat(manager.clients[0], filtered_dialogs[2])