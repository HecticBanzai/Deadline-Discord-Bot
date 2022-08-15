def suffix(day):
    if day % 10 == 1:
        return str(day) + "st"
    elif day % 10 == 2:
        return str(day) + "nd"
    elif day % 10 == 3:
        return str(day) + "rd"
    else:
        return str(day) + "th"

def create_time_string(hour, minute):
    if hour == 12 or hour == 0:
      str_hour = "12"
    else:
      str_hour = str(hour % 12)

    str_minute = ""
    meridiem = ""

    if hour >= 12:
        meridiem = "PM"
    else:
        meridiem = "AM"

    if minute < 10:
        str_minute = "0" + str(minute)
    else:
        str_minute = str(minute)
    
    return f"{str_hour}:{str_minute} {meridiem}"

def create_date_string(month, day, year):
    return f"{month} {day}, {year}"

months_table = {
    "January": 1,
    "Feburary": 2,
    "March": 3, 
    "April": 4,
    "May": 5, 
    "June": 6, 
    "July": 7, 
    "August": 8, 
    "September": 9, 
    "October": 10, 
    "November": 11, 
    "December": 12
}