import csv
import re
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.errors.rpcerrorlist import ChatAdminRequiredError

from telethon_engine.client import Client
from utils.my_logger import setup_logger
from utils.similar_words import similarity_percentage


class ClientManager:
    def __init__(self):
        self.clients = []
        self.logger = setup_logger("ClientManager")

    def add_client(self, client: Client):
        """Добавить клиента в менеджер"""
        self.clients.append(client)
        self.logger.info(f"Клиент {client} добавлен в менеджер")

    def start_all(self):
        """Запустить всех клиентов"""
        for client in self.clients:
            self.logger.debug(f"Запуск клиента {client}")
            client.run_client()

    def stop_all(self):
        """Отключить всех клиентов"""
        for client in self.clients:
            self.logger.debug(f"Отключение клиента {client}")
            client.disconnect()

    def list_dialogs(self, include_channels=True):
        """
        Получить словарь {клиент: список чатов (объекты Telethon)}
        """
        result = {}
        for client in self.clients:
            chats = client.client(
                GetDialogsRequest(
                    offset_date=None,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=200,
                    hash=0,
                )
            ).chats

            filtered = []
            for c in chats:
                if getattr(c, "left", False):
                    continue
                if getattr(c, "megagroup", False):
                    filtered.append(c)
                elif include_channels and getattr(c, "broadcast", False):
                    filtered.append(c)

            result[client] = filtered
            self.logger.info(
                f"У клиента {client} найдено {len(filtered)} чатов (включая каналы={include_channels})"
            )

        return result

    def filtered_list_dialogs_by_keywords(
        self, dialogs, keywords_dir: str = "it.txt", threshold: int = 95
    ):
        """
        dialogs — результат работы list_dialogs
        Фильтрует по ключевым словам и возвращает список чатов (объектов)
        """
        with open(keywords_dir, "r") as file:
            keywords = file.readline().strip().split(",")

        seen_ids = set()
        filtered = []

        for client, chats in dialogs.items():
            for chat in chats:
                chat_id = getattr(chat, "id", None)

                if chat_id in seen_ids:
                    continue

                title = getattr(chat, "title", "") or ""
                username = getattr(chat, "username", "") or ""

                if any(
                    kw in title
                    or kw in username
                    or similarity_percentage(title, kw) > threshold
                    or similarity_percentage(username, kw) > threshold
                    for kw in keywords
                ):
                    filtered.append(chat)
                    seen_ids.add(chat_id)
                    self.logger.info(f"Добавлен чат -> {title} ({username})")

        return filtered

    def dialogs_to_json(self, dialogs):
        """
        dialogs — результат list_dialogs или список чатов
        """
        if isinstance(dialogs, dict):
            json_ready = {}
            for client, chats in dialogs.items():
                json_ready[str(client)] = [
                    {
                        "id": chat.id,
                        "title": getattr(chat, "title", None),
                        "username": getattr(chat, "username", None),
                        "type": chat.__class__.__name__,
                    }
                    for chat in chats
                ]
        else:
            json_ready = [
                {
                    "id": chat.id,
                    "title": getattr(chat, "title", None),
                    "username": getattr(chat, "username", None),
                    "type": chat.__class__.__name__,
                }
                for chat in dialogs
            ]
        return json_ready

    def scrape_chat(self, client: Client, chat, filename_prefix="members"):
        """
        Скрап участников из чата и сохранение в CSV
        """
        try:
            users = client.client.get_participants(chat, aggressive=True)
        except ChatAdminRequiredError:
            self.logger.error(f"🚫 Нужны права админа для {getattr(chat, 'title', '')}")
            return None

        fn = f"{filename_prefix}-{re.sub('-+','-', re.sub('[^a-zA-Zа-яА-Я0-9]', '-', getattr(chat, 'title', '').lower()))}.csv"

        with open(fn, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "username",
                    "user id",
                    "access hash",
                    "name",
                    "group",
                    "group id",
                    "active",
                ]
            )
            for u in users:
                active = not u.deleted and u.status is not None
                w.writerow(
                    [
                        u.username or "",
                        u.id,
                        u.access_hash,
                        f"{u.first_name or ''} {u.last_name or ''}".strip(),
                        getattr(chat, "title", ""),
                        getattr(chat, "id", ""),
                        "yes" if active else "no",
                    ]
                )

        self.logger.info(f"✅ Сохранено {len(users)} участников в {fn}")
        return fn
