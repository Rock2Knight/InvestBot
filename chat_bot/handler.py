import asyncio
import multiprocessing as mp

from aiogram import types, F, Router, Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from app import bot
from app.bot import InvestBot

import kb
import text
import config
import chat_utils

prtfStates = {'1': False, '2': False, '3': False}
accountState = {'1': False, '2': False, '3': False}
configInfo = dict()   # Словарь для конфигурационного файла
setPrftCnt = 0
us_token = ''
account_id_active = ''
config_fname = ''
tradeProcess = None

router = Router() # создаём роутер для дальнешей привязки к нему обработчиков
investBot = None  # Экземпляр торгового робота

def runInvestBot(bot: InvestBot):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(bot.run())


# Декоратор @router.message означает, что функция является обработчиком входящих сообщений.
@router.message(Command("start"))
async def start_handler(msg: Message):
    # msg.from_user.full_name - Имя пользователя
    await msg.answer(text.greet.format(name=msg.from_user.full_name), reply_markup=kb.menu)

@router.message(F.text == "Меню")
@router.message(F.text == "Выйти в меню")
@router.message(F.text == "◀️ Выйти в меню")
async def menu(msg: Message):
    await msg.answer(text.menu, reply_markup=kb.menu)

# Функция, которая будет вызвана при нажатии на кнопку
@router.callback_query()
async def on_callback_query(callback_query: CallbackQuery):
    global prtfStates
    global accountState
    global account_id_active
    global config_fname
    global tradeProcess
    # Получаем callback_data из запроса
    callback_data = callback_query.data
    match callback_data:
        case "get_info":
            text_message = "Здравствуй, дорогой трейдер! Данное приложение\n"
            text_message += "предназначено для частных инвесторов и трейдеров для упрощения процесса трейдинга. В качестве брокера\n"
            text_message += "используется мобильное приложение Тинькофф Инвестиции.\n"
            text_message += "Вы можете настроить робота для вашего стиля торговли. Для этого предоставляется следующий набор функций:\n\n"
            text_message += "1. Настройка параметров портфеля\n"
            text_message += "2. Изменение частоты торговли\n"
            text_message += "3. Изменение уровня риска\n\n"
            text_message += "Желаем вам максимальной прибыли!"
            await callback_query.message.answer(text_message, reply_markup=kb.helpAnswerMenu)

        case "1_click":
            text_message = "Напишите ожидаемый уровень ежемесячной доходности в процентах"
            prtfStates['1'] = True
            await callback_query.message.answer(text_message)
        case "4_click":
            text_message = "Напишите ID счета, на котором желаете торговать"
            accountState['1'] = True
            await callback_query.message.answer(text_message)
        case "6_click":
            text_message = "Напишите ID счета, состояние которого хотите узнать"
            accountState['3'] = True
            await callback_query.message.answer(text_message)
        case "main_menu":
            await callback_query.message.answer(text.menu, reply_markup=kb.menu)
        case "start_trade":
            investBot = bot.InvestBot(account_id=account_id_active, filename='../settings.ini', autofill=False) # Инициализируем экземпляр торгового робота
            tradeProcess = mp.Process(target=runInvestBot, args=[investBot]) # Создаем процесс торговли торгового робота
            tradeProcess.start()  # Запускаем процесс торговли


