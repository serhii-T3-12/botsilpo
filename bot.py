import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
import asyncio

# Налаштування бота
TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Логування помилок
logging.basicConfig(level=logging.INFO)

# Підключення до бази даних SQLite
conn = sqlite3.connect("products.db")
cursor = conn.cursor()

# Створення таблиці для збереження товарів
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        article TEXT NOT NULL
    )
""")
conn.commit()


# 📌 Команда /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("👋 Привіт! Я твій бот. Ось доступні команди:\n"
                         "/add - Додати товар\n"
                         "/list - Показати всі товари\n"
                         "/search - Пошук за назвою")


# 📌 Команда /add (додавання одного або кількох товарів)
@dp.message(Command("add"))
async def add_multiple_products(message: Message):
    try:
        text = message.text.split(" ", 1)[1]  # Отримуємо текст після команди
        items = text.split(",")  # Розбиваємо товари через кому

        added_products = []
        errors = []

        for item in items:
            try:
                name, article = item.strip().split(" - ")  # Розділяємо назву і артикул
                cursor.execute("INSERT INTO products (name, article) VALUES (?, ?)", (name.strip(), article.strip()))
                added_products.append(f"✅ {hbold(name.strip())} (🆔 {hbold(article.strip())})")
            except sqlite3.IntegrityError:
                errors.append(f"⚠️ {hbold(name.strip())} вже є в базі")
            except ValueError:
                errors.append(f"⚠️ Неправильний формат: {hbold(item.strip())}")

        conn.commit()

        response = "\n".join(added_products) if added_products else "⚠️ Жоден товар не додано."
        if errors:
            response += "\n\n❌ Помилки:\n" + "\n".join(errors)

        await message.answer(response)

    except IndexError:
        await message.answer("⚠️ Формат команди: /add Назва1 - Артикул1, Назва2 - Артикул2")


# 📌 Команда /list (показ всіх товарів)
@dp.message(Command("list"))
async def list_products(message: Message):
    cursor.execute("SELECT name, article FROM products")
    products = cursor.fetchall()

    if not products:
        await message.answer("⚠️ Список товарів порожній.")
        return

    response = "📜 <b>Список товарів:</b>\n"
    for name, article in products:
        response += f"🔹 {hbold(name)} (🆔 {hbold(article)})\n"

    await message.answer(response)


# 📌 Команда /search (пошук товару)
@dp.message(Command("search"))
async def search_product(message: Message):
    try:
        query = message.text.split(" ", 1)[1].strip()
        cursor.execute("SELECT name, article FROM products WHERE name LIKE ?", ('%' + query + '%',))
        results = cursor.fetchall()

        if not results:
            await message.answer(f"⚠️ Товар '{query}' не знайдено.")
            return

        response = "🔍 <b>Результати пошуку:</b>\n"
        for name, article in results:
            response += f"✅ {hbold(name)} (🆔 {hbold(article)})\n"

        await message.answer(response)

    except IndexError:
        await message.answer("⚠️ Введіть назву товару для пошуку: /search Назва")


# 📌 Запуск бота
async def main():
    print("✅ Бот запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

