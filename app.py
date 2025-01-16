from flask import Flask, request, jsonify
from flask_cors import CORS
from twitter_functions import post_tweet, reply_tweet, reply_tagged_tweet
import logging
from config import port, username
from datetime import datetime, timedelta
import schedule
import time
import threading
import pytz



app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@app.route("/post_tweet", methods=['POST'])
def post_tweet_endpoint():
    data = request.json
    try:
        if not data or 'text' not in data:
            return jsonify({'status': False, 'message': 'Missing "text" in the request payload'}), 400

        text = data.get('text')
        if not text.strip():
            return jsonify({'status': False, 'message': 'Tweet "text" cannot be empty'}), 400

        tweet = post_tweet(text=text)  # will return a dictionary

        if tweet:
            return jsonify({'status': True, 'data': tweet}), 200
        else:
            return jsonify({'status': False, 'message': 'Failed to post the tweet'}), 500

    except Exception as e:
        return jsonify({'status': False, 'message': str(e)}), 500
         
   
@app.route("/reply_tweet", methods=['POST'])
def reply_tweet_endpoint():
    data = request.json
    username = data.get('username')
    reply_text = data.get('reply_text')
    # print(username, reply_text)
    
    try:
        if not username or not reply_text:
            return jsonify({'status': False, 'message': 'Missing "data or reply text or username" in the request payload'}), 400

        
        if not reply_text.strip():
            return jsonify({'status': False, 'message': 'Tweet "text" cannot be empty'}), 400

        response_reply_tweet = reply_tweet(username=username, reply_text=reply_text)  # will return a dictionary

        if response_reply_tweet:
            return jsonify({'status': True, 'data': response_reply_tweet}), 200
        else:
            return jsonify({'status': False, 'message': 'Failed to post the reply of the given tweet'}), 500

    except Exception as e:
        return jsonify({'status': False, 'message': str(e)}), 500
 
scheduler_lock = threading.Lock()

def scheduler():
    with scheduler_lock:
        # netherlands_tz = pytz.timezone("Europe/Amsterdam")

        now = datetime.now()  

        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        interval = now - timedelta(hours=12)
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

 
schedule.every(250).minutes.do(scheduler)

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
