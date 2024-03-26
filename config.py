import os

from dotenv import load_dotenv

GPT_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"  # Путь к серверу нейросети

LOGS_PATH = "logs/logs.txt"  # Путь к файлу логов

MODEL_NAME = "yandexgpt-lite"  # Название используемой нейросети

TEMPERATURE = 0.4

MAX_MODEL_TOKENS = 128  # Максимальный размер ответа

DB_NAME = "db.sqlite"  # Название базы данных

DB_TABLE_USERS_NAME = "users"  # Название таблицы пользователей в базе

MAX_SESSIONS = 3  # Максимальное количество сессий на пользователя

MAX_TOKENS_PER_SESSION = 1000  # Максимальное количество токенов на сессию

MAX_USERS = 3  # Максимальное количество пользователей приложения

load_dotenv()

FOLDER_ID = os.getenv("folder_id")

ADMINS = os.getenv("admin_id")

BOT_TOKEN = os.getenv("token")


