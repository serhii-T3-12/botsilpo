import sqlite3
import logging
import os
import csv
import datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold
import asyncio
import aiosqlite


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
            await message.answer(
                "✅ Ви успішно авторизовані! Вам доступні адміністративні команди.",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Невірний пароль! Спробуйте ще раз.", parse_mode="HTML")
    except IndexError:
        await message.answer("⚠️ Використання: <code>/login пароль</code>", parse_mode="HTML")


# 📌 /count
@dp.message(Command("count"))
async def count_products(message: Message):
    result = await execute_query("SELECT COUNT(*) FROM products", fetchone=True)
    count = result[0] if result else 0
    await message.answer(f"📦 У базі збережено {count} товарів.")


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
        errors = []

        for product in products:
            try:
                name, article, category = map(str.strip, product.split(" - "))

                if not name or not article.isdigit():  # Перевіряємо, що артикул - число
                    errors.append(product)
                    continue

                existing_product = await execute_query(
                    "SELECT id FROM products WHERE name = ? OR article = ?",
                    (name, article), fetchone=True
                )

                if existing_product:
                    existing_count += 1
                    continue  # Пропускаємо товар, якщо він уже є

                await execute_query(
                    "INSERT INTO products (name, article, category) VALUES (?, ?, ?)",
                    (name, article, category)
                )
                added_count += 1

            except ValueError:
                errors.append(product)
                continue  # Пропускаємо помилковий запис

        result_msg = f"✅ Успішно додано: {added_count} товар(ів).\n"
        if existing_count:
            result_msg += f"⚠️ Пропущено (вже є в базі): {existing_count} товар(ів).\n"
        if errors:
            result_msg += f"❌ Помилки у записах: {', '.join(errors)}."

        await message.answer(result_msg)

    except IndexError:
        await message.answer("⚠️ Формат: /add Назва - Артикул - Категорія\n"
                             "Щоб додати кілька товарів, введіть кожен з нового рядка.")


class ClearAllState(StatesGroup):
    waiting_for_password = State()
    waiting_for_confirmation = State()

CLEAR_ALL_PASSWORD = "05012025"

@dp.message(Command("clear_all"))
async def clear_all_products(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас немає прав!")
        return

    await message.answer("⚠️ Введіть пароль для підтвердження видалення всіх товарів.")
    await state.set_state(ClearAllState.waiting_for_password)

@dp.message(ClearAllState.waiting_for_password)
async def confirm_password(msg: Message, state: FSMContext):
    if msg.text == CLEAR_ALL_PASSWORD:
        await msg.answer("🔴 Ви точно хочете видалити всі товари? Відповідайте 'ТАК' для підтвердження або 'НІ' для скасування.")
        await state.set_state(ClearAllState.waiting_for_confirmation)
    else:
        await msg.answer("❌ Невірний пароль. Операція скасована.")
        await state.clear()

@dp.message(ClearAllState.waiting_for_confirmation)
async def final_confirmation(msg: Message, state: FSMContext):
    if msg.text.strip().lower() == "так":
        await execute_query("DELETE FROM products")
        await execute_query("VACUUM")  # Очищення бази після видалення
        await msg.answer("🗑 Всі товари видалено, база оптимізована!")
    else:
        await msg.answer("✅ Видалення скасовано.")
    
    await state.clear()

# 📌 /search
@dp.message(Command("search"))
async def search_product(message: Message):
    try:
        query = message.text.split(" ", 1)[1].strip()

        results = await execute_query(
            "SELECT name, article, category FROM products WHERE name LIKE ? OR article LIKE ?",
            ('%' + query + '%', '%' + query + '%'), fetchall=True
        )

        if not results:
            await message.answer(f"⚠️ '{query}' не знайдено.")
            return

        response = "🔍 <b>Знайдено:</b>\n"
        for name, article, category in results:
            response += f"✅ {hbold(name)} (🆔 {hbold(article)}, 📂 {hbold(category)})\n"

        await message.answer(response)

    except IndexError:
        await message.answer("⚠️ Введіть назву або артикул: /search <запит>")


# 📌 /categories
@dp.message(Command("categories"))
async def list_categories(message: Message):
    categories = await execute_query("SELECT DISTINCT category FROM products", fetchall=True)

    if not categories:
        await message.answer("📭 Категорії ще не додані!")
        return

    response = "📂 <b>Список категорій:</b>\n" + "\n".join(f"✅ {hbold(cat[0])}" for cat in categories)
    await message.answer(response)


# 📌 /delete (оновлена команда з оптимізацією бази даних)
@dp.message(Command("delete"))
async def delete_product(message: Message):
    if not is_authorized(message.from_user.id):
        await message.answer("❌ У вас немає прав!")
        return

    try:
        name = message.text.split(" ", 1)[1].strip()
        result = await execute_query("SELECT id FROM products WHERE name = ?", (name,), fetchone=True)
        
        if not result:
            await message.answer(f"⚠️ Товар '{hbold(name)}' не знайдено!")
            return

        await execute_query("DELETE FROM products WHERE name = ?", (name,))
        await execute_query("VACUUM")  # Оптимізація після видалення
        await message.answer(f"🗑 Товар '{hbold(name)}' видалено, база оптимізована!")
    
    except IndexError:
        await message.answer("⚠️ Формат: /delete Назва")


# Команда /edit - редагування товару
@dp.message(Command("edit"))
async def edit_product(message: Message):
    try:
        text = message.text.split(" ", 1)[1].strip()
        name, new_article, new_category = text.split(" - ")

        existing = await execute_query("SELECT * FROM products WHERE name = ?", (name,), fetchone=True)
        if not existing:
            await message.answer(f"⚠️ Товар '{name}' не знайдено!")
            return

        await execute_query(
            "UPDATE products SET article = ?, category = ? WHERE name = ?",
            (new_article.strip(), new_category.strip(), name.strip())
        )

        await message.answer(
            f"✏️ Товар '{hbold(name)}' оновлено!\n"
            f"Новий артикул: 🆔 {hbold(new_article.strip())}\n"
            f"Нова категорія: 📂 {hbold(new_category.strip())}"
        )
    
    except ValueError:
        await message.answer("⚠️ Формат: /edit Назва - Новий артикул - Нова категорія")


async def send_daily_report():
    try:
        result = await execute_query("SELECT COUNT(*) FROM products", fetchone=True)
        count = result[0] if result else 0
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_message = f"📊 <b>Щоденний звіт</b>\n🕒 Час: {now}\n📦 Кількість товарів: {count}"
        
        await bot.send_message(ADMIN_ID, report_message)
        logging.info("✅ Щоденний звіт успішно відправлено.")
    
    except Exception as e:
        logging.error(f"❌ Помилка при надсиланні щоденного звіту: {e}")


async def schedule_daily_report():
    while True:
        try:
            now = datetime.datetime.now()
            target_time = now.replace(hour=23, minute=0, second=0, microsecond=0)

            if now > target_time:
                target_time += datetime.timedelta(days=1)

            wait_time = (target_time - now).total_seconds()
            logging.info(f"📅 Наступний звіт буде через {wait_time / 3600:.2f} годин.")

            await asyncio.sleep(wait_time)
            await send_daily_report()

        except Exception as e:
            logging.error(f"❌ Помилка у щоденному звіті: {e}")
            await asyncio.sleep(60)  # Якщо сталася помилка, чекаємо хвилину перед повтором



# 📌 Запуск бота
async def main():
    print("✅ Бот запущено!")
    await init_db()
    products = await execute_query("SELECT COUNT(*) FROM products", fetchone=True)
    print(f"📦 Товарів у базі: {products[0] if products else 0}")
    asyncio.create_task(schedule_daily_report())  # Запускаємо щоденний звіт
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())  # Коректний виклик основної функції

