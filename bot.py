import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import json
import os

TOKEN = os.getenv("TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "data.json")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

def get_current_shift():
    now = datetime.datetime.now()
    shift_type = "ДЕНЬ" if now.hour < 20 else "НОЧЬ"
    return now.strftime("%d.%m.%y"), shift_type

def update_shift():
    today, shift = get_current_shift()
    if shift == "ДЕНЬ":
        next_shift = "НОЧЬ"
    else:
        next_shift = "ДЕНЬ"
        today = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%d.%m.%y")
    return today, next_shift

operators = ["Ардина", "Назгул", "Жазира"]
barmen = ["Дастан", "Магжан", "Мейржан"]

deposit_data = {}

operator_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for op in operators:
    operator_keyboard.add(KeyboardButton(op))

barmen_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for br in barmen:
    barmen_keyboard.add(KeyboardButton(br))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    today, shift = get_current_shift()
    await message.answer(f"Здравствуйте! Сейчас идет смена ({today} - {shift}).\nВыберите ваше имя:", reply_markup=operator_keyboard)

@dp.message_handler(lambda message: message.text in operators)
async def operator_selected(message: types.Message):
    deposit_data[message.chat.id] = {"operator": message.text, "step": "pc_income"}
    await message.answer("Введите поступления по ПК:")

@dp.message_handler(lambda message: message.chat.id in deposit_data and deposit_data[message.chat.id]["step"] == "pc_income")
async def input_pc_income(message: types.Message):
    deposit_data[message.chat.id]["pc_income"] = message.text
    deposit_data[message.chat.id]["step"] = "simracing_income"
    await message.answer("Введите поступления по SimRacing:")

@dp.message_handler(lambda message: message.chat.id in deposit_data and deposit_data[message.chat.id]["step"] == "simracing_income")
async def input_simracing_income(message: types.Message):
    deposit_data[message.chat.id]["simracing_income"] = message.text
    deposit_data[message.chat.id]["step"] = "playstation_income"
    await message.answer("Введите поступления по PlayStation:")

@dp.message_handler(lambda message: message.chat.id in deposit_data and deposit_data[message.chat.id]["step"] == "playstation_income")
async def input_playstation_income(message: types.Message):
    deposit_data[message.chat.id]["playstation_income"] = message.text
    deposit_data[message.chat.id]["step"] = "cash_left"
    await message.answer("Введите остаток в кассе:")

@dp.message_handler(lambda message: message.chat.id in deposit_data and deposit_data[message.chat.id]["step"] == "cash_left")
async def input_cash_left(message: types.Message):
    deposit_data[message.chat.id]["cash_left"] = message.text
    deposit_data[message.chat.id]["step"] = "confirm_operator"
    await message.answer("Подтвердите введенные данные:\n" +
                         f"ПК: {deposit_data[message.chat.id]['pc_income']}\n" +
                         f"SimRacing: {deposit_data[message.chat.id]['simracing_income']}\n" +
                         f"PlayStation: {deposit_data[message.chat.id]['playstation_income']}\n" +
                         f"Остаток в кассе: {deposit_data[message.chat.id]['cash_left']}\n\n" +
                         "Введите 'Да' для подтверждения или 'Нет' для исправления.")

@dp.message_handler(lambda message: message.text.lower() == "да" and message.chat.id in deposit_data and deposit_data[message.chat.id]["step"] == "confirm_operator")
async def confirm_operator(message: types.Message):
    await message.answer("Данные подтверждены. Бармен, введите поступления по бару:", reply_markup=barmen_keyboard)
    deposit_data[message.chat.id]["step"] = "bar_income"

@dp.message_handler(lambda message: message.text.lower() == "нет" and message.chat.id in deposit_data)
async def redo_operator_data(message: types.Message):
    deposit_data[message.chat.id]["step"] = "pc_income"
    await message.answer("Начнем ввод заново. Введите поступления по ПК:")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
