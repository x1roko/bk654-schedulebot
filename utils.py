from datetime import datetime, timedelta
import re

def parse_schedule_text(text):
    schedule = {}
    lines = text.split('\n')
    
    for line in lines:
        if ':' not in line:
            continue
            
        day_part, time_part = line.split(':', 1)
        day = day_part.strip().lower()
        time = time_part.strip().lower()
        
        # Нормализация названий дней
        day_mapping = {
            'понедельник': 'monday',
            'вторник': 'tuesday',
            'среда': 'wednesday',
            'четверг': 'thursday',
            'пятница': 'friday',
            'суббота': 'saturday',
            'воскресенье': 'sunday'
        }
        
        for ru_day, en_day in day_mapping.items():
            if ru_day in day:
                schedule[en_day] = time
                break
    
    return schedule

def validate_schedule(schedule):
    time_pattern = re.compile(r'^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$|^выходной$')
    
    for day, time in schedule.items():
        if not time_pattern.match(time):
            return False
    return True

def get_week_start_date(date=None):
    if date is None:
        date = datetime.now().date()
    return date - timedelta(days=date.weekday())

def get_next_week_start_date():
    return get_week_start_date() + timedelta(days=7)

def get_day_of_week(date=None):
    if date is None:
        date = datetime.now().date()
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[date.weekday()]

def format_schedule_for_tomorrow(schedule_entries, day_name):
    hours = [f"{hour:02d}:00" for hour in range(8, 23)]
    result = f"Расписание на {day_name}:\n\n"
    result += "Фамилия | " + " | ".join(hours) + "\n"
    
    for entry in schedule_entries:
        last_name = entry['last_name']
        time_range = entry['schedule']
        
        if time_range == 'выходной':
            continue
            
        start_time, end_time = time_range.split('-')
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        
        time_slots = []
        for hour in range(8, 23):
            if start_hour <= hour < end_hour:
                time_slots.append("✓")
            else:
                time_slots.append("✗")
                
        result += f"{last_name} | " + " | ".join(time_slots) + "\n"
    
    return result

def calculate_working_hours(time_str):
    """Расчет количества рабочих часов из строки расписания"""
    if time_str == 'выходной':
        return 0

    try:
        start, end = time_str.split('-')
        start_time = datetime.strptime(start.strip(), '%H:%M') if ':' in start else datetime.strptime(start.strip(), '%H')
        end_time = datetime.strptime(end.strip(), '%H:%M') if ':' in end else datetime.strptime(end.strip(), '%H')
        return (end_time - start_time).seconds / 3600
    except:
        return 0

def calculate_salary(user_data, rates):
    """Расчет зарплаты для одного пользователя"""
    total_hours = 0
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    for day in days:
        time_str = user_data.get(day, 'выходной')
        total_hours += calculate_working_hours(time_str)

    rate = rates.get(user_data['role'], 0)
    salary = total_hours * rate
    return total_hours, salary
