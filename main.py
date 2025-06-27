import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from config import Config
from database import Database
from keyboards import get_main_keyboard, get_week_choice_keyboard, get_day_choice_keyboard
from utils import parse_schedule_text, validate_schedule, get_week_start_date, get_next_week_start_date, get_day_of_week, format_schedule_for_tomorrow
from excel_generator import generate_week_schedule_excel, generate_day_schedule_excel
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()
db = Database()

class Registration(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()

class ScheduleInput(StatesGroup):
    waiting_for_schedule = State()

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    
    if db.is_user_registered(user.id):
        await message.answer(
            f"Добро пожаловать, {db.get_user_name(user.id)}!\n"
            "Используйте кнопки ниже для работы с расписанием.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Добро пожаловать! Для начала работы вам нужно зарегистрироваться.\n"
            "Введите ваше имя:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Registration.waiting_for_first_name)

@dp.message(Registration.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Теперь введите вашу фамилию:")
    await state.set_state(Registration.waiting_for_last_name)

@dp.message(Registration.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    first_name = user_data['first_name']
    last_name = message.text
    
    if db.register_user(message.from_user.id, first_name, last_name):
        await message.answer(
            f"Спасибо за регистрацию, {last_name} {first_name}!\n"
            "Теперь вы можете управлять своим расписанием.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "Произошла ошибка при регистрации. Попробуйте еще раз.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

@dp.message(F.text == "Заполнить расписание")
async def fill_schedule(message: Message, state: FSMContext):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "📅 Введите ваше расписание на следующую неделю в формате:\n\n"
        "понедельник: 9-18\n"
        "вторник: 10-19\n"
        "среда: выходной\n"
        "четверг: 11-21\n"
        "пятница: 9-18\n"
        "суббота: выходной\n"
        "воскресенье: выходной\n\n"
        "Можно вводить как одной строкой, так и по дням:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(ScheduleInput.waiting_for_schedule)

@dp.message(ScheduleInput.waiting_for_schedule)
async def process_schedule_input(message: Message, state: FSMContext):
    try:
        schedule_data = parse_schedule_text(message.text)
        if not validate_schedule(schedule_data):
            await message.answer(
                "❌ Некорректный формат. Используйте:\n"
                "день: время (например: понедельник: 9-18)\n"
                "или 'выходной'\n\n"
                "Попробуйте еще раз:",
                reply_markup=ReplyKeyboardRemove()
            )
            return
        
        next_week_start = get_next_week_start_date()
        if db.save_schedule(message.from_user.id, next_week_start, schedule_data):
            await message.answer(
                "✅ Расписание на следующую неделю успешно сохранено!",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Ошибка при сохранении. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке расписания: {e}")
        await message.answer(
            "❌ Произошла ошибка. Проверьте формат и попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
    finally:
        await state.clear()

@dp.message(F.text == "Мое расписание")
async def my_schedule(message: Message):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "Выберите неделю для просмотра:",
        reply_markup=get_week_choice_keyboard()
    )

@dp.message(F.text == "Расписание на завтра")
async def tomorrow_schedule(message: Message):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    tomorrow = datetime.now() + timedelta(days=1)
    day_name = get_day_of_week(tomorrow.date())
    week_start = get_week_start_date(tomorrow.date())
    
    schedule_entries = db.get_week_schedule(week_start)
    formatted_schedule = format_schedule_for_tomorrow(schedule_entries, day_name)
    
    await message.answer(formatted_schedule)

@dp.message(F.text == "Общее расписание")
async def full_schedule(message: Message):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "Выберите неделю для просмотра:",
        reply_markup=get_week_choice_keyboard()
    )

@dp.callback_query(F.data.startswith('day_'))
async def process_day_choice(callback: CallbackQuery):
    if not db.is_user_registered(callback.from_user.id):
        await callback.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    day = callback.data.split('_')[1]
    today = datetime.now().date()
    week_start = get_week_start_date(today)
    
    schedule_entries = db.get_week_schedule(week_start)
    
    try:
        filename = generate_day_schedule_excel(schedule_entries, day)
        
        await callback.message.answer_document(
            FSInputFile(filename, filename=f"schedule_{day}.xlsx"),
            caption=f"Расписание на {day}"
        )
        
        # Текстовая версия
        text_schedule = f"Расписание на {day}:\n\n"
        for entry in schedule_entries:
            name = f"{entry['last_name']} {entry['first_name']}"
            text_schedule += f"{name}: {entry.get('schedule', 'выходной')}\n"
        
        await callback.message.answer(text_schedule)
        os.remove(filename)
    except Exception as e:
        logger.error(f"Ошибка при отправке файла: {e}")
        await callback.message.answer(
            f"Не удалось отправить расписание на {day}. Попробуйте позже."
        )
    
    await callback.answer()

@dp.callback_query(F.data.in_(['current_week', 'next_week']))
async def process_week_choice(callback: CallbackQuery):
    if not db.is_user_registered(callback.from_user.id):
        await callback.answer("Сначала зарегистрируйтесь с помощью /start")
        return
    
    if callback.data == 'current_week':
        week_start = get_week_start_date()
        week_name = "текущую неделю"
    else:
        week_start = get_next_week_start_date()
        week_name = "следующую неделю"
    
    schedule_data = db.get_week_schedule(week_start)
    if not schedule_data:
        await callback.message.answer(f"На {week_name} расписание еще не заполнено.")
        await callback.answer()
        return
    
    try:
        filename = generate_week_schedule_excel(schedule_data, week_start)
        
        await callback.message.answer_document(
            FSInputFile(filename, filename=f"schedule_{week_start}.xlsx"),
            caption=f"Расписание на {week_name}"
        )
        
        # Текстовая версия
        text_schedule = "Фамилия Имя | Понедельник | Вторник | Среда | Четверг | Пятница | Суббота | Воскресенье\n"
        for entry in schedule_data:
            name = f"{entry['last_name']} {entry['first_name']}"
            text_schedule += f"{name} | {entry.get('monday', 'выходной')} | {entry.get('tuesday', 'выходной')} | {entry.get('wednesday', 'выходной')} | {entry.get('thursday', 'выходной')} | {entry.get('friday', 'выходной')} | {entry.get('saturday', 'выход')} | {entry.get('sunday', 'выход')}\n"
        
        await callback.message.answer(text_schedule)
        os.remove(filename)
    except Exception as e:
        logger.error(f"Ошибка при отправке файла: {e}")
        await callback.message.answer(
            f"Не удалось отправить расписание на {week_name}. Попробуйте позже."
        )
    
    await callback.answer()

async def scheduler():
    """Планировщик задач"""
    while True:
        now = datetime.now()
        
        # Каждую среду в 10:00 отправляем напоминание
        if now.weekday() == 2 and now.hour == 10 and now.minute == 0:
            await send_schedule_reminder()
        
        # Ежедневно в 18:00 отправляем расписание на завтра
        if now.hour == 18 and now.minute == 0:
            await send_daily_schedule()
        
        await asyncio.sleep(60)

async def send_schedule_reminder():
    """Отправка напоминания о заполнении расписания"""
    users = db.get_all_users()
    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                "⏰ Напоминание: пожалуйста, заполните расписание на следующую неделю!\n"
                "Нажмите кнопку 'Заполнить расписание' в главном меню.",
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания пользователю {user['user_id']}: {e}")

async def send_daily_schedule():
    """Отправка расписания на завтра"""
    tomorrow = datetime.now() + timedelta(days=1)
    day_name = get_day_of_week(tomorrow.date())
    week_start = get_week_start_date(tomorrow.date())
    
    schedule_entries = db.get_week_schedule(week_start)
    formatted_schedule = format_schedule_for_tomorrow(schedule_entries, day_name)
    
    users = db.get_all_users()
    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                formatted_schedule
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке расписания пользователю {user['user_id']}: {e}")

async def on_startup():
    asyncio.create_task(scheduler())

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
