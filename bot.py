import sqlite3
import logging
import os
import csv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
import asyncio

# Налаштування бота
TOKEN = "ТВІЙ_ТОКЕН"
ADMIN_ID = 1299582357  # Твій Telegram ID
bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Логування
logging.basicConfig(level=logging.INFO)

# Шлях до бази даних
DB_PATH = "products.db"

# Якщо файлу немає – створюємо новий
if not os.path.exists(DB_PATH):
    open(DB_PATH, 'w').close()

# Підключення до SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Створення таблиці, якщо вона не існує
cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        article TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Загальна'
    )
""")
conn.commit()


# 🔔 Сповіщення адміна
async def notify_admin(action, product_name, article, category=""):
    message = f"🔔 <b>{action}</b>\n📌 Назва: {hbold(product_name)}\n🆔 Артикул: {hbold(article)}"
    if category:
        message += f"\n📂 Категорія: {hbold(category)}"
    await bot.send_message(ADMIN_ID, message)


# 📌 /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("👋 Привіт! Ось команди:\n"
                         "/add - Додати товар\n"
                         "/list - Список товарів\n"
                         "/search - Пошук товару\n"
                         "/delete - Видалити товар\n"
                         "/edit - Змінити товар\n"
                         "/categories - Переглянути категорії\n"
                         "/export - Експорт товарів\n"
                         "/import - Імпорт товарів")


# 📌 /export (експорт у CSV)
@dp.message(Command("export"))
async def export_products(message: Message):
    file_path = "products.csv"

    cursor.execute("SELECT name, article, category FROM products")
    products = cursor.fetchall()

    if not products:
        await message.answer("⚠️ База товарів порожня.")
        return

    # Запис у CSV
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Назва", "Артикул", "Категорія"])
        writer.writerows(products)

    # Надсилання файлу
    await message.answer_document(types.FSInputFile(file_path), caption="📂 Ваш список товарів")


# 📌 /import (імпорт із CSV)
@dp.message(Command("import"))
async def import_products(message: Message):
    if not os.path.exists("products.csv"):
        await message.answer("⚠️ Файл products.csv не знайдено.")
        return

    with open("products.csv", mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)  # Пропускаємо заголовки
        added = 0

        for row in reader:
            try:
                name, article, category = row
                cursor.execute("INSERT INTO products (name, article, category) VALUES (?, ?, ?)", 
                               (name.strip(), article.strip(), category.strip()))
                added += 1
            except sqlite3.IntegrityError:
                pass

        conn.commit()

    await message.answer(f"✅ Імпортовано {added} товарів")


# 📌 /add
@dp.message(Command("add"))
async def add_product(message: Message):
    try:
        text = message.text.split(" ", 1)[1]
        items = text.split(",")

        for item in items:
            name, article, category = map(str.strip, item.split(" - ")) if " - " in item else (item.strip(), "Невідомо", "Загальна")

            cursor.execute("INSERT INTO products (name, article, category) VALUES (?, ?, ?)", 
                           (name, article, category))
            await notify_admin("Додано новий товар", name, article, category)

        conn.commit()
        await message.answer(f"✅ Додано {len(items)} товарів")

    except IndexError:
        await message.answer("⚠️ Формат: /add Назва - Артикул - Категорія")


# 📌 /list
@dp.message(Command("list"))
async def list_products(message: Message):
    cursor.execute("SELECT name, article, category FROM products")
    products = cursor.fetchall()

    if not products:
        await message.answer("⚠️ Список порожній.")
        return

    response = "📜 <b>Товари:</b>\n"
    for name, article, category in products:
        response += f"🔹 {hbold(name)} (🆔 {hbold(article)}, 📂 {hbold(category)})\n"

    await message.answer(response)


# 📌 /search
@dp.message(Command("search"))
async def search_product(message: Message):
    try:
        query = message.text.split(" ", 1)[1].strip()
        cursor.execute("SELECT name, article, category FROM products WHERE name LIKE ?", ('%' + query + '%',))
        results = cursor.fetchall()

        if not results:
            await message.answer(f"⚠️ '{query}' не знайдено.")
            return

        response = "🔍 <b>Знайдено:</b>\n"
        for name, article, category in results:
            response += f"✅ {hbold(name)} (🆔 {hbold(article)}, 📂 {hbold(category)})\n"

        await message.answer(response)

    except IndexError:
        await message.answer("⚠️ Введіть назву: /search Назва")


# 📌 /delete
@dp.message(Command("delete"))
async def delete_product(message: Message):
    try:
        name = message.text.split(" ", 1)[1].strip()
        cursor.execute("DELETE FROM products WHERE name = ?", (name,))
        conn.commit()
        await message.answer(f"🗑 Товар '{hbold(name)}' видалено!")

    except IndexError:
        await message.answer("⚠️ Формат: /delete Назва")


# 📌 /edit
@dp.message(Command("edit"))
async def edit_product(message: Message):
    try:
        text = message.text.split(" ", 1)[1].strip()
        name, new_article = text.split(" - ")

        cursor.execute("UPDATE products SET article = ? WHERE name = ?", (new_article.strip(), name.strip()))
        conn.commit()

        await message.answer(f"✏️ Товар '{hbold(name)}' оновлено!\nНовий артикул: 🆔 {hbold(new_article.strip())}")

    except IndexError:
        await message.answer("⚠️ Формат: /edit Назва - Новий артикул")


# 📌 Запуск бота
async def main():
    print("✅ Бот запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


