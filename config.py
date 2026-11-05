import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Достаем токен
TOKEN = os.getenv("BOT_TOKEN")