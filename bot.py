import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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
    data['operator'] = message.text
    await message.answer("Введите поступления по ПК:", reply_markup=ReplyKeyboardRemove())
    await dp.current_state(user=message.from_user.id).set_state("pc_income")

@dp.message_handler(lambda message: message.text.isdigit(), state="pc_income")
async def enter_pc_income(message: types.Message):
    data['pc_income'] = int(message.text)
    await message.answer("Введите поступления по SimRacing:")
    await dp.current_state(user=message.from_user.id).set_state("simracing_income")

@dp.message_handler(lambda message: message.text.isdigit(), state="simracing_income")
async def enter_simracing_income(message: types.Message):
    data['simracing_income'] = int(message.text)
    await message.answer("Введите поступления по PlayStation:")
    await dp.current_state(user=message.from_user.id).set_state("playstation_income")

@dp.message_handler(lambda message: message.text.isdigit(), state="playstation_income")
async def enter_playstation_income(message: types.Message):
    data['playstation_income'] = int(message.text)
    await message.answer("Введите остаток в кассе (до 3000 тенге):")
    await dp.current_state(user=message.from_user.id).set_state("cash_left")

@dp.message_handler(lambda message: not message.text.isdigit(), state="pc_income")
@dp.message_handler(lambda message: not message.text.isdigit(), state="simracing_income")
@dp.message_handler(lambda message: not message.text.isdigit(), state="playstation_income")
@dp.message_handler(lambda message: not message.text.isdigit(), state="cash_left")
async def invalid_input(message: types.Message):
    await message.answer("Пожалуйста, введите только цифры.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
