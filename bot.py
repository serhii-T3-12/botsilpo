import sqlite3
import logging
import os
import csv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
import asyncio
import aiosqlite

from aiogram import Bot, Dispatcher

# 🔹 Налаштування бота
TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"
ADMIN_ID = 1299582357  # Твій Telegram ID
AUTHORIZED_USERS = {ADMIN_ID}  # Список авторизованих користувачів

# Створення бота
bot = Bot(token=TOKEN, parse_mode="HTML")

# Створення диспетчера
dp = Dispatcher()  # Токен тут не потрібен


# 🔹 Логування
logging.basicConfig(level=logging.INFO)

# 🔹 Шлях до бази даних
DB_PATH = "products.db"

# 🔹 Функція підключення до БД та виконання запитів
async def execute_query(query, params=(), fetchone=False, fetchall=False):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        result = None

        if fetchone:
            result = await cursor.fetchone()
        elif fetchall:
            result = await cursor.fetchall()

        await db.commit()
        await cursor.close()  # Закриваємо курсор перед виходом
        return result


# 🔹 Створення таблиці, якщо її немає
async def init_db():
    await execute_query("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            article TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Загальна'
        )
    """)

# 🔹 Функція перевірки адміністратора
def is_admin(user_id):
    return user_id == ADMIN_ID

# 🔹 Функція перевірки авторизації
def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS

# 🔹 Сповіщення адміністратора
async def notify_admin(action, product_name, article, category=""):
    message = f"🔔 <b>{action}</b>\n📌 Назва: {hbold(product_name)}\n🆔 Артикул: {hbold(article)}"
    if category:
        message += f"\n📂 Категорія: {hbold(category)}"
    await bot.send_message(ADMIN_ID, message)


# 📌 /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("👋 Привіт! Ось команди:\n"
                         "/search - Пошук товару\n"
                         "/search_article - Пошук за артикулом\n"
                         "/count - Кількість товарів\n"
                         "\n🔐 <b>Авторизовані користувачі:</b>\n"
                         "/add, /list, /delete, /edit, /categories\n"
                         "/export, /import, /export_category, /clear_all\n"
                         "\n/login <пароль> – авторизація\n/logout – вийти")

# 📌 /login - Авторизація
@dp.message(Command("login"))
async def login_command(message: Message):
    try:
        password = message.text.split(" ", 1)[1].strip()
        if password == "01032025":
            AUTHORIZED_USERS.add(message.from_user.id)
            await message.answer("✅ Ви успішно авторизовані! Вам доступні адміністративні команди.")
        else:
            await message.answer("❌ Невірний пароль! Спробуйте ще раз.")
    except IndexError:
        await message.answer("⚠️ Використання: /login пароль")

# 📌 /count
@dp.message(Command("count"))
async def count_products(message: Message):
    result = await execute_query("SELECT COUNT(*) FROM products", fetchone=True)
    count = result[0] if result else 0
    await message.answer(f"📦 У базі збережено {count} товарів.")

# 📌 /list
@dp.message(Command("list"))
async def list_products(message: Message):
    products = await execute_query("SELECT name, article, category FROM products", fetchall=True)

    if not products:
        await message.answer("📭 У базі немає товарів!")
        return

    response = "📋 <b>Список товарів:</b>\n"
    for name, article, category in products:
        response += f"✅ {hbold(name)} (🆔 {hbold(article)}, 📂 {hbold(category)})\n"

    await message.answer(response)


# 📌 /search_article
@dp.message(Command("search_article"))
async def search_article(message: Message):
    try:
        article = message.text.split(" ", 1)[1].strip()
        result = await execute_query("SELECT name, category FROM products WHERE article = ?", (article,), fetchone=True)
        if result:
            name, category = result
            await message.answer(f"🔍 Знайдено:\n✅ {hbold(name)} (📂 {hbold(category)})")
        else:
            await message.answer(f"⚠️ Артикул '{article}' не знайдено.")
    except IndexError:
        await message.answer("⚠️ Формат: /search_article <артикул>")

# 📌 /export_category
@dp.message(Command("export_category"))
async def export_category(message: Message):
    if not is_authorized(message.from_user.id):
        await message.answer("❌ У вас немає прав!")
        return

    try:
        category = message.text.split(" ", 1)[1].strip()
        file_path = f"{category}_products.csv"

        products = await execute_query(
            "SELECT name, article FROM products WHERE category = ?", (category,), fetchall=True
        )

        if not products:
            await message.answer(f"⚠️ У категорії '{category}' товарів немає.")
            return

        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Назва", "Артикул"])
            writer.writerows(products)

        await message.answer_document(types.FSInputFile(file_path), caption=f"📂 Товари з категорії '{category}'")

    except IndexError:
        await message.answer("⚠️ Формат: /export_category <категорія>")



# 📌 /export (експорт у CSV) - лише для адмінів
@dp.message(Command("export"))
async def export_products(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас немає прав для виконання цієї команди!")
        return

    file_path = "products.csv"

    products = await execute_query(
        "SELECT name, article, category FROM products", fetchall=True
    )

    if not products:
        await message.answer("⚠️ База товарів порожня.")
        return

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Назва", "Артикул", "Категорія"])
        writer.writerows(products)

    await message.answer_document(types.FSInputFile(file_path), caption="📂 Ваш список товарів")




# 📌 /import (імпорт із CSV) - лише для адмінів
@dp.message(Command("import"))
async def import_products(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас немає прав для виконання цієї команди!")
        return

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

                await execute_query(
                    "INSERT INTO products (name, article, category) VALUES (?, ?, ?)",
                    (name.strip(), article.strip(), category.strip()),
                    fetchone=False,
                    fetchall=False
                )

                added += 1
            except sqlite3.IntegrityError:
                pass

    await message.answer(f"✅ Імпортовано {added} товарів")



# 📌 /add
@dp.message(Command("add"))
async def add_product(message: Message):
    if not is_authorized(message.from_user.id):
        await message.answer("❌ У вас немає прав!")
        return

    try:
        text = message.text.split(" ", 1)[1].strip()
        products = [p.strip() for p in text.split("\n")]  # Розбиваємо товари по рядках

        added_count = 0
        existing_count = 0

        for product in products:
            try:
                name, article, category = map(str.strip, product.split(" - "))

                # 🔍 Перевіряємо, чи є такий товар у базі
                existing_product = await execute_query(
                    "SELECT id FROM products WHERE name = ? OR article = ?",
                    (name, article), fetchone=True
                )

                if existing_product:
                    existing_count += 1
                    continue  # Пропускаємо товар, якщо він уже є

                # ✅ Додаємо товар у базу
                await execute_query(
                    "INSERT INTO products (name, article, category) VALUES (?, ?, ?)",
                    (name, article, category)
                )

                added_count += 1

            except ValueError:
                await message.answer(f"⚠️ Неправильний формат: {product}. Формат: Назва - Артикул - Категорія")
                continue  # Пропускаємо помилковий запис

        # 🔔 Відправляємо підсумкове повідомлення
        result_msg = f"✅ Успішно додано: {added_count} товар(ів).\n"
        if existing_count:
            result_msg += f"⚠️ Пропущено (вже є в базі): {existing_count} товар(ів)."

        await message.answer(result_msg)

    except IndexError:
        await message.answer("⚠️ Формат: /add Назва - Артикул - Категорія\n"
                             "Щоб додати кілька товарів, введіть кожен з нового рядка.")




# 📌 /search
@dp.message(Command("search"))
async def search_product(message: Message):
    try:
        query = message.text.split(" ", 1)[1].strip()
        results = await execute_query("SELECT name, article, category FROM products WHERE name LIKE ?", 
                                      ('%' + query + '%',), fetchall=True)
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
    if not is_authorized(message.from_user.id):
        await message.answer("❌ У вас немає прав!")
        return

    try:
        name = message.text.split(" ", 1)[1].strip()
        await execute_query("DELETE FROM products WHERE name = ?", (name,))
        
        await message.answer(f"🗑 Товар '{hbold(name)}' видалено!")
    except IndexError:
        await message.answer("⚠️ Формат: /delete Назва")

# 📌 /edit
@dp.message(Command("edit"))
async def edit_product(message: Message):
    try:
        text = message.text.split(" ", 1)[1].strip()
        name, new_article = text.split(" - ")

        await execute_query("UPDATE products SET article = ? WHERE name = ?", (new_article.strip(), name.strip()))
       

        await message.answer(f"✏️ Товар '{hbold(name)}' оновлено!\nНовий артикул: 🆔 {hbold(new_article.strip())}")

    except IndexError:
        await message.answer("⚠️ Формат: /edit Назва - Новий артикул")

# 📌 Запуск бота
async def main():
    print("✅ Бот запущено!")
    await init_db()  # Ініціалізація бази перед стартом бота (важливо!)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
