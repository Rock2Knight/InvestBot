import json
from typing import Union
from functools import cache
import math

from tinkoff.invest.schemas import *
from tinkoff.invest.sandbox.client import SandboxClient

from telebot.types import Message, User, Chat

from work.bot import bot, TOKEN, API_TOKEN

sandbox_account_flag = False             # Состояние аккаунта в песочнице

# Список имен, импортируемых из данного модуля при конструкцией "from functional import *"
__all__ = [
    'bot',
    'API_TOKEN',
    'TOKEN',
    'Message',
    'User',
    'Chat',
    'SandboxClient',
    'Quotation',
    'get_accounts',
    'cast_money'
]

# Список типов ценных бумаг
figi = {'derivative': 'Фьючерсы и опционы',
        'structured_bonds': 'структурные облигации',
        'closed_fund': 'закрытые паевые фонды',
        'bond': 'облигации',
        'structured_income_bonds': 'облигации со структурным доходом',
        'foreign_shares': 'иностранные акции, не включенные в котировальные списки',
        'foreign_etf': 'иностранные ETF',
        'foreign_bond': 'Еврооблигации',
        'russian_shares': 'акции, не включенные в котировальные списки'}

""" Convert Quotation/MoneyValue type to float """
@cache
def cast_money(sum: Union[Quotation, MoneyValue]) -> float:
    return sum.units + sum.nano / 1e9

def is_open_account(account: Account):
    if account.status == AccountStatus.ACCOUNT_STATUS_OPEN:
        return True
    else:
        return False


def reverse_money(sum: float) -> Quotation:
    zsum = math.floor(sum)
    drob = sum - zsum
    drob = drob * 1e9
    itog_sum = Quotation(units=zsum, nano=int(drob))
    return itog_sum

def reverse_money_mv(sum: float) -> MoneyValue:
    zsum = math.floor(sum)
    drob = sum - zsum
    drob = drob * 1e9
    itog_sum = MoneyValue(units=zsum, nano=int(drob), currency='RUB')
    return itog_sum


""" Получение всех аккаунтов в песочнице """
@bot.message_handler(commands=['accounts'])
def get_accounts(message):
    with SandboxClient(TOKEN) as client:                    # Запускаем клиент тинькофф-песочницы
        message_text = ""
        accounts_info = client.users.get_accounts()         # получаем информацию о счете

        for account in accounts_info.accounts:
            if is_open_account(account):
                message_text += str(account) + "\n\n"

        try:
            while(message_text[-1] == '\n'):
                message_text = message_text[:-1]
        except IndexError:
            message_text = "No accounts"
        finally:
            bot.send_message(message.chat.id, message_text)


""" Открытие счета в песочнице """
@bot.message_handler(commands=['open'])
def open_account(message):

    with SandboxClient(TOKEN) as client:                               # Запускаем клиент тинькофф-песочницы
        sbAccountRescponse = client.sandbox.open_sandbox_account()     # создаем счет в песочнице
        sandbox_account_flag = True                                    # устанавливаем флаг создания песочницы
        message_text = "Вы создали новый счет в песочнице!\nЕго номер: " + sbAccountRescponse.account_id
        bot.send_message(message.chat.id, message_text)

    # Сохраняем номер счета в файле
    with open("accounts_sandbox.txt", 'a', encoding="utf-8") as SanboxClients:
        SanboxClients.write(sbAccountRescponse.account_id + '\n')
        SanboxClients.close()


""" Получение информации о счете в тинькофф-песочнице """
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


""" Пополнение счета в песочнице """
@bot.message_handler(commands=['PayIn'])
def pay_in(message):
    words = message.text.split(' ')        # Разделяем текст строки на слова
    amount = float(words[2])
    account_sb_id = words[1]

    """ Пополнение счета в песочнице """
    with SandboxClient(TOKEN) as client:
        # Получаем целую и дробную часть суммы
        unit_sum = int(math.floor(amount))
        nano_sum = int(amount - unit_sum)

        pay_sum = MoneyValue(currency="RUB", units=unit_sum, nano=nano_sum)                          # Преобразование суммы к нужному типу
        client.sandbox.sandbox_pay_in(account_id=account_sb_id, amount=pay_sum)                      # Пополнение счета на сумму pay_sum
        bot.send_message(message.chat.id, f"Account {account_sb_id} was refilled by {amount} RUB")   # Высылаем в чат подтверждение пополнения


""" Закрытие счета в песочнице """
@bot.message_handler(commands=['close'])
def close_accountant(message):
    words = message.text.split(' ')        # Разделяем текст строки на слова
    account_sb_id = words[1]

    with SandboxClient(TOKEN) as client:
        client.sandbox.close_sandbox_account(account_id=account_sb_id)
        bot.send_message(message.chat.id, f"Account {account_sb_id} has been closed")
