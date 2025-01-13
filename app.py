from flask import Flask, request, jsonify
from flask_cors import CORS
from twitter_functions import post_tweet, reply_tweet, reply_tagged_tweet
import logging
from config import port

app = Flask(__name__)
CORS(app)


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
  
  
@app.route("/reply_tagged_tweet", methods=['POST'])
def reply_tag_tweet_endpoint():
    data = request.json
    username = data.get('username') # jiskay tags check krne ho'n 
    
    
    try:
        if not username:
            return jsonify({'status': False, 'message': 'Missing "username" in the request payload'}), 400

        

        response_reply_tweet = reply_tagged_tweet(username=username)  # will return a dictionary
        
        
        if response_reply_tweet:
            return jsonify({'status': True, 'data': response_reply_tweet}), 200
        else:
            return jsonify({'status': False, 'message': 'Failed to post the reply of the given tweet'}), 500

    except Exception as e:
        return jsonify({'status': False, 'message': str(e)}), 500
  
  
    

if __name__ == "__main__":
    try:
        port = int(port)
        app.run(host='0.0.0.0', port=port, debug=True)
    
    except Exception as e:
        logging.error(f"An error occurred when starting the app: {str(e)}")
        print(f"An error occurred: {str(e)}")
    
    
    
        







