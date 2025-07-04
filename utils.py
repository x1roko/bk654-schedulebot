import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List

def parse_schedule_text(text: str) -> Dict[str, str]:
    """Парсит текст с расписанием в словарь"""
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

def validate_schedule(schedule: Dict[str, str]) -> bool:
    """Проверяет корректность формата расписания"""
    if not schedule:
        return False
        
    time_pattern = re.compile(
        r'^(\d{1,2})\s*-\s*(\d{1,2})$|'
        r'^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$|'
        r'^выходной$',
        re.IGNORECASE
    )
    
    for day, time in schedule.items():
        if not time_pattern.match(time.strip()):
            return False
            
    return True

def get_week_start_date(date: Optional[datetime.date] = None) -> datetime.date:
    """Возвращает дату понедельника текущей недели"""
    if date is None:
        date = datetime.now().date()
    return date - timedelta(days=date.weekday())

def get_next_week_start_date() -> datetime.date:
    """Возвращает дату понедельника следующей недели"""
    return get_week_start_date() + timedelta(days=7)

def get_day_of_week(date: Optional[datetime.date] = None) -> str:
    """Возвращает название дня недели на английском"""
    if date is None:
        date = datetime.now().date()
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[date.weekday()]

def format_schedule_for_tomorrow(schedule_entries: List[Dict], day_name: str) -> str:
    """Форматирует расписание на завтра в текстовом виде"""
    result = f"📅 <b>Расписание на {day_name.capitalize()}:</b>\n\n"
    
    for entry in schedule_entries:
        name = f"{entry['last_name']} {entry['first_name']}"
        time_range = entry.get(day_name, 'выходной')
        
        if time_range.lower() == 'выходной':
            result += f"👤 {name}: <i>выходной</i>\n"
        else:
            result += f"👤 {name}: {time_range}\n"
    
    return result
