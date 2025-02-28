import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Підключення до бази даних
conn = sqlite3.connect("products.db")
cursor = conn.cursor()

# Створення таблиці, якщо її немає
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    article TEXT
)
""")
conn.commit()


# 📌 Стартова команда
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привіт! Я твій бот для управління товарами! 🛒\n\n"
                         "Команди:\n"
                         "/list - Показати всі товари\n"
                         "/search <назва> - Пошук товару\n"
                         "/add <назва> - <артикул> - Додати товар")


# 📌 Додавання нового товару
@dp.message(Command("add"))
async def add_product(message: Message):
    try:
        text = message.text.split(" ", 1)[1]  # Беремо текст після команди
        name, article = text.split(" - ")  # Розділяємо назву і артикул

        cursor.execute("INSERT INTO products (name, article) VALUES (?, ?)", (name.strip(), article.strip()))
        conn.commit()

        await message.answer(f"✅ Товар {hbold(name.strip())} додано!\n🆔 Артикул: {hbold(article.strip())}")
    except (IndexError, ValueError):
        await message.answer("⚠️ Формат команди: /add Назва - Артикул")
    except sqlite3.IntegrityError:
        await message.answer("⚠️ Такий товар вже існує!")


# 📌 Пошук товару за назвою
@dp.message(Command("search"))
async def search_product(message: Message):
    try:
        query = message.text.split(" ", 1)[1].strip()
        cursor.execute("SELECT name, article FROM products WHERE name LIKE ?", (f"%{query}%",))
        result = cursor.fetchall()

        if result:
            response = "🔎 Знайдені товари:\n\n"
            for name, article in result:
                response += f"✅ {hbold(name)}\n🆔 Артикул: {hbold(article)}\n\n"
            await message.answer(response)
        else:
            await message.answer("⚠️ Нічого не знайдено.")
    except IndexError:
        await message.answer("⚠️ Формат команди: /search Назва")


# 📌 Виведення всіх товарів
@dp.message(Command("list"))
async def list_products(message: Message):
    cursor.execute("SELECT name, article FROM products")
    products = cursor.fetchall()

    if products:
        response = "📜 Усі товари:\n\n"
        for name, article in products:
            response += f"✅ {hbold(name)}\n🆔 Артикул: {hbold(article)}\n\n"
        await message.answer(response)
    else:
        await message.answer("⚠️ Товарів поки що немає!")


# 📌 Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

