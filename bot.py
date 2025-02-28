import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Прапорець для відстеження пошуку
user_searching = {}

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
    user_searching[message.from_user.id] = True
    await message.answer("Введи назву товару для пошуку.")

# Обробник текстових повідомлень (якщо користувач у режимі пошуку)
@dp.message()
async def handle_text(message: Message):
    user_id = message.from_user.id
    if user_searching.get(user_id):
        query = message.text.lower()
        
        # Імітація бази даних
        fake_database = ["айзберг", "молоко", "хліб", "яблуко"]
        
        if query in fake_database:
            response = f"🔍 Знайдено товар: {query.capitalize()}"
        else:
            response = "❌ Товар не знайдено."

        await message.answer(response)
        user_searching[user_id] = False  # Вимикаємо режим пошуку

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

