from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text="Заполнить расписание")],
        [KeyboardButton(text="Мое расписание")],
        [KeyboardButton(text="Расписание на завтра")],
        [KeyboardButton(text="Общее расписание")]
    ]
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
