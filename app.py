from flask import Flask
from flask_cors import CORS
from twitter_functions import post_tweet, reply_tagged_tweet, reply_tweet
import logging
from config import port, username
from datetime import datetime, timedelta
import schedule
import time
import threading



app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

categories = ['Artificial Intelligence', 'top sports news', 'Basketball', 'crypto', 'trending', 'tech']

current_category_index = 0  

post_scheduler_lock = threading.Lock()

def posting_tweet():
    with post_scheduler_lock:
        global current_category_index

        try:
            category = categories[current_category_index] 

            logging.info(f"Posting tweet for category: {category}")
            tweet = post_tweet(tweet_category=category)
            if tweet:
                logging.info("Tweet posted successfully!")
                current_category_index = (current_category_index + 1) % len(categories)
            else:
                logging.info("No tweet was posted.")
                current_category_index = (current_category_index + 1) % len(categories)


        except Exception as e:
            current_category_index = (current_category_index + 1) % len(categories)
            logging.error(f"Error in post_tweet: {e}", exc_info=True)


 
reply_scheduler_lock = threading.Lock()
def tweet_reply_scheduler():
    with reply_scheduler_lock:
        # netherlands_tz = pytz.timezone("Europe/Amsterdam")

        now = datetime.now()  

        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        interval = now - timedelta(hours=5)  
        start_time = interval.strftime('%Y-%m-%dT%H:%M:%SZ')

        logging.info(f"Start Time: {start_time}, End Time: {end_time}")
        
        try:
            json_response = reply_tagged_tweet(username, start_time, end_time)
            if json_response:
                logging.info(f"Response Posted: {json_response}")
                logging.info("=" * 40)
            else:
                print('No data found to be commented.')
        except Exception as e:
            logging.error(f"Error in scheduler: {e}", exc_info=True)

 
selected_reply_scheduler_lock = threading.Lock()
def selected_reply_scheduler():
    with selected_reply_scheduler_lock:
        accounts_list = ["ScottiePippen", "saylor", "elonmusk", "espn", "SportsCenter", 
                        "bleacherreport", "patrickbetdavid", "rovercrc", "RWAwatchlist_", 
                        "rawalerts", "AutismCapital", "MarioNawfal", "DailyLoud", "Cointelegraph", 
                        "EricTrump", "RealAlexJones", "BallIsLife", "VitalikButerin", "Ashcryptoreal"
                        ]
        
        now = datetime.now()  

        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        interval = now - timedelta(hours=15)
        start_time = interval.strftime('%Y-%m-%dT%H:%M:%SZ')

        try:
            for username in accounts_list:
                reply_tweet(username, start_time=start_time, end_time=end_time)
            
            print('tweets replied of selected accounts..')
            
        except Exception as e:
            print(f"An error occur: {e}") 
            


schedule.every(17).minutes.do(selected_reply_scheduler)
schedule.every(15).minutes.do(tweet_reply_scheduler)

schedule.every(240).minutes.do(posting_tweet) 



def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)
      

if __name__ == "__main__":
    try:
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

        port = int(port)
        app.run(host='0.0.0.0', port=port, debug=False)
            

    except Exception as e:
        logging.error(f"An error occurred when starting the app: {str(e)}")
        print(f"An error occurred: {str(e)}")
