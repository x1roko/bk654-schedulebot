import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from config import Config
from database import Database
from keyboards import get_main_keyboard, get_week_choice_keyboard, get_day_choice_keyboard
from utils import parse_schedule_text, validate_schedule, get_week_start_date, get_next_week_start_date, get_day_of_week, format_schedule_for_tomorrow, calculate_working_hours, calculate_salary
from excel_generator import generate_week_schedule_excel, generate_day_schedule_excel
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher()
db = Database()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    # По умолчанию назначаем роль сотрудника, менеджер может изменить через админку
    db.add_user(user.id, user.username, user.first_name, user.last_name, 'employee')
    
    await message.answer(
        f"Добро пожаловать, {user.first_name}!\n"
        "Я бот для учета расписания сотрудников.\n\n"
        "Каждую среду я буду напоминать вам о необходимости указать расписание на следующую неделю.\n"
        "Также я буду присылать вам ежедневное расписание на завтра.",
        reply_markup=get_main_keyboard('employee')
    )

@dp.message(F.text == "Мое расписание")
async def my_schedule(message: Message):
    await message.answer(
        "Выберите неделю:",
        reply_markup=get_week_choice_keyboard()
    )

@dp.message(F.text == "Получить расписание")
async def get_schedule(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Вы не зарегистрированы в системе.")
        return
    
    await message.answer(
        "Выберите неделю:",
        reply_markup=get_week_choice_keyboard()
    )

@dp.message(F.text == "Расписание на завтра")
async def tomorrow_schedule(message: Message):
    tomorrow = datetime.now() + timedelta(days=1)
    day_name = get_day_of_week(tomorrow.date())
    week_start = get_week_start_date(tomorrow.date())
    
    schedule_entries = db.get_tomorrow_schedule(day_name, week_start)
    formatted_schedule = format_schedule_for_tomorrow(schedule_entries, day_name)
    
    await message.answer(formatted_schedule)

@dp.message(F.text == "Расписание на день")
async def day_schedule(message: Message):
    await message.answer(
        "Выберите день:",
        reply_markup=get_day_choice_keyboard()
    )

@dp.callback_query(F.data.startswith('day_'))
async def process_day_choice(callback: CallbackQuery):
    day = callback.data.split('_')[1]
    today = datetime.now().date()
    week_start = get_week_start_date(today)
    
    schedule_entries = db.get_tomorrow_schedule(day, week_start)
    filename = generate_day_schedule_excel(schedule_entries, day)
    
    with open(filename, 'rb') as file:
        await callback.message.answer_document(
            file,
            caption=f"Расписание на {day}"
        )
    
    os.remove(filename)
    await callback.answer()

@dp.callback_query(F.data.in_(['current_week', 'next_week']))
async def process_week_choice(callback: CallbackQuery):
    if callback.data == 'current_week':
        week_start = get_week_start_date()
        week_name = "текущую неделю"
    else:
        week_start = get_next_week_start_date()
        week_name = "следующую неделю"
    
    schedule_data = db.get_schedule_for_week(week_start)
    if not schedule_data:
        await callback.message.answer(f"На {week_name} расписание еще не заполнено.")
        return
    
    filename = generate_week_schedule_excel(schedule_data, week_start)
    
    with open(filename, 'rb') as file:
        await callback.message.answer_document(
            file,
            caption=f"Расписание на {week_name}"
        )
    
    # Отправляем текстовую версию
    text_schedule = "Фамилия | Понедельник | Вторник | Среда | Четверг | Пятница | Суббота | Воскресенье\n"
    for entry in schedule_data:
        text_schedule += f"{entry['last_name']} | {entry.get('monday', 'выходной')} | {entry.get('tuesday', 'выходной')} | {entry.get('wednesday', 'выходной')} | {entry.get('thursday', 'выходной')} | {entry.get('friday', 'выходной')} | {entry.get('saturday', 'выходной')} | {entry.get('sunday', 'выходной')}\n"
    
    await callback.message.answer(text_schedule)
    
    os.remove(filename)
    await callback.answer()

@dp.message(Command("add_user"))
async def cmd_add_user(message: Message):
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'manager':
        await message.answer("У вас нет прав для добавления пользователей.")
        return
    
    args = message.text.split()[1:]
    if len(args) != 2:
        await message.answer("Использование: /add_user @username роль\n\nДоступные роли: сотрудник, универсал, тренер, тренер_2")
        return
    
    username = args[0].replace('@', '')
    role = args[1].lower()
    
    role_mapping = {
        'сотрудник': 'employee',
        'универсал': 'universal',
        'тренер': 'trainer',
        'тренер_2': 'trainer_2'
    }
    
    if role not in role_mapping:
        await message.answer("Некорректная роль. Доступные роли: сотрудник, универсал, тренер, тренер_2")
        return
    
    if db.add_user_by_username(username, role_mapping[role]):
        await message.answer(f"Пользователь {username} успешно добавлен с ролью {role}")
    else:
        await message.answer(f"Не удалось добавить пользователя {username}. Возможно, он не зарегистрирован в боте.")

@dp.message(Command("calculate"))
async def cmd_calculate(message: Message):
    week_start = get_week_start_date()
    users_data = db.get_users_for_calculation(week_start)
    
    if not users_data:
        await message.answer("Нет данных для расчета.")
        return
    
    result = "Расчет зарплаты за текущую неделю:\n\n"
    result += "Фамилия | Роль | Часы | Зарплата\n"
    
    total_company = 0
    
    for user in users_data:
        total_hours = 0
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in days:
            time_str = user.get(day, 'выходной')
            total_hours += calculate_working_hours(time_str)
        
        rate = Config.RATES.get(user['role'], 0)
        salary = total_hours * rate
        total_company += salary
        
        result += f"{user['last_name']} | {Config.ROLES[user['role']]} | {total_hours:.1f} ч. | {salary:.2f} руб.\n"
    
    result += f"\nОбщая сумма выплат: {total_company:.2f} руб."
    
    await message.answer(result)

@dp.message()
async def process_schedule_input(message: Message):
    user = db.get_user(message.from_user.id)
    if not user or user['role'] == 'manager':
        return
    
    try:
        schedule_data = parse_schedule_text(message.text)
        if not validate_schedule(schedule_data):
            await message.answer("Некорректный формат расписания. Пожалуйста, используйте формат:\n"
                               "понедельник: 12-20\n"
                               "вторник: 12:00-20:30\n"
                               "среда: выходной\n"
                               "... и так для всех дней недели")
            return
        
        next_week_start = get_next_week_start_date()
        db.save_schedule(user['user_id'], next_week_start, schedule_data)
        await message.answer("Ваше расписание успешно сохранено!")
    except Exception as e:
        logger.error(f"Ошибка при обработке расписания: {e}")
        await message.answer("Произошла ошибка при обработке вашего расписания. Пожалуйста, попробуйте еще раз.")

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
        if user['role'] != 'manager':  # Отправляем только сотрудникам
            try:
                await bot.send_message(
                    user['user_id'],
                    "Пожалуйста, укажите ваше расписание на следующую неделю.\n\n"
                    "Пример формата:\n"
                    "понедельник: 12-20\n"
                    "вторник: 12:00-20:30\n"
                    "среда: выходной\n"
                    "... и так для всех дней недели"
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания пользователю {user['user_id']}: {e}")

async def send_daily_schedule():
    """Отправка расписания на завтра"""
    tomorrow = datetime.now() + timedelta(days=1)
    day_name = get_day_of_week(tomorrow.date())
    week_start = get_week_start_date(tomorrow.date())
    
    schedule_entries = db.get_tomorrow_schedule(day_name, week_start)
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
