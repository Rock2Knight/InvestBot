from tinkoff.invest.schemas import Quotation, MoneyValue
from tinkoff.invest.sandbox.client import SandboxClient

from work.bot import bot, TOKEN
from telebot.types import Message, User, Chat
sandbox_account_flag = False             # Состояние аккаунта в песочнице

import json

# Список имен, импортируемых из данного модуля при конструкцией "from functional import *"
__all__ = [
    'bot',
    'TOKEN',
    'Message',
    'User',
    'Chat',
    'SandboxClient',
    'Quotation',
    'getAccounts'
]

# Список типов ценных бумаг
figi = {'derivative': 'Фьючерсы и опционы', 'structured_bonds': 'структурные облигации', 'closed_fund': 'закрытые паевые фонды',
        'bond': 'облигации', 'structured_income_bonds': 'облигации со структурным доходом',
        'foreign_shares': 'иностранные акции, не включенные в котировальные списки', 'foreign_etf': 'иностранные ETF',
        'foreign_bond': 'Еврооблигации',
        'russian_shares': 'акции, не включенные в котировальные списки'}

""" Convert Quotation type to float """
def cast_money(v: Quotation):
    return v.units + v.nano / 1e9


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

""" Отладочный метод: получения информации о полях экземпляра Message """
@bot.message_handler(commands=['message'])
def getMessageInfo(message: Message):
    message_id = message.message_id
    user: User = message.from_user
    date = message.date                  # Date the message was sent in Unix time
    from_user = dict()                   # Информация об отправителе сообщения
    chat_info = dict()                   # Информация о чате
    message_info = dict()                # Информация о сообщении
    chat: Chat = message.chat            # Chat of message

    from_user["id"] = user.id                                                     # id юзера
    from_user["is_bot"] = user.is_bot                                             # бот или нет
    from_user["first_name"] = user.first_name                                     # Имя
    from_user["last_name"] = user.last_name                                       # Фамилия
    from_user["username"] = user.username                                         # Никнейм
    from_user["language_code"] = user.language_code
    from_user["is_premium"] = user.is_premium                                     # премиум-аккаунт или нет
    from_user["added_to_attachment_menu"] = user.added_to_attachment_menu
    from_user["can_join_groups"] = user.can_join_groups                           # может ли присоединяться ко всем группам
    from_user["can_read_all_group_messages"] = user.can_read_all_group_messages   # может ли читать сообщения всех групп
    from_user["supports_inline_queries"] = user.supports_inline_queries

    chat_info["id"] = chat.id
    chat_info["type"] = chat.type

    message_info["message_id"] = message_id
    message_info["date"] = date
    message_info["from_user"] = from_user
    message_info["chat_info"] = chat_info
    message_info["content_type"] = list(["text"])
    message_info["options"] = dict()
    message_info["json_string"] = ""

    with open("../message_admin_info.json", "w") as write_file:
        json.dump(message_info, write_file)


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