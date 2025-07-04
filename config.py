from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Настройки бота
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    ADMIN_ID: str = os.getenv('ADMIN_ID', '')
    
    # Настройки базы данных
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_USER: str = os.getenv('DB_USER', 'root')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_NAME: str = os.getenv('DB_NAME', 'schedule_bot')
    
    # Настройки расписания
    WORK_START_HOUR: int = 9
    WORK_END_HOUR: int = 18
    REMINDER_DAY: str = 'wednesday'  # День напоминания (среда)
    REMINDER_HOUR: int = 10          # Час отправки напоминания
    
    class Messages:
        WELCOME = "👋 Добро пожаловать в бот для управления расписанием!"
        HELP = "ℹ️ Используйте кнопки меню для работы с расписанием."
        REMINDER = "⏰ Не забудьте заполнить расписание на следующую неделю!"
