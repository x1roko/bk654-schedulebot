import openpyxl
from openpyxl.styles import Font, Alignment

def generate_week_schedule_excel(schedule_data, week_start_date):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Расписание"
    
    # Заголовки
    days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    headers = ['Фамилия Имя'] + days
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Данные
    for row_num, entry in enumerate(schedule_data, 2):
        name = f"{entry['last_name']} {entry['first_name']}"
        ws.cell(row=row_num, column=1, value=name)
        ws.cell(row=row_num, column=2, value=entry.get('monday', 'выходной'))
        ws.cell(row=row_num, column=3, value=entry.get('tuesday', 'выходной'))
        ws.cell(row=row_num, column=4, value=entry.get('wednesday', 'выходной'))
        ws.cell(row=row_num, column=5, value=entry.get('thursday', 'выходной'))
        ws.cell(row=row_num, column=6, value=entry.get('friday', 'выходной'))
        ws.cell(row=row_num, column=7, value=entry.get('saturday', 'выходной'))
        ws.cell(row=row_num, column=8, value=entry.get('sunday', 'выходной'))
    
    # Настройка ширины столбцов
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width
    
    # Сохранение файла
    filename = f"schedule_{week_start_date}.xlsx"
    wb.save(filename)
    return filename

def generate_day_schedule_excel(schedule_entries, day_name):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Расписание на {day_name}"
    
    # Заголовки
    hours = [f"{hour:02d}:00" for hour in range(8, 23)]
    headers = ['Фамилия Имя'] + hours
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    
    # Данные
    for row_num, entry in enumerate(schedule_entries, 2):
        name = f"{entry['last_name']} {entry['first_name']}"
        time_range = entry.get('schedule', 'выходной')
        
        ws.cell(row=row_num, column=1, value=name)
        
        if time_range == 'выходной':
            continue
            
        start_time, end_time = time_range.split('-')
        start_hour = int(start_time.split(':')[0])
        end_hour = int(end_time.split(':')[0])
        
        for col_num, hour in enumerate(range(8, 23), 2):
            if start_hour <= hour < end_hour:
                ws.cell(row=row_num, column=col_num, value="✓")
            else:
                ws.cell(row=row_num, column=col_num, value="✗")
    
    # Настройка ширины столбцов
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column].width = adjusted_width
    
    # Сохранение файла
    filename = f"schedule_{day_name}.xlsx"
    wb.save(filename)
    return filename
