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
        time.sleep(15)
        print('posting_tweet sleep stop')
        print("=" * 20)
    


def tagged_tweet_reply_scheduler():
    """ Runs the tweet reply scheduler every 15 minutes. """
    while True:
        tweet_reply_scheduler()
        time.sleep(2)


def posting_tweet_scheduler():
    """ Runs the posting tweet function every 4 hours. """
    while True:
        posting_tweet()
        time.sleep(5)


def selected_reply_scheduler_runner():
    """ Runs the selected reply function every 680 minutes. """
    while True:
        selected_reply_scheduler()
        time.sleep(15)


if __name__ == "__main__":
    try:
        tagged_tweet_reply_thread = threading.Thread(target=tagged_tweet_reply_scheduler, daemon=True)
        tagged_tweet_reply_thread.start()
        
        tweet_posting_thread = threading.Thread(target=posting_tweet_scheduler, daemon=True)
        tweet_posting_thread.start()
        
        selected_reply_thread = threading.Thread(target=selected_reply_scheduler_runner, daemon=True)
        selected_reply_thread.start()

        port = int(port)
        app.run(host='0.0.0.0', port=port, debug=False)

    except Exception as e:
        logging.error(f"An error occurred when starting the app: {str(e)}")
        print(f"An error occurred: {str(e)}")
