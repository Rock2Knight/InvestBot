import telebot
import os

API_TOKEN = os.getenv('TELE_TOKEN')     # Токен бота
#API_TOKEN = os.environ['TELE_TOKEN']     # Токен бота
TOKEN = os.getenv('TINKOFF_TOKEN')      # Токен тинькофф-инвестиций

bot = telebot.TeleBot(API_TOKEN)         # сам бот