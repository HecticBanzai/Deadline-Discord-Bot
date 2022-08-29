from datetime import datetime

def suffix(day):
    if day % 10 == 1:
        return str(day) + "st"
    elif day % 10 == 2:
        return str(day) + "nd"
    elif day % 10 == 3:
        return str(day) + "rd"
    else:
        return str(day) + "th"

months_table_to_int = {
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
    "December": 12,
    None: None
}

months_table_to_str = {
    1: "January",
    2: "Feburary",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
    None: None
}

days_in_month = {
    "January": 31,
    "Feburary": 28,
    "March": 31, 
    "April": 30,
    "May": 31, 
    "June": 30, 
    "July": 31, 
    "August": 31, 
    "September": 30, 
    "October": 31, 
    "November": 30, 
    "December": 31
}

tzname_to_localize = {
    "Hawaii": "US/Hawaii",
    "Aleutian": "US/Aleutian",
    "Alaska": "US/Alaska",
    "Pacific": "US/Pacific",
    "Mountain": "US/Mountain",
    "Central": "US/Central",
    "Eastern": "US/Eastern"
}