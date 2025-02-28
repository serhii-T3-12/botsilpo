import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor

TOKEN = "7861897815:AAFByfkNqSIWIauet7k0lyS80SgiuqWPDhw"  # Твій токен бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# База товарів (назва → артикул)
PRODUCTS = {
    "салат айзберг": "540258",
    "помідори чері": "123456",
    "огірок свіжий": "789012",
    "банани": "345678"
}

# 📌 Обробник команди /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: Message):
    await message.reply("Привіт! Введи назву товару, і я знайду його артикул 🔍")

# 📌 Обробник команди /list (список товарів)
@dp.message_handler(commands=['list'])
async def send_product_list(message: Message):
    product_list = "\n".join([f"🔹 {name}" for name in PRODUCTS.keys()])
    await message.reply(f"Ось список доступних товарів:\n{product_list}")

# 📌 Обробник пошуку артикула
@dp.message_handler()
async def find_product(message: Message):
    query = message.text.lower().strip()
    for name, article in PRODUCTS.items():
        if query in name:  # Пошук за частковим збігом
            await message.reply(f"✅ {name.capitalize()} – Артикул: {article}")
            return
    await message.reply("❌ Товар не знайдено, спробуй іншу назву.")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

