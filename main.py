import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
scheduler = AsyncIOScheduler()

class Registration(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()

class ScheduleInput(StatesGroup):
    waiting_for_schedule = State()

# ================== ОБРАБОТЧИКИ КОМАНД ==================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    
    if db.is_user_registered(user.id):
        await message.answer(
            f"👋 Добро пожаловать, {db.get_user_name(user.id)}!\n"
            "Используйте кнопки меню для работы с расписанием.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "👋 Добро пожаловать! Для начала работы вам нужно зарегистрироваться.\n"
            "Введите ваше имя:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Registration.waiting_for_first_name)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "ℹ️ <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать справку\n\n"
        "<b>Основные функции:</b>\n"
        "📝 <b>Заполнить расписание</b> - ввести свое расписание на неделю\n"
        "👀 <b>Мое расписание</b> - просмотреть свое расписание\n"
        "📅 <b>Расписание на завтра</b> - увидеть кто работает завтра\n"
        "👥 <b>Общее расписание</b> - скачать полное расписание\n\n"
        "Бот автоматически напомнит о заполнении расписания в среду утром."
    )
    await message.answer(help_text, reply_markup=get_main_keyboard(), parse_mode="HTML")

# ================== ОБРАБОТЧИКИ КНОПОК ==================

@dp.message(F.text.in_(["📝 Заполнить расписание", "Заполнить расписание", "заполнить"]))
async def cmd_fill_schedule(message: Message, state: FSMContext):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "📝 <b>Введите ваше расписание на следующую неделю:</b>\n\n"
        "<i>Формат:</i>\n"
        "понедельник: 9-18\n"
        "вторник: 10-19\n"
        "среда: выходной\n"
        "четверг: 11-21\n"
        "пятница: 9-18\n"
        "суббота: выходной\n"
        "воскресенье: выходной\n\n"
        "Можно вводить как одной строкой, так и по дням:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(ScheduleInput.waiting_for_schedule)

@dp.message(F.text.in_(["👀 Мое расписание", "Мое расписание", "мое расписание"]))
async def cmd_my_schedule(message: Message):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "Выберите неделю для просмотра:",
        reply_markup=get_week_choice_keyboard()
    )

@dp.message(F.text.in_(["📅 Расписание на завтра", "Расписание на завтра", "завтра"]))
async def cmd_tomorrow_schedule(message: Message):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    tomorrow = datetime.now() + timedelta(days=1)
    day_name = get_day_of_week(tomorrow.date())
    week_start = get_week_start_date(tomorrow.date())
    
    schedule_entries = db.get_week_schedule(week_start)
    formatted_schedule = format_schedule_for_tomorrow(schedule_entries, day_name)
    
    await message.answer(formatted_schedule)

@dp.message(F.text.in_(["👥 Общее расписание", "Общее расписание", "общее"]))
async def cmd_full_schedule(message: Message):
    if not db.is_user_registered(message.from_user.id):
        await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /start")
        return
    
    await message.answer(
        "Выберите неделю для просмотра:",
        reply_markup=get_week_choice_keyboard()
    )

# ================== ОБРАБОТЧИКИ СОСТОЯНИЙ ==================

@dp.message(Registration.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer("Имя слишком длинное. Максимум 50 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(first_name=message.text.strip())
    await message.answer("Теперь введите вашу фамилию:")
    await state.set_state(Registration.waiting_for_last_name)

@dp.message(Registration.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    if len(message.text) > 50:
        await message.answer("Фамилия слишком длинная. Максимум 50 символов. Попробуйте еще раз:")
        return
    
    user_data = await state.get_data()
    first_name = user_data['first_name']
    last_name = message.text.strip()
    
    if db.register_user(message.from_user.id, first_name, last_name):
        logger.info(f"New user registered: {last_name} {first_name} (ID: {message.from_user.id})")
        await message.answer(
            f"✅ Регистрация завершена, {last_name} {first_name}!\n"
            "Теперь вы можете управлять своим расписанием.",
            reply_markup=get_main_keyboard()
        )
    else:
        logger.error(f"Failed to register user: {message.from_user.id}")
        await message.answer(
            "❌ Ошибка при регистрации. Попробуйте еще раз.",
            reply_markup=ReplyKeyboardRemove()
        )
    
    await state.clear()

@dp.message(ScheduleInput.waiting_for_schedule)
async def process_schedule_input(message: Message, state: FSMContext):
    try:
        schedule_data = parse_schedule_text(message.text)
        
        if len(schedule_data) < 7:
            await message.answer("❌ Пожалуйста, укажите расписание для всех дней недели.")
            return
            
        if not validate_schedule(schedule_data):
            await message.answer(
                "❌ <b>Некорректный формат.</b> Используйте:\n"
                "<i>день: время</i> (например: понедельник: 9-18)\n"
                "или 'выходной'\n\n"
                "Попробуйте еще раз:",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode="HTML"
            )
            return
        
        next_week_start = get_next_week_start_date()
        if db.save_schedule(message.from_user.id, next_week_start, schedule_data):
            logger.info(f"Schedule saved for user: {message.from_user.id}")
            await message.answer(
                "✅ <b>Расписание на следующую неделю успешно сохранено!</b>",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        else:
            logger.error(f"Failed to save schedule for user: {message.from_user.id}")
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

# ================== ОБРАБОТЧИКИ CALLBACK ==================

@dp.callback_query(F.data.in_(['current_week', 'next_week']))
async def process_week_choice(callback: CallbackQuery):
    if not db.is_user_registered(callback.from_user.id):
        await callback.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /start")
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
        os.remove(filename)
    except Exception as e:
        logger.error(f"Ошибка при отправке файла: {e}")
        await callback.message.answer(
            f"Не удалось отправить расписание на {week_name}. Попробуйте позже."
        )
    
    await callback.answer()

@dp.callback_query(F.data.startswith('day_'))
async def process_day_choice(callback: CallbackQuery):
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
        os.remove(filename)
    except Exception as e:
        logger.error(f"Ошибка при отправке файла: {e}")
        await callback.message.answer(
            f"Не удалось отправить расписание на {day}. Попробуйте позже."
        )
    
    await callback.answer()

# ================== СЛУЖЕБНЫЕ ФУНКЦИИ ==================

async def send_schedule_reminder():
    """Отправка напоминания о заполнении расписания"""
    users = db.get_all_users()
    for user in users:
        try:
            await bot.send_message(
                user['user_id'],
                "⏰ <b>Напоминание:</b> пожалуйста, заполните расписание на следующую неделю!\n"
                "Используйте кнопку '📝 Заполнить расписание' в меню.",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            logger.info(f"Reminder sent to user: {user['user_id']}")
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
            logger.info(f"Daily schedule sent to user: {user['user_id']}")
        except Exception as e:
            logger.error(f"Ошибка при отправке расписания пользователю {user['user_id']}: {e}")

async def on_startup():
    scheduler.add_job(send_schedule_reminder, 'cron', day_of_week='wed', hour=10)
    scheduler.add_job(send_daily_schedule, 'cron', hour=18)
    scheduler.start()
    logger.info("Bot and scheduler started")

async def on_shutdown():
    scheduler.shutdown()
    db.close()
    logger.info("Bot and scheduler stopped")

async def main():
    await on_startup()
    try:
        await dp.start_polling(bot)
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
