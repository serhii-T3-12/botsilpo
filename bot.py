import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

# Токен бота
TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"

# Ініціалізація бота і диспетчера
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Обробник команди /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привіт! Я твій бот.")

# Обробник команди /list
@dp.message(Command("list"))
async def list_command(message: Message):
    commands = "/start - Почати\n/list - Показати команди\n/search - Пошук за назвою"
    await message.answer(f"Доступні команди:\n{commands}")

# Обробник команди /search
@dp.message(Command("search"))
async def search_command(message: Message):
    await message.answer("Введи назву товару для пошуку.")

# Головна функція запуску бота
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущено...")
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())


