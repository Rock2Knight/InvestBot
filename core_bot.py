# Мой первый телеграм-бот
# с  использованием библиотки pyTelegramBotAPI

import os
import telebot
from tinkoff.invest.sandbox.client import SandboxClient
from tinkoff.invest.schemas import MoneyValue

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


# Получение информации о счете в тинькофф-песочнице
@bot.message_handler(commands=['info'])
def get_info_accountant(message):
    client_info = None
    message_text = ""
    with SandboxClient(TOKEN) as client:          # Запускаем клиент тинькофф-песочницы
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

    bot.send_message(message.chat.id, message_text)         # Отправка сообщения в чат

""" Открытие счета в песочнице """
@bot.message_handler(commands=['open'])
def open_account(message):
    global sandbox_account_flag

    if sandbox_account_flag:                                      # если счет в песочнице уже есть,
        message_text = "У вас уже есть аккаунт в песочнице!"      # то выводим соответствующее оповщение
        bot.send_message(message.chat.id, message_text)
        return

    with SandboxClient(TOKEN) as client:                               # Запускаем клиент тинькофф-песочницы
        sbAccountRescponse = client.sandbox.open_sandbox_account()     # создаем счет в песочнице
        sandbox_account_flag = True                                    # устанавливаем флаг создания песочницы
        message_text = "Вы создали новый счет в песочнице!\nЕго номер: " + sbAccountRescponse.account_id
        bot.send_message(message.chat.id, message_text)

    # Сохраняем номер счета в файле
    with open("accounts_sandbox.txt", 'a', encoding="utf-8") as SanboxClients:
        SanboxClients.write(sbAccountRescponse.account_id + '\n')
        SanboxClients.close()


""" Пополнение счета в песочнице """
@bot.message_handler(commands=['PayIn'])
def payIn(message):
    account_sb_id = ""
    words = message.text.split(' ')        # Разделяем текст строки на слова
    amount = int(words[-1])

    """ Пополнение счета в песочнице """
    with SandboxClient(TOKEN) as client:
        accounts_info = client.users.get_accounts()          # получаем информацию о всех счетах
        account_sb_id = str(accounts_info.accounts[0].id)    # Получаем первый счет из списка

        # Получаем целую и дробную часть суммы
        unit_sum = int(amount)
        nano_sum = 0
        if amount % 1 != 0:
            nano_sum = int((str(amount % 1))[2:11])

        pay_sum = MoneyValue(currency="RUB", units=unit_sum, nano=nano_sum)                          # Преобразование суммы к нужному типу
        client.sandbox.sandbox_pay_in(account_id=account_sb_id, amount=pay_sum)                      # Пополнение счета на сумму pay_sum
        bot.send_message(message.chat.id, f"Account {account_sb_id} was refilled by {amount} RUB")   # Высылаем в чат подтверждение пополнения


""" Получение всех аккаунтов в песочнице """
@bot.message_handler(commands=['accounts'])
def getAccounts(message):
    with SandboxClient(TOKEN) as client:                    # Запускаем клиент тинькофф-песочницы
        message_text = ""
        accounts_info = client.users.get_accounts()         # получаем информацию о счете

        for account in accounts_info.accounts:
            message_text += str(account) + "\n\n"

        while(message_text[-1] == '\n'):
            message_text = message_text[:-1]

        bot.send_message(message.chat.id, message_text)


# Получаем баланс счета в песочнице по id
@bot.message_handler(commands=['portfolio'])
def getSandboxPortfolio(message):
    words = message.text.split(' ')
    in_account_id = words[-1]         # Введенный id

    with SandboxClient(TOKEN) as client:             # Запускаем клиент тинькофф-песочницы
        accounts_info = client.users.get_accounts()  # получаем информацию о счете
        isNotAccount = True

        # Проверка наличия счета в списке
        for account in accounts_info.accounts:
            if in_account_id == str(account.id):     # Если нашли нужный счет, то выходим из списка
                isNotAccount = False
                break

        # Если счета нет, то выводим сообщение об ошибке и выходим из функции
        if isNotAccount:
            bot.send_message(message.chat.id, "Неверно указан id счета")
            return

        # Формулировка сообщения
        message_text = f"Баланс счета {in_account_id}: \n"
        portfolio = client.sandbox.get_sandbox_portfolio(account_id=in_account_id)
        total_amount = portfolio.total_amount_portfolio
        message_text += "Currency: " + total_amount.currency + "\n"
        message_text += "Units: " + str(total_amount.units) + "\n"
        message_text += "Nano: " + str(total_amount.nano)

        bot.send_message(message.chat.id, message_text)   # Отправляем состояние счета

if __name__ == '__main__':
    bot.infinity_polling()