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
    """
    Posts a new tweet to the Game5Ball account based on a scheduled category.

    This function retrieves a tweet from the `post_tweet` function using a predefined 
    category list and posts it under a thread-safe lock to prevent concurrent execution.

    Functionality:
    --------------
    - Acquires a lock (`post_scheduler_lock`) to ensure only one tweet is posted at a time.
    - Fetches the current tweet category from the `categories` list using `current_category_index`.
    - Calls `post_tweet` to generate and post a tweet.
    - Updates `current_category_index` cyclically to move to the next category after each post.
    """
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
    """
    Schedules and posts replies to tweets that have tagged the Game5Ball account.

    This function:
    - Acquires a thread lock (`reply_scheduler_lock`) to ensure that only one instance runs at a time.
    - Defines a time window (last 4 hours) to fetch tweets mentioning the `Game5Ball` account.
    - Calls `reply_tagged_tweet` to retrieve and respond to tweets within the defined time window.
    - Logs the process, including the start and end times, responses, and any errors.

    Functionality:
    --------------
    - Defines a 4-hour time window to fetch recent mentions.
    - Calls `reply_tagged_tweet(username, start_time, end_time)` to fetch tweets that tagged the account.
    - If relevant tweets exist, logs the response; otherwise, it logs that no data was found.

    """
    with reply_scheduler_lock:
        # netherlands_tz = pytz.timezone("Europe/Amsterdam")

        now = datetime.now()  

        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        interval = now - timedelta(hours=4)  
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
    """
    Replies to tweets from a predefined list of selected accounts.

    This function:
    - Acquires a thread lock (`selected_reply_scheduler_lock`) to ensure only one instance runs at a time.
    - Defines a 13-hour time window to fetch tweets from selected accounts.
    - Iterates through a predefined list of accounts and replies to their latest tweets.
    - Introduces a delay of 1200 seconds (20 minutes) between replies to avoid spam-like behavior.
    - Logs errors and continues processing the remaining accounts if an exception occurs.

    Functionality:
    --------------
    - Defines a 13-hour time window for fetching tweets.
    - Calls `reply_tweet(username, start_time, end_time)` for each account in `accounts_list`.
    - Introduces a 20-minute delay between replies to prevent rate limiting.
    - Uses exception handling to ensure failures in one account do not affect the rest.
    """
    with selected_reply_scheduler_lock:
        accounts_list = ["ScottiePippen", "saylor", "elonmusk", "espn", "SportsCenter", 
                        "bleacherreport", "patrickbetdavid", "rovercrc", "RWAwatchlist_", 
                        "rawalerts", "AutismCapital", "MarioNawfal", "DailyLoud", "Cointelegraph", 
                        "EricTrump", "RealAlexJones", "BallIsLife", "VitalikButerin", "Ashcryptoreal",
                        "cz_binance", "alx", "nba", "KDTrey5", "KingJames", "ESPNNBA", "stephenasmith", 
                        "barstoolsports", "binance", "coinmarketcap", "coinbase", "coingecko", "brian_armstrong",
                        "AltcoinDailyio", "WatcherGuru"
                        ]
        
        now = datetime.now()  

        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        interval = now - timedelta(hours=13)
        start_time = interval.strftime('%Y-%m-%dT%H:%M:%SZ')


        for username in accounts_list:
            try:
                print(f"Processing {username}...")
                reply_tweet(username, start_time=start_time, end_time=end_time)
                time.sleep(1200)  
                
            except Exception as e:
                print(f"Error while replying to {username}: {e}")
                continue        
                
        print("Finished replying to selected accounts.")      




schedule.every(680).minutes.do(selected_reply_scheduler)

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