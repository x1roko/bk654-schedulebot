from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    ADMIN_ID = os.getenv('ADMIN_ID')
    
    ROLES = {
        'manager': 'Менеджер',
        'employee': 'Сотрудник',
        'universal': 'Универсал',
        'trainer': 'Тренер',
        'trainer_2': 'Тренер 2.0'
    }
    
    RATES = {
        'employee': 230,
        'universal': 240,
        'trainer': 260,
        'trainer_2': 270
    }
