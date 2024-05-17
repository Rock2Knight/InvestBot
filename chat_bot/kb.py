"""
все клавиатуры, используемые ботом
"""

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)



# Создаем меню. Добавляем кнопки, как список аргументов
menu = [
    [InlineKeyboardButton(text="📖 Получить инструкцию по работе с ботом", callback_data="get_info"),
    InlineKeyboardButton(text="🖼 Генерировать изображение", callback_data="generate_image")],
    [InlineKeyboardButton(text="💳 Купить токены", callback_data="buy_tokens"),
    InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
    [InlineKeyboardButton(text="💎 Партнёрская программа", callback_data="ref"),
    InlineKeyboardButton(text="🎁 Бесплатные токены", callback_data="free_tokens")],
    [InlineKeyboardButton(text="🔎 Помощь", callback_data="help")]
]
menu = InlineKeyboardMarkup(inline_keyboard=menu)
exit_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="◀️ Выйти в меню")]], resize_keyboard=True)
iexit_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="menu")]])

itemsAnswer = [
    [
        InlineKeyboardButton(text="1", callback_data="1_click"),
        InlineKeyboardButton(text="2", callback_data="2_click"),
        InlineKeyboardButton(text="3", callback_data="3_click"),
    ]
]
helpAnswerMenu = InlineKeyboardMarkup(inline_keyboard=itemsAnswer)

accountsButtons = [
    [
        InlineKeyboardButton(text="Выбрать из предложенных счетов", callback_data="4_click"),
        InlineKeyboardButton(text="Создать новый", callback_data="5_click"),
        InlineKeyboardButton(text="Узнать информацию по счету", callback_data="6_click"),
    ]
]
accountsMenu = InlineKeyboardMarkup(inline_keyboard=accountsButtons)

startTrade = [
    [
        InlineKeyboardButton(text="Приступить", callback_data="start_trade"),
        InlineKeyboardButton(text="Отложить", callback_data="return_to_menu"),
    ]
]
startTradeMenu = InlineKeyboardMarkup(inline_keyboard=startTrade)

returnToMenuBtn = [[InlineKeyboardButton(text="◀️ Выйти в меню", callback_data="return_to_menu")]]
returnToMenu = InlineKeyboardMarkup(inline_keyboard=returnToMenuBtn)