from twitter_functions import reply_tweet
import pytz
from datetime import datetime, timedelta

print('text')

# netherlands_tz = pytz.timezone("Europe/Amsterdam")

now = datetime.now()  

end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

interval = now - timedelta(hours=15)  
start_time = interval.strftime('%Y-%m-%dT%H:%M:%SZ')


username = "zaid_works515"

text = reply_tweet(username=username, start_time=start_time, end_time=end_time)

