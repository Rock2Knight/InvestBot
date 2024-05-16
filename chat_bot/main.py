"""
Точка входа, код запуска бота и инициализации всех остальных модулей
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher  # основной модуль библиотеки aiogram, из которого мы импортируем классы Bot и Dispatcher
from aiogram.enums.parse_mode import ParseMode # содержит настройки разметки сообщений (HTML, Markdown)
from aiogram.fsm.storage.memory import MemoryStorage # хранилища данных для состояний пользователей

import config
from handler import router


async def main():
    bot = Bot(token=config.TELE_TOKEN, parse_mode=ParseMode.HTML) # Создаем бота. Параметр parse_mode устанавливает разметку сообщений
    dp = Dispatcher(storage=MemoryStorage()) # параметр MemoryStorage() говорит, что все данные, которые не сохраняются в БД, будут стерты при перезапуске
    dp.include_router(router)  # Подключение обработчиков
    await bot.delete_webhook(drop_pending_updates=True) # Удаляет все обновления, которые пришли после заврешения работы бота
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())