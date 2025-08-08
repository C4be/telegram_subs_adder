from utils.my_logger import setup_logger
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError


class Client:
    def __init__(
        self, name: str, api_id: str, api_hash: str, phone_number: str
    ) -> None:
        if not phone_number.startswith("+"):
            raise ValueError("Phone number must start with '+'")

        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone_number
        self.client_name = name
        self.client_logger = setup_logger(self.client_name)

        self.client = TelegramClient(
            session=self.phone, api_id=self.api_id, api_hash=self.api_hash
        )

    def connect(self):
        self.client.connect()
        self.client_logger.debug("Подключение установлено")

    def authorize(self, code=None):
        if not self.client.is_user_authorized():
            self.client_logger.warning("Не авторизован, отправляем код")
            self.client.send_code_request(self.phone)

            if code is None:
                code = input(f"Введите код подтверждения для {self.phone}: ")

            try:
                self.client.sign_in(self.phone, code)
                self.client_logger.info("Авторизация успешна")

            except SessionPasswordNeededError:
                self.client_logger.warning("Нужен пароль двухфакторной аутентификации")
                password = input("Введите пароль 2FA: ")
                self.client.sign_in(password=password)
                self.client_logger.info("Авторизация успешна с 2FA")

            except Exception as e:
                self.client_logger.exception(f"Ошибка авторизации: {e}")
                raise
        else:
            self.client_logger.info("Уже авторизован")

    def run_client(self):
        self.connect()
        self.authorize()

    def disconnect(self):
        self.client.disconnect()
        self.client_logger.info("Клиент отключён")

    def logout(self):
        self.client.log_out()
        self.client_logger.info("Клиент вышел из аккаунта")

    def __enter__(self):
        self.run_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def __str__(self):
        return f"Client({self.client_name})"

    def __repr__(self):
        return f"<Client {self.client_name} [{self.phone}]>"
