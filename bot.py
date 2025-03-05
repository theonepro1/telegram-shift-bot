import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import json
import os

TOKEN = os.getenv("TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "data.json")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Загрузка данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# Определение текущей смены
def get_current_shift():
    now = datetime.datetime.now()
    shift_type = "ДЕНЬ" if now.hour < 20 else "НОЧЬ"
    return now.strftime("%d.%m.%y"), shift_type

# Обновление смены после подтверждения
def update_shift():
    today, shift = get_current_shift()
    if shift == "ДЕНЬ":
        next_shift = "НОЧЬ"
    else:
        next_shift = "ДЕНЬ"
        today = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%d.%m.%y")
    return today, next_shift

# Операторы и бармены (для выбора)
operators = ["Ардина", "Назгул", "Жазира"]
barmen = ["Дастан", "Магжан", "Мейржан"]

# Клавиатуры
confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("✅ Подтверждаю"),
    KeyboardButton("❌ Отмена")
)

operator_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for op in operators:
    operator_keyboard.add(KeyboardButton(op))

barmen_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for br in barmen:
    barmen_keyboard.add(KeyboardButton(br))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    today, shift = get_current_shift()
    await message.answer(f"Здравствуйте! Сейчас идет смена ({today} - {shift}).\nВыберите ваше имя:", reply_markup=operator_keyboard)

@dp.message_handler(lambda message: message.text in operators)
async def operator_selected(message: types.Message):
    global data
    if not isinstance(data, dict):
        data = {}  
    data["operator"] = message.text
    save_data(data)
    await message.answer("Введите поступления по ПК:", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_pc_income(message: types.Message):
    global data
    data["pc_income"] = int(message.text)
    save_data(data)
    await message.answer("Введите поступления по SimRacing:")

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_simracing_income(message: types.Message):
    global data
    data["simracing_income"] = int(message.text)
    save_data(data)
    await message.answer("Введите поступления по PlayStation:")

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_playstation_income(message: types.Message):
    global data
    data["playstation_income"] = int(message.text)
    save_data(data)
    await message.answer("Введите остаток в кассе (копейки до 3000 тенге):")

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_cash_left(message: types.Message):
    global data
    data["cash_left"] = int(message.text)
    save_data(data)
    await message.answer("Подтвердите введенные данные:", reply_markup=confirm_keyboard)

@dp.message_handler(lambda message: message.text == "✅ Подтверждаю")
async def confirm_shift(message: types.Message):
    today, shift = get_current_shift()
    next_day, next_shift = update_shift()
    await message.answer(f"✅ Смена ({today} - {shift}) ЗАКРЫЛАСЬ.\nОткрылась смена ({next_day} - {next_shift}).")
    await message.answer("Бармен, подтвердите остатки напитков:", reply_markup=barmen_keyboard)

@dp.message_handler(lambda message: message.text in barmen)
async def barmen_selected(message: types.Message):
    global data
    data["barmen"] = message.text
    save_data(data)
    await message.answer("Введите поступления по бару:")

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_bar_income(message: types.Message):
    global data
    data["bar_income"] = int(message.text)
    save_data(data)
    await message.answer("Введите остатки напитков:")

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_drinks_left(message: types.Message):
    global data
    data["drinks_left"] = int(message.text)
    save_data(data)
    await message.answer("Введите остатки еды:")

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_food_left(message: types.Message):
    global data
    data["food_left"] = int(message.text)
    save_data(data)
    await message.answer("Введите остаток в кассе бара (копейки до 3000 тенге):")

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def input_bar_cash_left(message: types.Message):
    global data
    data["bar_cash_left"] = int(message.text)
    save_data(data)
    await message.answer("Подтвердите введенные данные:", reply_markup=confirm_keyboard)

@dp.message_handler(lambda message: message.text == "✅ Подтверждаю")
async def confirm_bar_shift(message: types.Message):
    today, shift = get_current_shift()
    next_day, next_shift = update_shift()
    await message.answer(f"✅ ВСЁ, СМЕНА ({today} - {shift}) ЗАКРЫЛАСЬ.\nОТКРЫЛАСЬ СМЕНА ({next_day} - {next_shift}).")

@dp.message_handler(lambda message: message.text == "❌ Отмена")
async def cancel_shift(message: types.Message):
    await message.answer("Отмена подтверждения смены.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
