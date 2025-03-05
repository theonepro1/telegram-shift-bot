import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import json
import os

TOKEN = os.getenv("TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "data.json")

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

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

# Состояния FSM
class ShiftReport(StatesGroup):
    waiting_for_pc_income = State()
    waiting_for_simracing_income = State()
    waiting_for_playstation_income = State()
    waiting_for_cash_left = State()
    waiting_for_bar_income = State()
    waiting_for_drinks_left = State()
    waiting_for_food_left = State()
    waiting_for_bar_cash_left = State()
    waiting_for_confirmation = State()

# Операторы и бармены
operators = ["Ардина", "Назгул", "Жазира"]
barmen = ["Дастан", "Магжан", "Мейржан"]

# Клавиатуры
operator_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for op in operators:
    operator_keyboard.add(KeyboardButton(op))

barmen_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
for br in barmen:
    barmen_keyboard.add(KeyboardButton(br))

numeric_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
numeric_keyboard.add(types.KeyboardButton("0"))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    today, shift = get_current_shift()
    await message.answer(f"Здравствуйте! Сейчас идет смена ({today} - {shift}).\nВыберите ваше имя:", reply_markup=operator_keyboard)

@dp.message_handler(lambda message: message.text in operators)
async def operator_selected(message: types.Message, state: FSMContext):
    await state.update_data(operator=message.text)
    await message.answer("Введите поступления по ПК:", reply_markup=ReplyKeyboardRemove())
    await ShiftReport.waiting_for_pc_income.set()

@dp.message_handler(state=ShiftReport.waiting_for_pc_income)
async def get_pc_income(message: types.Message, state: FSMContext):
    await state.update_data(pc_income=message.text)
    await message.answer("Введите поступления по SimRacing:", reply_markup=numeric_keyboard)
    await ShiftReport.waiting_for_simracing_income.set()

@dp.message_handler(state=ShiftReport.waiting_for_simracing_income)
async def get_simracing_income(message: types.Message, state: FSMContext):
    await state.update_data(simracing_income=message.text)
    await message.answer("Введите поступления по PlayStation:", reply_markup=numeric_keyboard)
    await ShiftReport.waiting_for_playstation_income.set()

@dp.message_handler(state=ShiftReport.waiting_for_playstation_income)
async def get_playstation_income(message: types.Message, state: FSMContext):
    await state.update_data(playstation_income=message.text)
    await message.answer("Введите остаток денег в кассе:", reply_markup=numeric_keyboard)
    await ShiftReport.waiting_for_cash_left.set()

@dp.message_handler(state=ShiftReport.waiting_for_cash_left)
async def get_cash_left(message: types.Message, state: FSMContext):
    await state.update_data(cash_left=message.text)
    await message.answer("Бармен, выберите свое имя:", reply_markup=barmen_keyboard)
    await ShiftReport.waiting_for_bar_income.set()

@dp.message_handler(lambda message: message.text in barmen, state=ShiftReport.waiting_for_bar_income)
async def barmen_selected(message: types.Message, state: FSMContext):
    await state.update_data(barmen=message.text)
    await message.answer("Введите поступления по бару:", reply_markup=numeric_keyboard)
    await ShiftReport.waiting_for_drinks_left.set()

@dp.message_handler(state=ShiftReport.waiting_for_drinks_left)
async def get_bar_income(message: types.Message, state: FSMContext):
    await state.update_data(bar_income=message.text)
    await message.answer("Введите остаток напитков:", reply_markup=numeric_keyboard)
    await ShiftReport.waiting_for_food_left.set()

@dp.message_handler(state=ShiftReport.waiting_for_food_left)
async def get_drinks_left(message: types.Message, state: FSMContext):
    await state.update_data(drinks_left=message.text)
    await message.answer("Введите остаток еды:", reply_markup=numeric_keyboard)
    await ShiftReport.waiting_for_bar_cash_left.set()

@dp.message_handler(state=ShiftReport.waiting_for_bar_cash_left)
async def get_food_left(message: types.Message, state: FSMContext):
    await state.update_data(food_left=message.text)
    await message.answer("Введите остаток денег в кассе бара:", reply_markup=numeric_keyboard)
    await ShiftReport.waiting_for_confirmation.set()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
