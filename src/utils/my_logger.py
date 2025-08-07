import logging
from logging.handlers import RotatingFileHandler

import os
import sys

import utils.config as conf


def setup_logger(name: str = None) -> logging.Logger:
    # Проверка конфига
    if conf.APP_STATUS not in ["PROD", "DEV"]:
        raise ValueError("APP_STATUS должен быть 'PROD' или 'DEV'")
    
    # Убедимся, что директория существует
    log_dir = os.path.dirname(conf.LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    
    # Создаем  класс Logger
    logger = logging.getLogger(name)
    
    # Устанавливаем уровень логирования в соотвествии с конфигурацией
    app_status = conf.APP_STATUS
    logger_level = logging.INFO if app_status == "PROD" else logging.DEBUG
    logger.setLevel(logger_level)
    
    # Вид строки лога
    formatter = logging.Formatter(conf.LOG_FORMAT, datefmt=conf.DATE_FORMAT)

    # Обработчик для терминала
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logger_level)
    console_handler.setFormatter(formatter)

    # Обработчик для файла с ротацией
    file_handler = RotatingFileHandler(
        conf.LOG_FILE, maxBytes=10_000_000, backupCount=5, encoding="utf-8"  # 10 MB
    )
    file_handler.setLevel(logger_level)
    file_handler.setFormatter(formatter)

    # Добавляем хендлеры, если они ещё не добавлены
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    logger.propagate = False  # Чтобы не дублировать логи в root
    return logger
