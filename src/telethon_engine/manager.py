import csv
import re
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import InputPeerEmpty, ChannelParticipantsSearch, ChannelParticipantsRecent
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

    # def scrape_all_chats(self, chats_by_client, filename="members-all.csv"):
    #     all_users = {}
    #     for client, chats in chats_by_client.items():
    #         for chat in chats:
    #             try:
    #                 self.logger.info(f"Обрабатываем чат {chat.title} ({chat.id}), тип {chat.__class__.__name__}")

    #                 if chat.__class__.__name__ == 'Chat':
    #                     # Обычный чат
    #                     full_chat = client.client(GetFullChatRequest(chat_id=chat.id))
    #                     users = full_chat.users
    #                 else:
    #                     # Канал или супергруппа
    #                     users = client.client.get_participants(chat, aggressive=True)

    #                 self.logger.info(f"Получено {len(users)} участников")

    #             except ChatAdminRequiredError:
    #                 self.logger.warning(f"Нет прав админа для {chat.title}, пробуем частично")
    #                 users = []
    #                 # твоя логика с GetParticipantsRequest с фильтрами
    #             except Exception as e:
    #                 self.logger.error(f"Ошибка при получении участников из {chat.title}: {e}")
    #     # for client, chats in chats_by_client.items():
    #     #     self.logger.info(f"Обрабатываем клиента {client.name} с {len(chats)} чатами")
    #     #     for chat in chats:
    #     #         try:
    #     #             # Пробуем получить всех участников (требует права админа)
    #     #             users = client.client.get_participants(chat, aggressive=True)
    #     #         except ChatAdminRequiredError:
    #     #             self.logger.warning(f"🚫 Нет прав админа для {getattr(chat, 'title', '')}, берем частичных участников")
    #     #             users = []
    #     #             # Получаем участников через ChannelParticipantsRecent и поиск
    #     #             try:
    #     #                 limit = 200  # ограничение, можно увеличить при желании
    #     #                 recent = client.client(GetParticipantsRequest(
    #     #                     channel=chat,
    #     #                     filter=ChannelParticipantsRecent(),
    #     #                     offset=0,
    #     #                     limit=limit,
    #     #                     hash=0
    #     #                 ))
    #     #                 users.extend(recent.users)

    #     #                 # Для расширения списка — поиск по пустой строке
    #     #                 search = client.client(GetParticipantsRequest(
    #     #                     channel=chat,
    #     #                     filter=ChannelParticipantsSearch(""),
    #     #                     offset=0,
    #     #                     limit=limit,
    #     #                     hash=0
    #     #                 ))
    #     #                 users.extend(search.users)
    #     #             except Exception as e:
    #     #                 self.logger.error(f"Ошибка при частичном получении участников из {getattr(chat, 'title', '')}: {e}")

    #             for u in users:
    #                 # Уникальность по user id
    #                 if u.id not in all_users:
    #                     active = not u.deleted and u.status is not None
    #                     all_users[u.id] = {
    #                         "username": u.username or "",
    #                         "user_id": u.id,
    #                         "access_hash": u.access_hash,
    #                         "name": f"{u.first_name or ''} {u.last_name or ''}".strip(),
    #                         "group": getattr(chat, "title", ""),
    #                         "group_id": getattr(chat, "id", ""),
    #                         "active": "yes" if active else "no",
    #                     }

    #     # Записываем всех уникальных пользователей в один CSV
    #     with open(filename, "w", encoding="utf-8", newline="") as f:
    #         w = csv.writer(f)
    #         w.writerow(["username", "user id", "access hash", "name", "group", "group id", "active"])
    #         for u in all_users.values():
    #             w.writerow([
    #                 u["username"],
    #                 u["user_id"],
    #                 u["access_hash"],
    #                 u["name"],
    #                 u["group"],
    #                 u["group_id"],
    #                 u["active"],
    #             ])

    #     self.logger.info(f"✅ Сохранено {len(all_users)} уникальных участников в {filename}")
    #     return filename

    def scrape_all_chats(self, chats_by_client, filename="members-all.csv"):
        all_users = {}
        for client, chats in chats_by_client.items():
            self.logger.info(f"Обрабатываем клиента {client.name} с {len(chats)} чатами")
            for chat in chats:
                try:
                    # Получаем полноценный объект (с access_hash), чтобы корректно получить участников
                    entity = client.client.get_entity(chat.id)

                    # Получаем участников
                    users = client.client.get_participants(entity, aggressive=True)
                    self.logger.info(f"Получено {len(users)} участников из {chat.title}")

                except ChatAdminRequiredError:
                    self.logger.warning(f"🚫 Нет прав админа для {chat.title}, пытаемся получить частично")
                    users = []
                    try:
                        limit = 200
                        recent = client.client(GetParticipantsRequest(
                            channel=entity,
                            filter=ChannelParticipantsRecent(),
                            offset=0,
                            limit=limit,
                            hash=0
                        ))
                        users.extend(recent.users)

                        search = client.client(GetParticipantsRequest(
                            channel=entity,
                            filter=ChannelParticipantsSearch(""),
                            offset=0,
                            limit=limit,
                            hash=0
                        ))
                        users.extend(search.users)
                        self.logger.info(f"Получено {len(users)} частичных участников из {chat.title} после ограничения прав")

                    except Exception as e:
                        self.logger.error(f"Ошибка при частичном получении участников из {chat.title}: {e}")

                except Exception as e:
                    self.logger.error(f"Ошибка при получении участников из {chat.title}: {e}")
                    continue

                # Сохраняем уникальных пользователей
                for u in users:
                    if u.id not in all_users:
                        active = not u.deleted and u.status is not None
                        all_users[u.id] = {
                            "username": u.username or "",
                            "user_id": u.id,
                            "access_hash": u.access_hash,
                            "name": f"{u.first_name or ''} {u.last_name or ''}".strip(),
                            "group": chat.title,
                            "group_id": chat.id,
                            "active": "yes" if active else "no",
                        }

        # Записываем в CSV
        with open(filename, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["username", "user id", "access hash", "name", "group", "group id", "active"])
            for u in all_users.values():
                w.writerow([
                    u["username"],
                    u["user_id"],
                    u["access_hash"],
                    u["name"],
                    u["group"],
                    u["group_id"],
                    u["active"],
                ])

        self.logger.info(f"✅ Сохранено {len(all_users)} уникальных участников в {filename}")
        return filename