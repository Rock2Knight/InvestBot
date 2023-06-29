# Мой первый телеграм-бот
# с  использованием библиотки pyTelegramBotAPI

import os
import telebot
from tinkoff.invest.sandbox.client import SandboxClient

API_TOKEN = os.environ['TELE_TOKEN']     # Токен бота
TOKEN = os.environ['TINKOFF_TOKEN']      # Токен тинькофф-инвестиций

bot = telebot.TeleBot(API_TOKEN)         # сам бот
sandbox_account_flag = False             # Состояние аккаунта в песочнице

# Список типов ценных бумаг
figi = {'derivative': 'Фьючерсы и опционы', 'structured_bonds': 'структурные облигации', 'closed_fund': 'закрытые паевые фонды',
        'bond': 'облигации', 'structured_income_bonds': 'облигации со структурным доходом',
        'foreign_shares': 'иностранные акции, не включенные в котировальные списки', 'foreign_etf': 'иностранные ETF',
        'foreign_bond': 'Еврооблигации',
        'russian_shares': 'акции, не включенные в котировальные списки'}

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am TraderBot.
I can help you to deal with shares, bonds and other. To get info about account, send \"info\"\
""")

"""
# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, message.text)
"""

# Получение информации о счете в тинькофф-песочнице
@bot.message_handler(commands=['info'])
def get_info_accountant(message):
    client_info = None
    message_text = ""
    with SandboxClient(TOKEN) as client:   # Создаем аккаунт тинькофф-инвестиций
        client_info = client.users.get_info()     # получаем информацию о счете

    if not client_info.prem_status:
        message_text += "Статус: Без премиума\n"
    else:
        message_text += "Статус: C премиумом\n"

    if not client_info.qual_status:
        message_text += "Тип инвестора: неквалифицированный\n"
    else:
        message_text += "Тип инвестора: квалифицированный\n"

    message_text += "Тариф: песочница\nДоступные для торговли бумаги:\n"
    for name in client_info.qualified_for_work_with:
        if name in figi.keys():
            message_text += figi[name] + '\n'

    bot.send_message(message.chat.id, message_text)

""" Открытие счета в песочнице """
@bot.message_handler(commands=['open'])
def open_account(message):
    global sandbox_account_flag

    if sandbox_account_flag:                                      # если счет в песочнице уже есть,
        message_text = "У вас уже есть аккаунт в песочнице!"      # то выводим соответствующее оповщение
        bot.send_message(message.chat.id, message_text)
        return

    with SandboxClient(TOKEN) as client:                               # Создаем аккаунт тинькофф-инвестиций
        sbAccountRescponse = client.sandbox.open_sandbox_account()     # создаем счет в песочнице
        sandbox_account_flag = True                                    # устанавливаем флаг создания песочницы
        message_text = "Вы создали новый счет в песочнице!\nЕго номер: " + sbAccountRescponse.account_id
        bot.send_message(message.chat.id, message_text)

    # Сохраняем номер счета в файле
    with open("accounts_sandbox.txt", 'a', encoding="utf-8") as SanboxClients:
        SanboxClients.write(sbAccountRescponse.account_id + '\n')
        SanboxClients.close()


@bot.message_handler(commands=['PayIn'])
def pay_in(message):

if __name__ == '__main__':
    bot.infinity_polling()