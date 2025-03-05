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
            data = json.load(f)
            if isinstance(data, dict): 
                return data
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

operator_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for op in operators:
    operator_keyboard.add(KeyboardButton(op))

barmen_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for br in barmen:
    barmen_keyboard.add(KeyboardButton(br))

numeric_keyboard = types.ReplyKeyboardRemove()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    today, shift = get_current_shift()
    await message.answer(f"Здравствуйте! Сейчас идет смена ({today} - {shift}).\nВыберите ваше имя:", reply_markup=operator_keyboard)

@dp.message_handler(lambda message: message.text in operators)
async def operator_selected(message: types.Message):
    if isinstance(data, dict):
    data["operator"] = message.text
else:
    data = {"operator": message.text}
    save_data(data)
    await message.answer(f"🖥️ Введите поступления по ПК:", reply_markup=numeric_keyboard)

@dp.message_handler(lambda message: message.text.isdigit(), state=None)
async def pc_income(message: types.Message):
    data["pc_income"] = int(message.text)
    save_data(data)
    await message.answer(f"🎮 Введите поступления по SimRacing:")

@dp.message_handler(lambda message: message.text.isdigit())
async def simracing_income(message: types.Message):
    data["simracing_income"] = int(message.text)
    save_data(data)
    await message.answer(f"🕹️ Введите поступления по PlayStation:")

@dp.message_handler(lambda message: message.text.isdigit())
async def playstation_income(message: types.Message):
    data["playstation_income"] = int(message.text)
    save_data(data)
    await message.answer(f"💰 Введите остаток денег в кассе (до 3000 тенге):")

@dp.message_handler(lambda message: message.text.isdigit())
async def cash_left(message: types.Message):
    data["cash_left"] = int(message.text)
    save_data(data)
    await message.answer(f"✅ Подтвердите данные:\n"
                         f"🖥️ ПК: {data['pc_income']} тенге\n"
                         f"🎮 SimRacing: {data['simracing_income']} тенге\n"
                         f"🕹️ PlayStation: {data['playstation_income']} тенге\n"
                         f"💰 Остаток в кассе: {data['cash_left']} тенге", reply_markup=confirm_keyboard)

@dp.message_handler(lambda message: message.text == "✅ Подтверждаю")
async def confirm_operator(message: types.Message):
    await message.answer(f"📢 Теперь очередь бармена! Выберите ваше имя:", reply_markup=barmen_keyboard)

@dp.message_handler(lambda message: message.text in barmen)
async def barmen_selected(message: types.Message):
    data["barmen"] = message.text
    save_data(data)
    await message.answer(f"🍹 Введите поступления по бару:", reply_markup=numeric_keyboard)

@dp.message_handler(lambda message: message.text.isdigit())
async def bar_income(message: types.Message):
    data["bar_income"] = int(message.text)
    save_data(data)
    await message.answer(f"🥤 Введите остаток напитков (шт.):")

@dp.message_handler(lambda message: message.text.isdigit())
async def drinks_left(message: types.Message):
    data["drinks_left"] = int(message.text)
    save_data(data)
    await message.answer(f"🍔 Введите остаток еды (шт.):")

@dp.message_handler(lambda message: message.text.isdigit())
async def food_left(message: types.Message):
    data["food_left"] = int(message.text)
    save_data(data)
    await message.answer(f"💰 Введите остаток денег в кассе (до 3000 тенге):")

@dp.message_handler(lambda message: message.text.isdigit())
async def bar_cash_left(message: types.Message):
    data["bar_cash_left"] = int(message.text)
    save_data(data)
    await message.answer(f"✅ Подтвердите данные:\n"
                         f"🍹 Бар: {data['bar_income']} тенге\n"
                         f"🥤 Напитки: {data['drinks_left']} шт.\n"
                         f"🍔 Еда: {data['food_left']} шт.\n"
                         f"💰 Остаток в кассе: {data['bar_cash_left']} тенге", reply_markup=confirm_keyboard)

@dp.message_handler(lambda message: message.text == "✅ Подтверждаю")
async def confirm_barmen(message: types.Message):
    today, shift = get_current_shift()
    next_day, next_shift = update_shift()
    await message.answer(f"🎉 Кутты болсын! Смена ({today} - {shift}) ЗАКРЫЛАСЬ.\n"
                         f"📢 Открылась смена ({next_day} - {next_shift}).")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
