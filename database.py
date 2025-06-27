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
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    role ENUM('manager', 'employee', 'universal', 'trainer', 'trainer_2') NOT NULL,
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

    def add_user(self, user_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str], role: str):
        """Добавляет нового пользователя или обновляет существующего"""
        try:
            self.cursor.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, role)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                role = VALUES(role)
            """, (user_id, username, first_name, last_name, role))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Ошибка при добавлении пользователя: {err}")
            return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получает данные пользователя по ID"""
        try:
            self.cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Ошибка при получении пользователя: {err}")
            return None

    def save_schedule(self, user_id: int, week_start_date: str, schedule_data: Dict):
        """Сохраняет расписание пользователя на неделю"""
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

    def get_schedule_for_week(self, week_start_date: str) -> List[Dict]:
        """Получает расписание всех пользователей на указанную неделю"""
        try:
            self.cursor.execute("""
                SELECT u.last_name, s.* 
                FROM schedules s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.week_start_date = %s
                ORDER BY u.last_name
            """, (week_start_date,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Ошибка при получении расписания: {err}")
            return []

    def get_tomorrow_schedule(self, day_of_week: str, week_start_date: str) -> List[Dict]:
        """Получает расписание на конкретный день недели"""
        try:
            self.cursor.execute(f"""
                SELECT u.last_name, s.{day_of_week} as schedule
                FROM schedules s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.week_start_date = %s AND s.{day_of_week} != 'выходной'
            """, (week_start_date,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Ошибка при получении расписания на день: {err}")
            return []

    def get_all_users(self) -> List[Dict]:
        """Получает список всех пользователей"""
        try:
            self.cursor.execute("SELECT * FROM users")
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Ошибка при получении списка пользователей: {err}")
            return []

    def add_user_by_username(self, username: str, role: str) -> bool:
        """Добавляет пользователя по username (для менеджера)"""
        try:
            self.cursor.execute("""
                INSERT INTO users (user_id, username, role)
                VALUES ((SELECT user_id FROM users WHERE username = %s), %s, %s)
                ON DUPLICATE KEY UPDATE role = VALUES(role)
            """, (username, username, role))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except mysql.connector.Error as err:
            print(f"Ошибка при добавлении пользователя по username: {err}")
            return False

    def get_users_for_calculation(self, week_start_date: str) -> List[Dict]:
        """Получает пользователей для расчета зарплаты"""
        try:
            self.cursor.execute("""
                SELECT u.user_id, u.last_name, u.role, 
                       s.monday, s.tuesday, s.wednesday, s.thursday, 
                       s.friday, s.saturday, s.sunday
                FROM users u
                LEFT JOIN schedules s ON u.user_id = s.user_id AND s.week_start_date = %s
                WHERE u.role != 'manager'
            """, (week_start_date,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Ошибка при получении пользователей для расчета: {err}")
            return []

    def close(self):
        """Закрывает соединение с БД"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
