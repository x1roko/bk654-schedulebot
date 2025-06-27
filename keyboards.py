from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

def get_main_keyboard(role):
    keyboard = []
    
    if role in ['manager', 'universal']:
        keyboard.append([KeyboardButton(text='Получить расписание')])
        keyboard.append([KeyboardButton(text='Расписание на завтра')])
        keyboard.append([KeyboardButton(text='Расписание на день')])
    else:
        keyboard.append([KeyboardButton(text='Мое расписание')])
        keyboard.append([KeyboardButton(text='Расписание на завтра')])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_week_choice_keyboard():
    keyboard = [
        [InlineKeyboardButton(text='Текущая неделя', callback_data='current_week')],
        [InlineKeyboardButton(text='Следующая неделя', callback_data='next_week')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_day_choice_keyboard():
    days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    buttons = [
        [InlineKeyboardButton(text=day.capitalize(), callback_data=f'day_{day}')] 
        for day in days
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
