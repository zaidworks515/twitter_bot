import tweepy
from requests_oauthlib import OAuth1
from config import api_key, api_secret, access_token, access_token_secret, bearer_token
import requests



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
    
    

def fetch_tagged_tweets(username, limit: int = 5):

    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "v2UserMentionsPython"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(
            f"Request returned an error: {response.status_code} {response.text}"
        )
        
    user_data = response.json()
    
    user_id = user_data["data"]["id"]
    
    mention_url = f"https://api.twitter.com/2/users/{user_id}/mentions?max_results={limit}"
    params = {"tweet.fields": "created_at"}
    # params = {"tweet.fields": "created_at,author_id"}

    response = requests.request("GET", mention_url, auth=bearer_oauth2, params=params)
    print(response.status_code)
    
    if response.status_code != 200:
        raise Exception(
            f"Request returned an error: {response.status_code} {response.text}"
        )
    
    
    return response.json()


def reply_tagged_tweet(username, reply_text):

    json_response = fetch_tagged_tweets(username)
    
    tweet_id = json_response["data"][0]['id']
    tweet_text = json_response["data"][0]['text'] 
    
    comment_text = f"{reply_text}"
    
    if tweet_id:
        comment_data = comment_on_tweet(tweet_id, comment_text, api_key, api_secret, access_token, access_token_secret)
    
    if comment_data:
        return comment_data
    else:
        return None
