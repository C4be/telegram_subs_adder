import os
import time as t

# Конфиг приложения
APP_STATUS = "DEV"  # ["PROD", "DEV"]
APP_DIR = os.getcwd()  # Текущая директория
SRC_DIR = os.path.join(APP_DIR, 'src')

# Конфигурация логера
LOG_DIR = os.path.join(APP_DIR, "logs", t.strftime('%d.%m.%y'))
os.makedirs(LOG_DIR, exist_ok=True)  # Создаём папку, если нет

# Считаем количество логов в папке
log_count = len([f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))])
LOG_FILE = os.path.join(LOG_DIR, f"log_{log_count + 1}.log")

# Форматы логирования
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
