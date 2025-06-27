import mysql.connector
from config import Config
import time
from typing import Optional, Dict, List

class Database:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self._connect_with_retry()
        self._create_tables()

    def _connect_with_retry(self, max_retries: int = 5, delay: int = 5):
        for attempt in range(max_retries):
            try:
                self.connection = mysql.connector.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME
                )
                self.cursor = self.connection.cursor(dictionary=True)
                print("Успешное подключение к БД")
                return
            except mysql.connector.Error as err:
                print(f"Попытка {attempt + 1} из {max_retries}: Ошибка подключения к БД: {err}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

    def _create_tables(self):
        try:
            # Таблица пользователей
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255) NOT NULL,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица расписания
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    week_start_date DATE,
                    monday VARCHAR(50),
                    tuesday VARCHAR(50),
                    wednesday VARCHAR(50),
                    thursday VARCHAR(50),
                    friday VARCHAR(50),
                    saturday VARCHAR(50),
                    sunday VARCHAR(50),
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE KEY unique_user_week (user_id, week_start_date)
                )
            """)
            
            self.connection.commit()
            print("Таблицы успешно созданы")
        except mysql.connector.Error as err:
            print(f"Ошибка при создании таблиц: {err}")
            raise

    def register_user(self, user_id: int, first_name: str, last_name: str) -> bool:
        """Регистрирует нового пользователя"""
        try:
            self.cursor.execute("""
                INSERT INTO users (user_id, first_name, last_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                first_name = VALUES(first_name),
                last_name = VALUES(last_name)
            """, (user_id, first_name, last_name))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Ошибка при регистрации пользователя: {err}")
            return False

    def is_user_registered(self, user_id: int) -> bool:
        """Проверяет, зарегистрирован ли пользователь"""
        try:
            self.cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            return bool(self.cursor.fetchone())
        except mysql.connector.Error as err:
            print(f"Ошибка при проверке регистрации пользователя: {err}")
            return False

    def get_user_name(self, user_id: int) -> Optional[str]:
        """Получает ФИО пользователя"""
        try:
            self.cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = %s", (user_id,))
            user = self.cursor.fetchone()
            return f"{user['last_name']} {user['first_name']}" if user else None
        except mysql.connector.Error as err:
            print(f"Ошибка при получении имени пользователя: {err}")
            return None

    def save_schedule(self, user_id: int, week_start_date: str, schedule_data: Dict) -> bool:
        """Сохраняет расписание пользователя"""
        try:
            self.cursor.execute("""
                INSERT INTO schedules (
                    user_id, week_start_date, 
                    monday, tuesday, wednesday, thursday, friday, saturday, sunday
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                monday = VALUES(monday),
                tuesday = VALUES(tuesday),
                wednesday = VALUES(wednesday),
                thursday = VALUES(thursday),
                friday = VALUES(friday),
                saturday = VALUES(saturday),
                sunday = VALUES(sunday)
            """, (
                user_id, week_start_date,
                schedule_data.get('monday', 'выходной'),
                schedule_data.get('tuesday', 'выходной'),
                schedule_data.get('wednesday', 'выходной'),
                schedule_data.get('thursday', 'выходной'),
                schedule_data.get('friday', 'выходной'),
                schedule_data.get('saturday', 'выходной'),
                schedule_data.get('sunday', 'выходной')
            ))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Ошибка при сохранении расписания: {err}")
            return False

    def get_week_schedule(self, week_start_date: str) -> List[Dict]:
        """Получает расписание всех на неделю"""
        try:
            self.cursor.execute("""
                SELECT u.first_name, u.last_name, s.* 
                FROM schedules s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.week_start_date = %s
                ORDER BY u.last_name, u.first_name
            """, (week_start_date,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Ошибка при получении расписания: {err}")
            return []

    def get_user_schedule(self, user_id: int, week_start_date: str) -> Optional[Dict]:
        """Получает расписание конкретного пользователя"""
        try:
            self.cursor.execute("""
                SELECT * FROM schedules 
                WHERE user_id = %s AND week_start_date = %s
            """, (user_id, week_start_date))
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Ошибка при получении расписания пользователя: {err}")
            return None

    def close(self):
        """Закрывает соединение с БД"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
