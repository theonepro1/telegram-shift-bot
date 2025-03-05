import logging
import asyncio
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
import json
import os

# Загружаем токен бота из переменных окружения
TOKEN = os.getenv("TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "database.json")

# Настраиваем бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Определение состояний для сбора данных
class ShiftData(StatesGroup):
    pc_income = State()
    simracing_income = State()
    playstation_income = State()
    cash_left = State()
    bar_income = State()
    drinks_left = State()
    food_left = State()
    bar_cash_left = State()
    confirm = State()

# Функция сохранения данных в JSON
def save_data(data):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    existing_data.append(data)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)

# Команда /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет! Этот бот поможет передавать смену. Нажмите 'Сдать смену' для начала.",
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("Сдать смену")))

# Запуск процесса сдачи смены
@dp.message_handler(lambda message: message.text == "Сдать смену")
async def start_shift(message: types.Message):
    await message.answer("Введите поступления от компьютеров (тенге):")
    await ShiftData.pc_income.set()

@dp.message_handler(state=ShiftData.pc_income)
async def get_pc_income(message: types.Message, state: FSMContext):
    await state.update_data(pc_income=message.text)
    await message.answer("Введите поступления от SimRacing:")
    await ShiftData.simracing_income.set()

@dp.message_handler(state=ShiftData.simracing_income)
async def get_simracing_income(message: types.Message, state: FSMContext):
    await state.update_data(simracing_income=message.text)
    await message.answer("Введите поступления от PlayStation:")
    await ShiftData.playstation_income.set()

@dp.message_handler(state=ShiftData.playstation_income)
async def get_playstation_income(message: types.Message, state: FSMContext):
    await state.update_data(playstation_income=message.text)
    await message.answer("Сколько денег осталось в кассе (тенге)?")
    await ShiftData.cash_left.set()

@dp.message_handler(state=ShiftData.cash_left)
async def get_cash_left(message: types.Message, state: FSMContext):
    await state.update_data(cash_left=message.text)
    await message.answer("Введите поступления от бара:")
    await ShiftData.bar_income.set()

@dp.message_handler(state=ShiftData.bar_income)
async def get_bar_income(message: types.Message, state: FSMContext):
    await state.update_data(bar_income=message.text)
    await message.answer("Сколько осталось напитков (шт.)?")
    await ShiftData.drinks_left.set()

@dp.message_handler(state=ShiftData.drinks_left)
async def get_drinks_left(message: types.Message, state: FSMContext):
    await state.update_data(drinks_left=message.text)
    await message.answer("Сколько осталось еды (шт.)?")
    await ShiftData.food_left.set()

@dp.message_handler(state=ShiftData.food_left)
async def get_food_left(message: types.Message, state: FSMContext):
    await state.update_data(food_left=message.text)
    await message.answer("Сколько денег осталось в кассе бара (тенге)?")
    await ShiftData.bar_cash_left.set()

@dp.message_handler(state=ShiftData.bar_cash_left)
async def get_bar_cash_left(message: types.Message, state: FSMContext):
    await state.update_data(bar_cash_left=message.text)
    
    data = await state.get_data()
    
    summary = (
        f"✅ Данные о смене:\n"
        f"💻 Компьютеры: {data['pc_income']} тенге\n"
        f"🏎 SimRacing: {data['simracing_income']} тенге\n"
        f"🎮 PlayStation: {data['playstation_income']} тенге\n"
        f"💰 Остаток в кассе: {data['cash_left']} тенге\n"
        f"🍹 Бар: {data['bar_income']} тенге\n"
        f"🥤 Напитки: {data['drinks_left']} шт.\n"
        f"🍔 Еда: {data['food_left']} шт.\n"
        f"💰 Остаток в кассе бара: {data['bar_cash_left']} тенге\n"
        f"\nПодтвердите сдачу смены? (Да/Нет)"
    )
    
    await message.answer(summary)
    await ShiftData.confirm.set()

@dp.message_handler(state=ShiftData.confirm)
async def confirm_shift(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        data = await state.get_data()
        save_data(data)
        await message.answer("✅ Смена успешно сдана! Данные сохранены.")
        await state.finish()
    else:
        await message.answer("❌ Смена отменена.")
        await state.finish()

# Запуск бота
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
