from flask import Flask
from flask_cors import CORS
# from twitter_functions import post_tweet, reply_tagged_tweet, reply_tweet
import logging
from config import port, username
from datetime import datetime, timedelta
import schedule
import time
import threading



app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


selected_reply_scheduler_lock = threading.Lock()
def selected_reply_scheduler():
    with selected_reply_scheduler_lock:
        print("=" * 20)
        print('selected_reply_scheduler RUNNING...')
        print('selected_reply_scheduler sleep start')
        time.sleep(360)
        print('selected_reply_scheduler sleep stop')
        print("=" * 20)
        
    


reply_scheduler_lock = threading.Lock()
def tweet_reply_scheduler():
    with reply_scheduler_lock:
        print("=" * 20)
        print('tweet_reply_scheduler RUNNING...')
        print('tweet_reply_scheduler sleep start')
        time.sleep(1)
        print('tweet_reply_scheduler sleep stop')
        print("=" * 20)

    



post_scheduler_lock = threading.Lock()
def posting_tweet():
    with post_scheduler_lock:
        print('posting_tweet RUNNING...')
        print('posting_tweet sleep start')
        time.sleep(1)
        print('posting_tweet sleep stop')
        print("=" * 20)
    




def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)
        
        
def run_selected_reply_scheduler():
    thread = threading.Thread(target=selected_reply_scheduler)
    thread.start()


schedule.every(1).minutes.do(tweet_reply_scheduler)

schedule.every(2.5).minutes.do(posting_tweet) 

schedule.every(4).minutes.do(run_selected_reply_scheduler)


if __name__ == "__main__":
    try:
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

        port = int(port)
        app.run(host='0.0.0.0', port=port, debug=False)
            

    except Exception as e:
        logging.error(f"An error occurred when starting the app: {str(e)}")
        print(f"An error occurred: {str(e)}")
