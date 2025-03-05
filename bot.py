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
barmen = ["Дастан", "Магжан", "Мейржан",]

# Клавиатуры
confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("✅ Подтверждаю"),
    KeyboardButton("❌ Отмена")
)

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
    await message.answer(f"Оператор {message.text}, подтвердите сдачу смены.", reply_markup=confirm_keyboard)

@dp.message_handler(lambda message: message.text == "✅ Подтверждаю")
async def confirm_shift(message: types.Message):
    today, shift = get_current_shift()
    next_day, next_shift = update_shift()
    await message.answer(f"Кутты болсын :-0, смена ({today} - {shift}) ЗАКРЫЛАСЬ.\nОткрылась смена ({next_day} - {next_shift}).")
    await message.answer("Бармен, подтвердите остатки напитков:", reply_markup=barmen_keyboard)

@dp.message_handler(lambda message: message.text in barmen)
async def barmen_selected(message: types.Message):
    await message.answer(f"Бармен {message.text}, подтвердите остатки напитков.")

@dp.message_handler(lambda message: message.text == "❌ Отмена")
async def cancel_shift(message: types.Message):
    await message.answer("Отмена подтверждения смены.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
