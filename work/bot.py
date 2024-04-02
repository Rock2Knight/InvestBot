import telebot
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('TELE_TOKEN')     # Токен бота
TOKEN = os.getenv('TINKOFF_TOKEN')      # Токен тинькофф-инвестиций

bot = telebot.TeleBot(API_TOKEN)         # сам бот