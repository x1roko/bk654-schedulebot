from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура с кнопками меню"""
    buttons = [
        [KeyboardButton(text="📝 Заполнить расписание")],
        [KeyboardButton(text="👀 Мое расписание")],
        [KeyboardButton(text="📅 Расписание на завтра")],
        [KeyboardButton(text="👥 Общее расписание")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_week_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора недели"""
    buttons = [
        [InlineKeyboardButton(text='Текущая неделя', callback_data='current_week')],
        [InlineKeyboardButton(text='Следующая неделя', callback_data='next_week')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_day_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора дня недели"""
    days = {
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье'
    }
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f'day_{day}')]
        for day, name in days.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
