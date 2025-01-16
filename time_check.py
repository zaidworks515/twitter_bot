from datetime import datetime


def time():
    # netherlands_tz = pytz.timezone("Europe/Amsterdam")
    now = datetime.now()  
    print(f"CURRENT TIME OF THE SERVER. {now}")
    
    
print(time)