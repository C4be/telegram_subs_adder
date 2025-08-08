from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

from telethon_engine.client import Client
from utils.my_logger import setup_logger


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
        Получить словарь {клиент: список чатов}
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
    
    def list_dialogs_json(self, include_channels=True):
        dialogs_dict = self.list_dialogs(include_channels)
        json_ready = {}

        for client, chats in dialogs_dict.items():
            client_name = str(client)
            json_ready[client_name] = []
            for chat in chats:
                json_ready[client_name].append({
                    "id": chat.id,
                    "title": getattr(chat, "title", None),
                    "username": getattr(chat, "username", None),
                    "type": chat.__class__.__name__
                })
        return json_ready
