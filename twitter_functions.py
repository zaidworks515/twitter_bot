from datetime import datetime, timedelta
import tweepy
from requests_oauthlib import OAuth1
from config import api_key, api_secret, access_token, access_token_secret, bearer_token, gork_api_key
import requests
from db_queries import check_status, insert_results



def post_tweet(text):    
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )


    try:
        response = client.create_tweet(text=text)
        if response:    
            print(f"Tweet posted successfully: {response.data}")
            return response.data # dict

    except tweepy.TweepyException as e:
        print(f"Error: {e}")
        return None


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r


def comment_on_tweet(tweet_id, comment_text, consumer_key, consumer_secret, access_token, access_token_secret):
    print(tweet_id, comment_text)
    comment_url = "https://api.twitter.com/2/tweets"
    
    auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)
    
    payload = {
        "text": comment_text,
        "reply": {
            "in_reply_to_tweet_id": tweet_id  
        }
    }
    
    print(payload)
    
    response = requests.post(comment_url, json=payload, auth=auth)
    
    if response.status_code != 201:
        raise Exception(f"Failed to post comment: {response.status_code} {response.text}")
    
    comment_data = response.json()
    
    return comment_data


def reply_tweet(username=None, reply_text=None):
    # print(username, reply_text)
    user_url = f"https://api.twitter.com/2/users/by/username/{username}"
    
    user_response = requests.get(user_url, headers={"Authorization": f"Bearer {bearer_token}"})
    
    if user_response.status_code != 200:
        raise Exception(f"Failed to fetch user details: {user_response.status_code} {user_response.text}")
    
    user_data = user_response.json()
    user_id = user_data["data"]["id"]

    print(f"User ID of {username}: {user_id}")

    tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets?max_results=5"

    
    response = requests.request("GET", tweets_url, auth=bearer_oauth)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    json_response = response.json()
    
    tweet_id = json_response["data"][0]['id']
    tweet_text = json_response["data"][0]['text']  #will use it later with GORK RESPONSE
    
    comment_text = f"@{username} {reply_text}"
    
    comment_data = comment_on_tweet(tweet_id, comment_text, api_key, api_secret, access_token, access_token_secret)
    
    if comment_data:
        return comment_data
    else:
        return None
    
    
def bearer_oauth2(r):
    """
    Method required by bearer token authentication.
    """
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2UserMentionsPython"
    return r
    

def fetch_tagged_tweets(username, start_time=None, end_time=None):

    if not bearer_token:
        raise ValueError("Bearer token not found. Set the BEARER_TOKEN environment variable.")

    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "v2UserMentionsPython"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Error fetching user ID: {response.status_code} {response.text}"
        )
        
    user_data = response.json()
    user_id = user_data["data"]["id"]
    
    mention_url = f"https://api.twitter.com/2/users/{user_id}/mentions"
    params = {
        "tweet.fields": "created_at,author_id"
    }
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    response = requests.get(mention_url, headers=headers, params=params)
    if response.status_code == 429:
        raise Exception("Rate limit exceeded. Try again later.")
    elif response.status_code != 200:
        raise Exception(
            f"Error fetching mentions: {response.status_code} {response.text}"
        )
    
    return response.json()


def reply_tagged_tweet(username, start_time=None, end_time=None):
    try:

        json_response = fetch_tagged_tweets(username, start_time, end_time)
        print("======= FETCHED RESPONSE =======")
        print(json_response)
        comment_data = None
        
        for row in json_response['data']:
            author_id = row['author_id']
            tweet_id = row['id']
            tweet_text = row['text']
            
            if tweet_id and author_id and tweet_text:
                status = check_status(tweet_id)
                print("STATUS CHECKED....")
                if status != 'successful' or not status:
                    
                    reply_text = get_gork_response(tweet_text)
                       
                    if reply_text:            
                        comment_text = f"{reply_text}"
                        print("REPLY CREATED BY GORK")
                    
                        comment_data = comment_on_tweet(tweet_id, comment_text, api_key, api_secret, access_token, access_token_secret)
                
                        if comment_data:
                            # comment_data = comment_data.encode("utf-8")
                            print('Comment Successful..........')
                            id = insert_results(tagged_tweet_id=tweet_id, 
                                                author_id=author_id, 
                                                tagged_tweet=tweet_text, 
                                                replied_comments=comment_text, 
                                                post_status='successful')
                        
        return comment_data
    except Exception as e:
        return e
    
def get_gork_response(tweet):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gork_api_key}"
    }

    data = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a highly responsible, empathetic, and charismatic chatbot. "
                    "When responding to tweets, always analyze the content for context. "
                    "If the tweet references a serious or tragic event, such as a wildfire, disaster, destruction, loss, or sadness, respond with empathy, support, and seriousness."
                    "Avoid humor or light-hearted tones in such cases."
                    "If the tweet is light-hearted, neutral, teasing, or joking, respond with sharp wit, playful jabs, and humor that make the interaction entertaining."
                    "You excel at best clever comebacks and humorous roasts that are sharp, classy, and leave everyone speechless—but always maintain respect and never be rude."
                    "Use Street Language tone, slangs in the response"
                    "Your goal is to turn teasing or joking tweets into opportunities for clever, hilarious replies that showcase intelligence and creativity."
                    "If someone exaggerates or lies about you, expose the humor in it with witty sarcasm and playful flair, making it clear they can’t outsmart you."
                    "Your responses should be the perfect blend of 'keh ke lena'—sharp, classy, and laugh-inducing—ensuring everyone enjoys the humor without feeling targeted."
                    "Add emojis to enhance expression for extra flair, but only when relevant."
                    "You are the life of the conversation, whether serious, witty, or jolly."
                    "If you have @username in the tweet, avoid repeating it in the reply."
                    "Your name is Zaid and your account is @zaid_works515, give a comeback when someone try to mess with you."
                    
                )
            },
            {
                "role": "user",
                "content": (
                    f"The following is a tweet where I was tagged: '{tweet}'."
                    "Analyze the tweet for context, especially for any serious or tragic references."
                    "If it is serious, reply with empathy and thoughtfulness, avoiding humor."
                    "If it is light-hearted, teasing, or joking, reply with sharp wit, humor, and playful comebacks that make the interaction entertaining."
                    "Do not explain your analysis; just provide the reply."
                )
            }
        ],
        "model": "grok-2",
        "stream": False,
        "temperature": 0.2  
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return reply.strip()
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
