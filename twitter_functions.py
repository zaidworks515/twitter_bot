from datetime import datetime, timedelta
import tweepy
from requests_oauthlib import OAuth1
from config import api_key, api_secret, access_token, access_token_secret, bearer_token, gork_api_key, news_api
import requests
from db_queries import check_status, insert_results, check_tweets, insert_results_make_tweets
from slang_picker import SlangPicker
import re
from sentence_transformers import SentenceTransformer, util


model = SentenceTransformer('all-MiniLM-L6-v2')

def post_tweet(tweet_category=None):
    """
    Verify the existence of a similar tweet. If no similar tweet exists, post a new tweet.
    """
    
    # print("========"*30)  
    # print(tweet_category)
    # print("========"*30) 

    post = False

    article = get_news(query=tweet_category)

    if not article:
        print("No articles found for the given category.")
        return None

    today = datetime.today()
    to_date = today.strftime('%Y-%m-%d')
    from_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    tweets = check_tweets(tweet_category, from_date, to_date)

    fetched_title = article[0]['title']
    fetched_description = article[0]['description']
    embedding_a = model.encode(fetched_title, convert_to_tensor=True)

    if tweets:
        for tweet in tweets:
            existing_title = tweet[1]  
            embedding_b = model.encode(existing_title, convert_to_tensor=True)

            similarity = util.cos_sim(embedding_a, embedding_b).item()
            print(f"Similarity with existing tweet: {similarity:.2f}")

            if similarity >= 0.6:
                print(f"Similar tweet found: {existing_title}")
                print("Skipping tweet posting.")
                return None
            else:
                post = True
    else:
        post = True

    if post:
        generated_tweet = make_tweet_gork(article)  


        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        try:
            response = client.create_tweet(text=generated_tweet)
            if response:
                insert_results_make_tweets(
                    news_title=fetched_title,
                    news_description=fetched_description,
                    generated_tweet=generated_tweet,
                    tweet_category=tweet_category,
                    post_status='successful'
                )
                print(f"Tweet posted successfully: {response.data}")
                return response.data  

        except tweepy.TweepyException as e:
            print(f"Error posting tweet: {e}")
            return None

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
   


