import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command

# Ініціалізація бота
TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Підключення до бази даних
def init_db():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT UNIQUE,
                      article TEXT UNIQUE)''')
    conn.commit()
    conn.close()

# Додавання товару
def add_product(name, article):
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, article) VALUES (?, ?)", (name, article))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Пошук товару
def search_product(name):
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, article FROM products WHERE name LIKE ?", (f"%{name}%",))
    result = cursor.fetchall()
    conn.close()
    return result

# Отримати всі товари
def get_all_products():
    conn = sqlite3.connect("products.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, article FROM products")
    result = cursor.fetchall()
    conn.close()
    return result

# Команда /start
@dp.message_handler(Command("start"))
async def start_command(message: Message):
    await message.answer("Привіт! Я бот для керування товарами. Використовуй /list, /search, /add.")

# Команда /list
@dp.message_handler(Command("list"))
async def list_command(message: Message):
    products = get_all_products()
    if products:
        response = "📋 Усі товари:\n" + "\n".join([f"✅ {name} - {article}" for name, article in products])
    else:
        response = "❌ Немає товарів у базі."
    await message.answer(response)

# Команда /search
@dp.message_handler(Command("search"))
async def search_command(message: Message):
    await message.answer("🔎 Введи назву товару для пошуку:")
    @dp.message_handler()
    async def process_search(msg: Message):
        products = search_product(msg.text.lower())
        if products:
            response = "🔍 Знайдені товари:\n" + "\n".join([f"✅ {name} - {article}" for name, article in products])
        else:
            response = "❌ Товар не знайдено."
        await msg.answer(response)

# Команда /add
@dp.message_handler(Command("add"))
async def add_command(message: Message):
    await message.answer("➕ Введи назву товару та артикул у форматі: назва - артикул")
    @dp.message_handler()
    async def process_add(msg: Message):
        try:
            name, article = map(str.strip, msg.text.split("-"))
            if add_product(name.lower(), article):
                await msg.answer(f"✅ Товар {name} додано!\n🆔 Артикул: {article}")
            else:
                await msg.answer("❌ Помилка! Товар або артикул вже існує.")
        except ValueError:
            await msg.answer("⚠️ Некоректний формат. Використовуй: назва - артикул")

# Запуск бота
if __name__ == "__main__":
    init_db()
    executor.start_polling(dp, skip_updates=True)

