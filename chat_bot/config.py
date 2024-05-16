"""
 файл со всеми конфигурационными параметрами, такими как токен бота и данные подключения к БД
"""
import os

from dotenv import load_dotenv

TELE_TOKEN = os.getenv("TELE_TOKEN")