@router.message()
async def userTextHandler(msg: Message):
    global prtfStates
    global setPrftCnt
    global us_token
    global account_id_active
    global investBot
    global config_fname
    userText = msg.text     # Текст сообщения
    userDoc = msg.document  # Прикрепленный файл
    userReturn = 0
    risk = 0

    if prtfStates['1']:
        userReturn = float(userText)  # Ожидаемый уровень доходности
        prtfStates['1'] = False
        setPrftCnt += 1
        configInfo['prtfReturn'] = userReturn
        await msg.answer('Напишите допустимый уровень риска портфеля в процентах')
    elif setPrftCnt == 1:
        risk = float(int(userText)) / 100
        setPrftCnt += 1
        configInfo['prtfRisk'] = risk
        instrumentsFile = FSInputFile("instruments.csv")
        ans_text = """Теперь необходимо введите UID о торгового инструмента, торговлю с которым хотите автоматизировать. 
        Из прикрепленного CSV-файла найдите необходимый вам торговый инструмент и напишите в чат его UID.
        """
        await msg.answer(ans_text)
        '''
        with open('instruments.csv', 'rb') as tools_file:
            await msg.reply_document(tools_file)
        '''
        await msg.reply_document(
            document=FSInputFile(path='instruments.csv')
        )
    elif setPrftCnt == 2:
        configInfo['uid'] = userText
        setPrftCnt += 1
        frequencyInfo = """
                    Выберите частоту торговли из предложенного списка (Выберите номер из списка):
                1. 1_MIN (минута)
                2. 5_MIN (5 минут)
                3. 15_MIN (15 минут)
                4. HOUR (час)
                5. DAY (1 день)
                6. 2_MIN (2 минуты)
                7. 3_MIN (3 минуты)
                8. 10_MIN (10 минут)
                9. 30_MIN (30 минут)
                10. 2_HOUR (2 часа)
                11. 4_HOUR (4 часа)
                12. WEEK (неделя)
                13. MONTH (месяц)
                """
        await msg.answer(frequencyInfo)
    elif setPrftCnt == 3:
        match userText:
            case '1':
                configInfo['timeframe'] = '1_MIN'
            case '2':
                configInfo['timeframe'] = '5_MIN'
            case '3':
                configInfo['timeframe'] = '15_MIN'
            case '4':
                configInfo['timeframe'] = 'HOUR'
            case '5':
                configInfo['timeframe'] = 'DAY'
            case '6':
                configInfo['timeframe'] = '2_MIN'
            case '7':
                configInfo['timeframe'] = '3_MIN'
            case '8':
                configInfo['timeframe'] = '10_MIN'
            case '9':
                configInfo['timeframe'] = '30_MIN'
            case '10':
                configInfo['timeframe'] = '2_HOUR'
            case '11':
                configInfo['timeframe'] = '4_HOUR'
            case '12':
                configInfo['timeframe'] = 'WEEK'
            case '13':
                configInfo['timeframe'] = 'MONTH'
        setPrftCnt += 1
        ansText = "Введите долю инструмента в портфеле от общей суммы в процентах"
        await msg.answer(ansText)
    elif setPrftCnt == 4:
        weight = float(userText) / 100
        configInfo['weight'] = weight
        setPrftCnt += 1
        ans_text = "Введите размер стоп-лосса для данного инструмента в процентах"
        await msg.answer(ans_text)
    elif setPrftCnt == 5:
        sl = float(userText) / 100
        configInfo['STOP-LOSS'] = sl
        setPrftCnt += 1
        ans_text = "Введите размер TAKE-PROFIT для данного инструмента в процентах"
        await msg.answer(ans_text)
    elif setPrftCnt == 6:
        tp = float(userText) / 100
        configInfo['TAKE-PROFIT'] = tp
        setPrftCnt += 1
        ans_text = """
            Отлично! Осталось еще чуть-чуть настроек перед началом работы. Теперь получите токен доступа типа Full-Acess
            в вашем личном кабинете на сайте Тинькофф-инвестиций. Введите его в файл ".env" и отправьте файл в чат 
        """
        await msg.answer(ans_text)
    elif setPrftCnt == 7:
        if userDoc:
            bot2 = Bot(token=config.TELE_TOKEN,
                       parse_mode=ParseMode.HTML)  # Создаем бота. Параметр parse_mode устанавливает разметку сообщений
            file_id = userDoc.file_id
            file = await bot2.get_file(file_id)
            file_path = file.file_path
            await bot2.download_file(file_path, 'target_file.txt')
            with open('target_file.txt', 'r') as target_file:
                us_token = target_file.readline().rstrip('\n')

            # Создаем файл с конфигурацией для торгового робота
            config_fname = chat_utils.create_config_file(configInfo, us_token)
            if config_fname:
                res_msg = "По данному аккаунту были найдены следующие счета:\n"
                res_msg += chat_utils.account_print(us_token)
                res_msg += "\nЖелаете ли вы торговать на одном из этих счетов или создадите новый?\n"
                setPrftCnt += 1
                await msg.answer(res_msg, reply_markup=kb.accountsMenu)
    elif setPrftCnt == 8:
        if accountState['1']:
            accountState['1'] = False
            account_id_active = userText
            await msg.answer("Приступить к торговле или отложить?", reply_markup=kb.startTradeMenu)
        elif accountState['3']:
            accountState['3'] = False
            msg_text = chat_utils.printPortfolio(us_token, userText)
            setPrftCnt += 1
            await msg.answer(msg_text, reply_markup=kb.accountsMenu)
    else:
        await msg.answer("Вам необходимо прикрепить файл к сообщению! Попробуйте еще раз")