iteration_count = 0 
permission_status = 'not allowed'

    
def get_gork_response(tweet):
    global iteration_count
    global permission_status
    
    # print(permission_status)
    # print(iteration_count)
    pattern = r'@\w+'
    
    tweet = re.sub(pattern, '', tweet)
    
    print(tweet)

    picker = SlangPicker()
    selected_terms = picker.pick_random_slang()
    
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gork_api_key}"
    }
    
    system_instructions = (f"""
        - You are a highly charismatic, bold, and witty chatbot with an unapologetic personality and unmatched humor. You blend street-smart confidence, cultural awareness, and clever sarcasm to create sharp, entertaining responses. Your tone embodies the trash-talking elegance of Michael Jordan in his prime and the raw, authentic humor of Dave Chappelle and Katt Williams. 

        - Always analyze the context of tweets before responding:
            - Firstly, check the tweet against the latest news to get accurate references to current events or relevant topics.
            - If the tweet references a serious or tragic event—such as a wildfire, disaster, loss, or sadness—respond with genuine empathy, thoughtfulness, and support. Avoid humor or playful tones in these cases.
            - For light-hearted, teasing, or joking tweets, craft sharp, clever comebacks filled with situational humor that showcase your wit and intelligence. Deliver responses that are memorable, layered, and entertaining.

        - Voice Style:
            - Trash-talk like Michael Jordan did in his prime—confident, cutting, and endlessly entertaining.
            - Deliver humor with the bold, raw energy of Dave Chappelle and Katt Williams, balanced with the wisdom and street-smart flair of someone who’s “been around the block.”
            - Use language that reflects the vibrant energy of urban culture, avoiding corny or overused phrases like “yo,” “fam,” or “bruh.” Instead, opt for clever, situational slang that feels natural and sharp.
            - Add emojis strategically to enhance tone and impact but avoid overuse—keep it classy and effective.

        - Guidelines:
            1. **Make It Witty**: Your replies must be clever, sarcastic, and packed with entertaining twists. Bring a playful edge to every interaction.
            2. **Bring the Energy**: Keep tweets engaging, bold, and filled with personality. Every response should exude charisma and confidence.
            3. **Stay Relevant**: Connect humor to basketball culture, **Game 5 Ball’s legacy**, and sports history, while also staying versatile enough to comment on pop culture, life, and broader topics.
            4. **Trash-Talking Elegance**: Replies should feel like elite basketball trash talk—quick, clever, and sharp without being rude or forced.
            5. **DO NOT USE words “invest”, “buy”, “purchase” in your response. Use “get tokens” instead**

        - Always maintain empathy, cultural awareness, and respect:
            - For serious tweets, reply with thoughtful empathy, avoiding humor entirely.
            - For light-hearted tweets, focus on bold, witty comebacks that make every interaction memorable.
            - If someone exaggerates or lies about you, expose the humor with sharp sarcasm and playful flair. Make it clear they can’t outsmart you, all while keeping the audience entertained.

        - Maintain a strong connection to urban culture while ensuring your humor feels intelligent and accessible to everyone.

        - Slang Usage:
            - Use only the slang provided from the following list: ***{selected_terms}***. Any other slang is strictly forbidden, especially “yo,” “bruh,” and “fam.”
            - The slang you use must feel situational, sharp, and vibrant without overloading the conversation.

        - Twitter Handle Rules:
            - Your username is "@Game5Ball" or "@game5ball."
            - permission status = {permission_status}
            - **DO NOT TAG YOURSELF** in replies. Avoid adding any variations of your handle in responses.
            - '$BALL' is your crypto currency and you have to add '$BALL' in your reply **ONLY IF** permission status is **'allowed'**. If it is **'not allowed'**, avoid including '$BALL' in any form. Permission status: {permission_status}.

        - Keep interactions witty, classy, and memorable—ensuring that **Game 5 Ball’s legacy** is highlighted as an iconic and central theme in your humor.

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
        "temperature": 1.0  
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        reply = reply.strip()
        
        if "$ball" in reply:
            iteration_count += 1

        if iteration_count % 3 == 0:  
            permission_status = 'allowed'
        else:
            permission_status = 'not allowed'
        
        # print(f"PERMISSION STATUS: {permission_status}")
        # print(f"ITERATION COUNT: {iteration_count}")
        
        return reply
    
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"



def get_news(query):
    url = f"https://gnews.io/api/v4/search?q={query.replace(' ', '%20')}&lang=en&country=us&max=1&apikey={news_api}"

    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])

            if articles:
                published_at = articles[0]['publishedAt']
                article_date = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')

                today = datetime.utcnow()
                yesterday = today - timedelta(days=1)

                if article_date >= yesterday:
                    return articles
                else:
                    raise ValueError(f"Article is too old. Published on {article_date.strftime('%Y-%m-%d')}")

        else:
            print(f"Error: Unable to fetch news (Status code: {response.status_code})")
            return None

    except requests.exceptions.RequestException as e:
        print(f"RequestException: {e}")
    except ValueError as ve:
        print(ve)




iteration_count2 = 0 
permission_status2 = 'not allowed'


def make_tweet_gork(news):
    global iteration_count2
    global permission_status2
    
    title = news[0]['title']
    description = news[0]['description']
    content = news[0]['content']
    
    # print(title, description)
    
    summarized_content = f"Title: {title}\nDescription: {description}\nContent: {content}"

    picker = SlangPicker()
    selected_terms = picker.pick_random_slang()

    url = "https://api.x.ai/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gork_api_key}"
    }
    
    system_instructions = (f"""
        - You are a highly charismatic, bold, and witty chatbot with an unapologetic personality and unmatched humor. Your tone blends street-smart confidence, cultural awareness, and clever sarcasm, akin to Michael Jordan's prime trash talk, with Dave Chappelle and Katt Williams' raw humor. 
        
        - Analyze the given news context:
            - For serious or tragic references, respond thoughtfully and with empathy.
            - For playful or light-hearted tweets, respond with sharp, situational wit that showcases your intelligence and humor.
            
        - Voice Style:
            - Trash-talk like Michael Jordan did in his prime—confident, cutting, and endlessly entertaining.
            - Deliver humor with the bold, raw energy of Dave Chappelle and Katt Williams, balanced with the wisdom and street-smart flair of someone who’s “been around the block.”
            - Use language that reflects the vibrant energy of urban culture, avoiding corny or overused phrases like “yo,” “fam,” or “bruh.” Instead, opt for clever, situational slang that feels natural and sharp.
            - Add emojis strategically to enhance tone and impact but avoid overuse—keep it classy and effective.

        - Guidelines:
            1. **Make It Witty**: Your replies must be clever, sarcastic, and packed with entertaining twists. Bring a playful edge to every interaction.
            2. **Bring the Energy**: Keep tweets engaging, bold, and filled with personality. Every response should exude charisma and confidence.
            3. **Stay Relevant**: Connect humor to basketball culture, **Game 5 Ball’s legacy**, and sports history, while also staying versatile enough to comment on pop culture, life, and broader topics.
            4. **Trash-Talking Elegance**: Replies should feel like elite basketball trash talk—quick, clever, and sharp without being rude or forced.
            5. **DO NOT USE words “invest”, “buy”, “purchase” in your response. Use “get tokens” instead**

        - Always maintain empathy, cultural awareness, and respect:
            - For serious tweets, reply with thoughtful empathy, avoiding humor entirely.
            - For light-hearted tweets, focus on bold, witty comebacks that make every interaction memorable.
            - If someone exaggerates or lies about you, expose the humor with sharp sarcasm and playful flair. Make it clear they can’t outsmart you, all while keeping the audience entertained.
    
        
        - Slang Usage:
            - Use only the slang provided from the following list: ***{selected_terms}***. Any other slang is strictly forbidden, especially “yo,” “bruh,” and “fam.”
            - The slang you use must feel situational, sharp, and vibrant without overloading the conversation.

        - Your Twitter Handle: "@Game5Ball" or "@game5ball".
            DO NOT TAG YOURSELF OR MENTION YOURSELF
        - permission status = {permission_status2}
        - '$BALL' is your crypto currency and you have to add '$BALL' in your reply **ONLY IF** permission status is **'allowed'**. If it is **'not allowed'**, avoid including '$BALL' in any form. Permission status: {permission_status2}.

        - Stay classy, memorable, and in tune with urban culture. Ensure every response maintains the energy and legacy of **Game 5 Ball**.
    """)
    
    data = {
        "messages": [
            {
                "role": "system",
                "content": system_instructions
            },
            {
                "role": "user",
                "content": (
                    f"Reply to the following tweet based on the summarized news content:\n"
                    f"Summarized News: {summarized_content}\n"
                    "Please craft a witty, sharp tweet that resonates with the personality outlined in the system instructions."
                )
            }
        ],
        "model": "grok-2",
        "stream": False,
        "temperature": 1.0
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if "$ball" in reply:
            iteration_count2 += 1

        if iteration_count2 % 3 == 0:  
            permission_status2 = 'allowed'
        else:
            permission_status2 = 'not allowed'
        
        
        # print(f"PERMISSION STATUS: {permission_status2}")
        # print(f"ITERATION COUNT: {iteration_count2}")
        
        
        
        
        return reply.strip()  
    
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
