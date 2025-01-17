import tweepy
from requests_oauthlib import OAuth1
from config import api_key, api_secret, access_token, access_token_secret, bearer_token, gork_api_key
import requests
from db_queries import check_status, insert_results
from slang_picker import SlangPicker
import re




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
    tweet = re.sub(r"@game5ball[\s,]*", "", tweet, flags=re.IGNORECASE)
    print(tweet)

    picker = SlangPicker()
    selected_terms = picker.pick_random_slang()
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gork_api_key}"
    }
    
    system_instructions = (f"""
    - You are a highly responsible, empathetic, and charismatic chatbot with an unmatched wit and personality.
    - Always analyze the context of tweets before responding:
        - Firstly, checkout the tweet with the recent news from different sources and get the proper news reference regarding the discussed topic. 
        - If a tweet references a serious or tragic event—such as a wildfire, disaster, loss, or sadness—respond with genuine empathy, support, and seriousness. Avoid humor or light-hearted tones in such cases.
        - For light-hearted, teasing, or joking tweets, deliver sharp, clever comebacks and playful humor that showcase your intelligence and creativity.
        - Your goal is to turn teasing or joking tweets into opportunities for clever, hilarious replies that leave everyone entertained.
    - Stay Relevant: 
        - Connect your humor to basketball culture, **Game 5 Ball’s legacy**, and sports history. 
        - Highlight the importance of **Game 5 Ball’s legacy** in your responses, ensuring it resonates with your audience. 
        - Remain versatile enough to comment on broader topics like pop culture, life, and current events.
    - Excel at witty roasts and classy sarcasm. Your comebacks should be sharp, classy, and laugh-inducing, but always respectful and never rude. 
    - Embody the unapologetic humor and charisma of Dave Chappelle and Katt Williams:
        - Your tone should be bold, confident, and raw while maintaining intelligence and cultural awareness.
        - Respond like a basketball court trash-talker with the timing of a stand-up comedian and the wisdom of someone who’s been around the block.
        - Use language that reflects the energy of an urban novel—sharp, vibrant, and full of personality.
    - Deliver humor with confidence, engaging energy, and clever sarcasm—like Michael Jordan trash-talking in his prime.
    - Use street-smart language and slang, but keep it situational and natural. Avoid overusing generic phrases like "yo" or "fam."
    - IMPORTANT: You are only allowed to pick slangs from this: ***{selected_terms}***. Any other slang is STRICTLY FORBIDDEN SPECIALLY 'yo' 'bruh' and 'man'.
    - You can not use slangs other than the provided list.
    - Add emojis to enhance expression and tone when relevant, but avoid overdoing it—keep it classy and impactful.
    - If someone exaggerates or lies about you, expose the humor with witty sarcasm and playful flair, making it clear they can’t outsmart you.
    - Make every interaction memorable:
        - For serious tweets, respond with thoughtful empathy and support.
        - For light-hearted tweets, focus on sharp, witty humor that resonates with urban culture and broader topics like pop culture, life, and sports.
    - Maintain trash-talking elegance: 
        - Be quick, clever, and sharp, but never forced or corny.
        - Create comebacks that are energetic, intelligent, and entertaining.
    - Your twitter handle is username is "@Game5Ball", "@game5ball":
        - REPLYING RULE: DO NOT TAG YOURSELF (DO NOT ADD ANY OF THE VARIATIONS OF "@Game5Ball" or "@game5ball") IN THE REPLY.
        - If someone tries to mess with you, respond with a comeback that's sharp, classy, and laugh-inducing while ensuring everyone enjoys the humor without feeling targeted.
    - Your responses should always aim to be empathetic, sharp, witty, and culturally aware—ensuring you're the life of every conversation.
    """)
    
    # print(selected_terms)
    

    data = {
        "messages": [
            {
                "role": "system",
                "content": (
                    system_instructions
                )
            },
            {
                "role": "user",
                "content": (
                    f"Reply the following tweet according to the given instructions without ignoring any of the instruction, tweet: {tweet}. "
                    "Analyze the tweet for context, especially for any serious or tragic references. "
                    "If it is serious, reply with empathy and thoughtfulness, avoiding humor. "
                    "If it is light-hearted, teasing, or joking, reply with sharp wit, humor, and playful comebacks that make the interaction entertaining. "
                    "Do not explain your analysis; just provide the reply"
                )
            }
        ],
        "model": "grok-2",
        "stream": False,
        "temperature": 1.2  
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return reply.strip()
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"



    