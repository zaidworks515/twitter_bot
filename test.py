from twitter_functions import reply_tweet
from datetime import datetime, timedelta
import pytz


netherlands_tz = pytz.timezone("Europe/Amsterdam")


now = datetime.now(netherlands_tz)  

end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

interval = now - timedelta(hours=13)
start_time = interval.strftime('%Y-%m-%dT%H:%M:%SZ')


reply_tweet(username='ESPNNBA', start_time=start_time, end_time=end_time, max_tweet=5)