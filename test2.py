# from twitter_functions import fetch_tagged_tweets
# import pytz
# from datetime import datetime, timedelta
# import json

# netherlands_tz = pytz.timezone("Europe/Amsterdam")

# now = datetime.now(netherlands_tz)  

# end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

# interval = now - timedelta(hours=56)  
# start_time = interval.strftime('%Y-%m-%dT%H:%M:%SZ')


# response = fetch_tagged_tweets(username='game5ball', start_time=start_time, end_time=end_time)

# if response:  
#     with open('fetch_tagged_tweets.json', 'w') as file:
#         json.dump(response, file, indent=4)
#     print("Data stored successfully...")
# else:
#     print("No data received.")
    
    
    



import json 
from db_queries import insert_results, check_status
from twitter_functions import get_gork_response

with open('fetch_tagged_tweets2.json', 'r') as file:
    data = json.load(file)


for row in reversed(data['data']):
    author_id = row['author_id']
    tweet_id = row['id']
    tweet_text = row['text']
    conversation_id = row['conversation_id'] 
    
    
    
    status, is_reply, reply_count, previous_reply = check_status(tweet_id, conversation_id, author_id)
    # previous_reply = previous_reply[::-1]
    print(f"CHAIN::: {previous_reply}")

    reply_text = get_gork_response(tweet_text, is_reply, reply_count, previous_reply)
    # print(tweet_text)
    # print(reply_text)
    print('='*20)
    
    print('Comment Successful..........')
    id = insert_results(tagged_tweet_id=tweet_id, 
                        author_id=author_id, 
                        tagged_tweet=tweet_text, 
                        replied_comments=reply_text,
                        conversation_id=conversation_id,
                        post_status='successful')
    print(f'data saved against ID: {id}')
    
    print('='*20)
    
    



# with open('fetch_tagged_tweets.json', 'r') as file:
#     data = json.load(file)

# chain = []
# for row in data['data']:
#     author_id = row['author_id']
#     tweet_id = row['id']
#     tweet_text = row['text']
#     conversation_id = row['conversation_id'] 
    
#     status, is_reply, reply_count, previous_reply = check_status(tweet_id, conversation_id, author_id)
    
#     previous_reply = previous_reply[::-1]
#     chain.append(previous_reply)
    


# if chain:  
#     with open('fetch_chain.json', 'w') as file:
#         json.dump(chain, file, indent=4)
#     print("Data stored successfully...")
# else:
#     print("No data received.")
