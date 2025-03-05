import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import os

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class ShiftState(StatesGroup):
    operator_name = State()
    pc_income = State()
    simracing_income = State()
    playstation_income = State()
    cash_left = State()
    bar_name = State()
    bar_income = State()
    drinks_left = State()
    food_left = State()
    bar_cash_left = State()
    confirm = State()

operators = ["Ардина", "Назгул", "Жазира"]
barmen = ["Дастан", "Магжан", "Мейржан"]

operator_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for op in operators:
    operator_keyboard.add(KeyboardButton(op))

barmen_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
for br in barmen:
    barmen_keyboard.add(KeyboardButton(br))

confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("✅ Подтверждаю"),
    KeyboardButton("❌ Отмена")
)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Здравствуйте! Выберите ваше имя:", reply_markup=operator_keyboard)
    await ShiftState.operator_name.set()

@dp.message_handler(lambda message: message.text in operators, state=ShiftState.operator_name)
async def operator_selected(message: types.Message, state: FSMContext):
    await state.update_data(operator=message.text)
    await message.answer("Введите поступления по ПК:")
    await ShiftState.pc_income.set()

@dp.message_handler(state=ShiftState.pc_income)
async def get_pc_income(message: types.Message, state: FSMContext):
    await state.update_data(pc_income=message.text)
    await message.answer("Введите поступления по SimRacing:")
    await ShiftState.simracing_income.set()

@dp.message_handler(state=ShiftState.simracing_income)
async def get_simracing_income(message: types.Message, state: FSMContext):
    await state.update_data(simracing_income=message.text)
    await message.answer("Введите поступления по PlayStation:")
    await ShiftState.playstation_income.set()

@dp.message_handler(state=ShiftState.playstation_income)
async def get_playstation_income(message: types.Message, state: FSMContext):
    await state.update_data(playstation_income=message.text)
    await message.answer("Введите остаток в кассе (копейки до 3000 тенге):")
    await ShiftState.cash_left.set()

@dp.message_handler(state=ShiftState.cash_left)
async def get_cash_left(message: types.Message, state: FSMContext):
    await state.update_data(cash_left=message.text)
    data = await state.get_data()
    summary = (f"Сводка по оператору {data['operator']}:\n"
               f"🖥 ПК: {data['pc_income']} тг\n"
               f"🏎 SimRacing: {data['simracing_income']} тг\n"
               f"🎮 PlayStation: {data['playstation_income']} тг\n"
               f"💰 Остаток в кассе: {data['cash_left']} тг")
    await message.answer(summary, reply_markup=confirm_keyboard)
    await ShiftState.confirm.set()

@dp.message_handler(lambda message: message.text == "✅ Подтверждаю", state=ShiftState.confirm)
async def confirm_operator_data(message: types.Message, state: FSMContext):
    await message.answer("Теперь очередь бармена! Выберите свое имя:", reply_markup=barmen_keyboard)
    await ShiftState.bar_name.set()

@dp.message_handler(lambda message: message.text in barmen, state=ShiftState.bar_name)
async def bar_selected(message: types.Message, state: FSMContext):
    await state.update_data(bar_name=message.text)
    await message.answer("Введите поступления по бару:")
    await ShiftState.bar_income.set()

@dp.message_handler(state=ShiftState.bar_income)
async def get_bar_income(message: types.Message, state: FSMContext):
    await state.update_data(bar_income=message.text)
    await message.answer("Введите остаток напитков (шт.):")
    await ShiftState.drinks_left.set()

@dp.message_handler(state=ShiftState.drinks_left)
async def get_drinks_left(message: types.Message, state: FSMContext):
    await state.update_data(drinks_left=message.text)
    await message.answer("Введите остаток еды (шт.):")
    await ShiftState.food_left.set()

@dp.message_handler(state=ShiftState.food_left)
async def get_food_left(message: types.Message, state: FSMContext):
    await state.update_data(food_left=message.text)
    await message.answer("Введите остаток мелочи в кассе (копейки до 3000 тг):")
    await ShiftState.bar_cash_left.set()

@dp.message_handler(state=ShiftState.bar_cash_left)
async def get_bar_cash_left(message: types.Message, state: FSMContext):
    await state.update_data(bar_cash_left=message.text)
    data = await state.get_data()
    summary = (f"Сводка по бармену {data['bar_name']}:\n"
               f"🍹 Бар: {data['bar_income']} тг\n"
               f"🥤 Напитки: {data['drinks_left']} шт\n"
               f"🍔 Еда: {data['food_left']} шт\n"
               f"💰 Остаток в кассе: {data['bar_cash_left']} тг")
    await message.answer(summary, reply_markup=confirm_keyboard)
    await ShiftState.confirm.set()

@dp.message_handler(lambda message: message.text == "✅ Подтверждаю", state=ShiftState.confirm)
async def confirm_bar_data(message: types.Message, state: FSMContext):
    today = datetime.datetime.now().strftime("%d.%m.%y")
    await message.answer(f"✅ Смена {today} ЗАКРЫТА! Открывается новая смена.")
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
