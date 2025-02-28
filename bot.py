import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Режими очікування вводу
user_searching = {}
user_adding = {}

# База товарів (Назва -> Артикул)
product_database = {
    "айзберг": "540258",
    "молоко": "M67890",
    "хліб": "H54321",
    "яблуко": "Y98765",
}

# Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привіт! Я твій бот для роботи з товарами.")

# Команда /list
@dp.message(Command("list"))
async def list_command(message: Message):
    commands = (
        "/start - Почати\n"
        "/list - Показати команди\n"
        "/search - Пошук за назвою\n"
        "/add - Додати новий товар"
    )
    await message.answer(f"Доступні команди:\n{commands}")

# Команда /search
@dp.message(Command("search"))
async def search_command(message: Message):
    user_searching[message.from_user.id] = True
    await message.answer("🔍 Введи назву товару для пошуку:")

# Команда /add
@dp.message(Command("add"))
async def add_command(message: Message):
    user_adding[message.from_user.id] = True
    await message.answer("➕ Введи назву нового товару та артикул у форматі: назва - артикул")

# Обробка текстових повідомлень
@dp.message()
async def handle_text(message: Message):
    user_id = message.from_user.id
    text = message.text.lower()

    # Обробка пошуку товару
    if user_searching.get(user_id):
        if text in product_database:
            response = f"✅ Товар знайдено: <b>{text.capitalize()}</b>\n🆔 Артикул: <code>{product_database[text]}</code>"
        else:
            response = "❌ Товар не знайдено."
        await message.answer(response)
        user_searching[user_id] = False  # Вимикаємо режим пошуку

    # Обробка додавання нового товару
    elif user_adding.get(user_id):
        try:
            name, article = map(str.strip, text.split("-", 1))
            if name in product_database:
                response = "⚠️ Цей товар вже є в базі!"
            else:
                product_database[name] = article
                response = f"✅ Товар <b>{name.capitalize()}</b> додано!\n🆔 Артикул: <code>{article}</code>"
        except ValueError:
            response = "⚠️ Невірний формат! Використовуй: <code>назва - артикул</code>"
        await message.answer(response)
        user_adding[user_id] = False  # Вимикаємо режим додавання

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущено...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


