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

# Логування
logging.basicConfig(level=logging.INFO)

# Підключення до SQLite
conn = sqlite3.connect("products.db")
cursor = conn.cursor()

# Створення таблиці
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
    await message.answer("👋 Привіт! Ось команди:\n"
                         "/add - Додати товар\n"
                         "/list - Список товарів\n"
                         "/search - Пошук товару\n"
                         "/delete - Видалити товар\n"
                         "/edit - Змінити товар")


# 📌 Команда /add
@dp.message(Command("add"))
async def add_product(message: Message):
    try:
        text = message.text.split(" ", 1)[1]
        items = text.split(",")

        added = []
        errors = []

        for item in items:
            try:
                name, article = item.strip().split(" - ")
                cursor.execute("INSERT INTO products (name, article) VALUES (?, ?)", (name.strip(), article.strip()))
                added.append(f"✅ {hbold(name.strip())} (🆔 {hbold(article.strip())})")
            except sqlite3.IntegrityError:
                errors.append(f"⚠️ {hbold(name.strip())} вже є")
            except ValueError:
                errors.append(f"⚠️ Неправильний формат: {hbold(item.strip())}")

        conn.commit()

        response = "\n".join(added) if added else "⚠️ Жоден товар не додано."
        if errors:
            response += "\n\n❌ Помилки:\n" + "\n".join(errors)

        await message.answer(response)

    except IndexError:
        await message.answer("⚠️ Формат: /add Назва - Артикул, Назва2 - Артикул2")


# 📌 Команда /list
@dp.message(Command("list"))
async def list_products(message: Message):
    cursor.execute("SELECT name, article FROM products")
    products = cursor.fetchall()

    if not products:
        await message.answer("⚠️ Список порожній.")
        return

    response = "📜 <b>Товари:</b>\n"
    for name, article in products:
        response += f"🔹 {hbold(name)} (🆔 {hbold(article)})\n"

    await message.answer(response)


# 📌 Команда /search
@dp.message(Command("search"))
async def search_product(message: Message):
    try:
        query = message.text.split(" ", 1)[1].strip()
        cursor.execute("SELECT name, article FROM products WHERE name LIKE ?", ('%' + query + '%',))
        results = cursor.fetchall()

        if not results:
            await message.answer(f"⚠️ '{query}' не знайдено.")
            return

        response = "🔍 <b>Знайдено:</b>\n"
        for name, article in results:
            response += f"✅ {hbold(name)} (🆔 {hbold(article)})\n"

        await message.answer(response)

    except IndexError:
        await message.answer("⚠️ Введіть назву: /search Назва")


# 📌 Команда /delete (видалення товару)
@dp.message(Command("delete"))
async def delete_product(message: Message):
    try:
        name = message.text.split(" ", 1)[1].strip()
        cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
        product = cursor.fetchone()

        if not product:
            await message.answer(f"⚠️ '{name}' не знайдено.")
            return

        cursor.execute("DELETE FROM products WHERE name = ?", (name,))
        conn.commit()
        await message.answer(f"🗑 Товар '{hbold(name)}' видалено!")

    except IndexError:
        await message.answer("⚠️ Введіть назву: /delete Назва")


# 📌 Команда /edit (редагування товару)
@dp.message(Command("edit"))
async def edit_product(message: Message):
    try:
        text = message.text.split(" ", 1)[1].strip()
        name, new_article = text.split(" - ")

        cursor.execute("SELECT * FROM products WHERE name = ?", (name.strip(),))
        product = cursor.fetchone()

        if not product:
            await message.answer(f"⚠️ '{name}' не знайдено.")
            return

        cursor.execute("UPDATE products SET article = ? WHERE name = ?", (new_article.strip(), name.strip()))
        conn.commit()

        await message.answer(f"✏️ Товар '{hbold(name)}' оновлено!\n"
                             f"Новий артикул: 🆔 {hbold(new_article.strip())}")

    except ValueError:
        await message.answer("⚠️ Формат: /edit Назва - Новий артикул")
    except IndexError:
        await message.answer("⚠️ Введіть назву та новий артикул: /edit Назва - Новий артикул")


# 📌 Запуск бота
async def main():
    print("✅ Бот запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

