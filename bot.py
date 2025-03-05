import datetime
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

# Инициализация бота и диспетчера с хранилищем состояний
TOKEN = os.getenv("TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "data.json")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния для FSM (машины состояний)
class ShiftState(StatesGroup):
    choosing_operator = State()
    pc_income = State()
    simracing_income = State()
    playstation_income = State()
    cash_left = State()
    confirm_operator = State()
    choosing_barmen = State()
    bar_income = State()
    confirm_barmen = State()

# Функции для работы с JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# Определение смены
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

# Операторы и бармены
operators = ["Ардина", "Назгул", "Жазира"]
barmen = ["Дастан", "Магжан", "Мейржан"]

# Клавиатуры
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

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    today, shift = get_current_shift()
    await ShiftState.choosing_operator.set()
    await message.answer(f"Здравствуйте! Сейчас идет смена ({today} - {shift}).\nВыберите ваше имя:", reply_markup=operator_keyboard)

# Оператор выбирает свое имя
@dp.message_handler(lambda message: message.text in operators, state=ShiftState.choosing_operator)
async def operator_selected(message: types.Message, state: FSMContext):
    await state.update_data(operator=message.text)
    await ShiftState.pc_income.set()
    await message.answer(f"Оператор {message.text}, введите поступления по ПК:", reply_markup=ReplyKeyboardRemove())

# Ввод поступлений по ПК
@dp.message_handler(state=ShiftState.pc_income)
async def pc_income(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только число!")
        return
    await state.update_data(pc_income=int(message.text))
    await ShiftState.simracing_income.set()
    await message.answer("Введите поступления по SimRacing:")

# Ввод поступлений по SimRacing
@dp.message_handler(state=ShiftState.simracing_income)
async def simracing_income(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только число!")
        return
    await state.update_data(simracing_income=int(message.text))
    await ShiftState.playstation_income.set()
    await message.answer("Введите поступления по PlayStation:")

# Ввод поступлений по PlayStation
@dp.message_handler(state=ShiftState.playstation_income)
async def playstation_income(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только число!")
        return
    await state.update_data(playstation_income=int(message.text))
    await ShiftState.cash_left.set()
    await message.answer("Введите остаток денег в кассе (до 3000 тенге):")

# Ввод остатка в кассе
@dp.message_handler(state=ShiftState.cash_left)
async def cash_left(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только число!")
        return
    await state.update_data(cash_left=int(message.text))

    data = await state.get_data()
    summary = f"📋 *Сводка по оператору {data['operator']}*:\n"
    summary += f"💻 ПК: {data['pc_income']} тенге\n"
    summary += f"🏎 SimRacing: {data['simracing_income']} тенге\n"
    summary += f"🎮 PlayStation: {data['playstation_income']} тенге\n"
    summary += f"💰 Остаток в кассе: {data['cash_left']} тенге\n\n"
    summary += "Подтвердите данные:"

    await ShiftState.confirm_operator.set()
    await message.answer(summary, reply_markup=confirm_keyboard, parse_mode="Markdown")

# Подтверждение оператором
@dp.message_handler(state=ShiftState.confirm_operator)
async def confirm_operator(message: types.Message, state: FSMContext):
    if message.text == "✅ Подтверждаю":
        await ShiftState.choosing_barmen.set()
        await message.answer("Теперь очередь бармена! Выберите свое имя:", reply_markup=barmen_keyboard)
    else:
        await ShiftState.pc_income.set()
        await message.answer("Введите данные заново!")

# Бармен выбирает имя
@dp.message_handler(lambda message: message.text in barmen, state=ShiftState.choosing_barmen)
async def barmen_selected(message: types.Message, state: FSMContext):
    await state.update_data(barmen=message.text)
    await ShiftState.bar_income.set()
    await message.answer(f"Бармен {message.text}, введите поступления по бару:", reply_markup=ReplyKeyboardRemove())

# Ввод поступлений по бару
@dp.message_handler(state=ShiftState.bar_income)
async def bar_income(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Введите только число!")
        return
    await state.update_data(bar_income=int(message.text))

    await ShiftState.confirm_barmen.set()
    await message.answer(f"Подтвердите остатки:", reply_markup=confirm_keyboard)

# Подтверждение бармена
@dp.message_handler(state=ShiftState.confirm_barmen)
async def confirm_barmen(message: types.Message, state: FSMContext):
    if message.text == "✅ Подтверждаю":
        today, shift = get_current_shift()
        next_day, next_shift = update_shift()
        await message.answer(f"✅ *Смена ({today} - {shift}) закрыта!*\n🔄 *Открылась смена ({next_day} - {next_shift}).*", parse_mode="Markdown")
    else:
        await message.answer("Данные введены неверно! Введите заново.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
