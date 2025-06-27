import re
from datetime import datetime, timedelta

def parse_schedule_text(text):
    schedule = {}
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    day_mapping = {
        'понедельник': 'monday',
        'вторник': 'tuesday',
        'среда': 'wednesday',
        'четверг': 'thursday',
        'пятница': 'friday',
        'суббота': 'saturday',
        'воскресенье': 'sunday'
    }

    for line in lines:
        if ':' not in line:
            continue
            
        day_part, time_part = line.split(':', 1)
        day = day_part.strip().lower()
        time = time_part.strip().lower()
        
        for ru_day, en_day in day_mapping.items():
            if ru_day in day:
                schedule[en_day] = time
                break
    
    return schedule

def validate_schedule(schedule):
    if not schedule:
        return False
        
    time_pattern = re.compile(r'^(\d{1,2})\s*-\s*(\d{1,2})$|^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$|^выходной$', re.IGNORECASE)
    
    for day, time in schedule.items():
        if not time_pattern.match(time.strip()):
            return False
            
    return True

def get_week_start_date(date=None):
    """Возвращает дату понедельника текущей недели"""
    if date is None:
        date = datetime.now().date()
    return date - timedelta(days=date.weekday())

def get_next_week_start_date():
    """Возвращает дату понедельника следующей недели"""
    return get_week_start_date() + timedelta(days=7)

def get_day_of_week(date=None):
    """Возвращает название дня недели на английском"""
    if date is None:
        date = datetime.now().date()
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[date.weekday()]

def format_schedule_for_tomorrow(schedule_entries, day_name):
    """Форматирует расписание на завтра"""
    hours = [f"{hour:02d}:00" for hour in range(8, 23)]
    result = f"Расписание на {day_name}:\n\n"
    result += "Фамилия Имя | " + " | ".join(hours) + "\n"
    
    for entry in schedule_entries:
        name = f"{entry['last_name']} {entry['first_name']}"
        time_range = entry.get('schedule', 'выходной')
        
        if time_range == 'выходной':
            continue
            
        try:
            start_time, end_time = time_range.split('-')
            start_hour = int(start_time.split(':')[0]) if ':' in start_time else int(start_time)
            end_hour = int(end_time.split(':')[0]) if ':' in end_time else int(end_time)
            
            time_slots = []
            for hour in range(8, 23):
                if start_hour <= hour < end_hour:
                    time_slots.append("✓")
                else:
                    time_slots.append("✗")
                    
            result += f"{name} | " + " | ".join(time_slots) + "\n"
        except ValueError:
            continue
    
    return result
