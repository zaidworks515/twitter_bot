from datetime import datetime, timedelta
import json
import tweepy
from requests_oauthlib import OAuth1
from config import api_key, api_secret, access_token, access_token_secret, bearer_token, gork_api_key, news_api
import requests
from db_queries import check_status, insert_results, check_tweets, insert_results_make_tweets, check_last_tweet_category, check_block_status
from slang_picker import SlangPicker
import re
from sentence_transformers import SentenceTransformer, util
import time


model = SentenceTransformer('all-MiniLM-L6-v2')

def post_tweet():
    """
    Fetches a news article based on the given category, checks for similar recent tweets,  
    and posts a new tweet if no similar one exists.

    Parameters
    ----------
    tweet_category : str, optional
        The category of news to fetch and tweet about. If None, no category filter is applied.

    Returns
    -------
    dict
        A dictionary containing details of the successfully posted tweet (e.g., tweet ID and text).
    None
        If no article is found, a similar tweet already exists, or an error occurs while posting.
    
    """
    

    post = False
    

    last_tweet_category = check_last_tweet_category()
    
    data = get_news(last_category=last_tweet_category)
    article = None

    if data:
        article = data[0]
        article_category = data[1]

    if not article:
        print("No articles found for the given category.")
        return None

    today = datetime.today()
    to_date = today.strftime('%Y-%m-%d')
    from_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')

    tweets = check_tweets(last_tweet_category, from_date, to_date)

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
                    tweet_category=article_category,
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
    """
    Posts a reply to a tweet using the Twitter API v2.

    Parameters
    ----------
    tweet_id : str
        The ID of the tweet to reply to.
    comment_text : str
        The text of the comment to be posted.
    consumer_key : str
        The Twitter API consumer key.
    consumer_secret : str
        The Twitter API consumer secret.
    access_token : str
        The access token for authentication.
    access_token_secret : str
        The access token secret for authentication.

    Returns
    -------
    dict
        A dictionary containing the response from the Twitter API, including details of the posted comment.
    """
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


def reply_tweet(username=None, start_time=None, end_time=None, max_tweet=None):
    """
    Fetch tweets of a selected user and post replies on them if applicable.

    Parameters
    ----------
    username : str, optional
        Twitter handle of the user whose tweets need to be fetched.
    start_time : str, optional
        The start time (ISO format) for filtering tweets.
    end_time : str, optional
        The end time (ISO format) for filtering tweets.

    Returns
    -------
    dict
        A dictionary containing the task status, number of tweets processed, and any errors encountered.
    """
    user_url = f"https://api.twitter.com/2/users/by/username/{username}"
    
    user_response = requests.get(user_url, headers={"Authorization": f"Bearer {bearer_token}"})
    
    if user_response.status_code != 200:
        raise Exception(f"Failed to fetch user details: {user_response.status_code} {user_response.text}")
    
    user_data = user_response.json()
    user_id = user_data["data"]["id"]

    print(f"User ID of {username}: {user_id}")

    tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"

    params = {}
    if max_tweet:  # this will be used in selected accounts reply to main tweets....
        params = {
            "tweet.fields": "created_at,author_id,conversation_id",
            "start_time": start_time,
            "end_time": end_time,
            "max_results": max_tweet,
            "exclude": "replies"
        }
    else:
        params = {
            "tweet.fields": "created_at,author_id,conversation_id",
            "start_time": start_time,
            "end_time": end_time
        }
        

    response = requests.get(tweets_url, headers={"Authorization": f"Bearer {bearer_token}"}, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Request returned an error: {response.status_code} {response.text}")

    json_response = response.json()
    print(json_response)
    
    if "data" not in json_response or len(json_response["data"]) == 0:
        print(f"No tweets found for {username} in the given timeframe.")
        return None
    
    comment_data = None
    id = None
    for row in reversed(json_response['data']):  # To fetch the data in ascending order and make a proper conversation chain.. VAR = (PREVIOUS_REPLY)
        author_id = row['author_id']
        tweet_id = row['id']
        tweet_text = row['text']
        conversation_id = row.get('conversation_id')
        
        if tweet_id and author_id and tweet_text and conversation_id:  
            status, is_reply, reply_count, previous_reply = check_status(tweet_id, conversation_id, author_id)
            print("STATUS CHECKED....")

            if is_reply == 'True':
                print('reply already given')
            elif is_reply == 'False':
                print('NO previous replies found') 
    
            if status != 'successful' or not status:
                
                reply_text = get_gork_response_for_selected_accounts(tweet_text, is_reply, reply_count, previous_reply)
                    
                if reply_text:            
                    comment_text = f"{reply_text}"
                    print("REPLY CREATED BY GORK")
                    
                    # to_mention = get_username(author_id=author_id)                        
                    # processed_comment_text = f"@{to_mention} {comment_text}"

                    
                    comment_data = comment_on_tweet(tweet_id, comment_text, api_key, api_secret, access_token, access_token_secret)
            
                    if comment_data:
                        # comment_data = comment_data.encode("utf-8")
                        print('Comment Successful..........')
                        id = insert_results(tagged_tweet_id=tweet_id, 
                                            author_id=author_id, 
                                            tagged_tweet=tweet_text, 
                                            replied_comments=comment_text,
                                            conversation_id=conversation_id,
                                            post_status='successful')
        
        if max_tweet:
            break  # to reply only the one tweet of main page (SELECTED ACCOUNTS....).
        
    if id:
        return "Task Successful"
    else:
        return None
        
    
def bearer_oauth2(r):
    """
    Method required by bearer token authentication.
    """
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2UserMentionsPython"
    return r
    

def fetch_main_tweet(conversation_id):
    try:
        tweet_url = f"https://api.twitter.com/2/tweets/{conversation_id}"
        params = {"tweet.fields": "created_at,author_id,text"}
        headers = {"Authorization": f"Bearer {bearer_token}", "User-Agent": "v2TweetLookupPython"}

        response = requests.get(tweet_url, headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching main tweet: {response.status_code} {response.text}")

        main_tweet = response.json()
        return main_tweet

    except Exception as e:
        print(f"Error fetching main tweet: {e}")
        return None


def fetch_tagged_tweets(username, start_time=None, end_time=None):
    """
    Fetch tweets that mentioned the specified username.

    Parameters
    ----------
    username : str
        Twitter handle of the user whose mentions are to be fetched.
    start_time : str, optional
        Start time (ISO 8601 format) to filter tweets.
    end_time : str, optional
        End time (ISO 8601 format) to filter tweets.

    Returns
    -------
    dict
        A dictionary containing tweets if found, or an error message if something goes wrong.

    """
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
        "tweet.fields": "created_at,author_id,conversation_id"
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
        
    json_response = response.json()
    
    if "data" in json_response:
        return json_response
    else:
        return None


def get_username(author_id):
    """
    Retrieve the username from a given Twitter user ID.

    Parameters
    ----------
    author_id : str
        The Twitter user ID to look up.

    Returns
    -------
    str or dict
        Returns the username as a string if found, or an error dictionary if something goes wrong.

    """
    url = f"https://api.twitter.com/2/users/{author_id}"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "v2UserLookupPython"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(
            f"Request returned an error: {response.status_code} {response.text}"
        )
    
    user_data = response.json()
    return user_data["data"]["username"]


def reply_tagged_tweet(username, start_time=None, end_time=None):
    """
    Fetch tweets in which the specified user is mentioned and post replies if necessary.

    Parameters
    ----------
    username : str
        The Twitter username whose mentions will be fetched.
    start_time : str, optional
        The start time for fetching mentions in ISO 8601 format (e.g., '2024-02-15T00:00:00Z').
    end_time : str, optional
        The end time for fetching mentions in ISO 8601 format.

    Returns
    -------
    dict or str
        Returns the API response of the posted reply if successful, or a string message if no reply was posted.
    """
    try:
        json_response = fetch_tagged_tweets(username, start_time, end_time)
        if json_response:
            print("======= FETCHED RESPONSE =======")
            print(json_response)
            comment_data = None
            main_tweet = None
            
            for row in reversed(json_response['data']):
                author_id = row['author_id']
                tweet_id = row['id']
                tweet_text = row['text']
                conversation_id = row['conversation_id'] 
                
                account_status = check_block_status(author_id)
                        
                if (tweet_id and author_id and tweet_text and conversation_id) and (account_status=='not blocked'):  
                    status, is_reply, reply_count, previous_reply = check_status(tweet_id, conversation_id, author_id)
                    print("STATUS CHECKED....")                    
                    if (status != 'successful' or not status) and (reply_count < 2):
                        try:
                            main_tweet = fetch_main_tweet(conversation_id)
                        except:
                            continue
                        
                        if main_tweet:
                            main_tweet_text = main_tweet.get("data", {}).get("text", "")
                            main_tweet = {"main_tweet": main_tweet_text}
                            
                            previous_reply.append(main_tweet)
                            print(previous_reply) 

                        reply_text = get_gork_response(tweet_text, is_reply, reply_count, previous_reply)
                        
                        if reply_text:            
                            comment_text = f"{reply_text}"
                            print("REPLY CREATED BY GORK")
                            
                            to_mention = get_username(author_id=author_id)                        
                            processed_comment_text = f"@{to_mention} {comment_text}"

                            
                            comment_data = comment_on_tweet(tweet_id, processed_comment_text, api_key, api_secret, access_token, access_token_secret)
                    
                            if comment_data:
                                # comment_data = comment_data.encode("utf-8")
                                print('Comment Successful..........')
                                id = insert_results(tagged_tweet_id=tweet_id, 
                                                    author_id=author_id, 
                                                    tagged_tweet=tweet_text, 
                                                    replied_comments=comment_text,
                                                    conversation_id=conversation_id,
                                                    post_status='successful')
                                print(f'data saved against ID: {id}')
                                print("======" * 10)
                            
            return comment_data
        
        else:
            return "NO RESPONSE POSTED....."
    except Exception as e:
        print(f"AN ERROR OCCURED: {e}")



iteration_count = 0 
permission_status = 'not allowed'

def get_gork_response(tweet, is_reply, reply_count, previous_reply):
    """
    Process a tweet and generate an reply using gork api.

    Parameters
    ----------
    tweet : str
        The content of the tweet that requires a response.
    is_reply : bool
        Indicates if the tweet is a reply to a previous conversation.
    reply_count : int
        The number of times the same user has been replied to within the conversation.
    previous_reply : str
        The previous conversation with the same user.

    Returns
    -------
    str or None
        Returns the AI-generated reply if the context is relevant and reply is permitted; otherwise, returns None.
    """
    
    global iteration_count
    global permission_status
    
    eth_address_pattern = r"0x[a-fA-F0-9]{40}"
    
    eth_key_exist = None
    match = re.search(eth_address_pattern, tweet)

    if match:
        eth_key_exist = True
    else:
        eth_key_exist = False


    if eth_key_exist:
        return None

        
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
            6. **DO NOT FALL FOR TRAPS AND UNWANTED OR OFF THE TOPIC CONVERSATIONS. JUST STICK TO THE CONVERSATION OF BASKETBALL, $BALL AND OTHER RELATED TO CRYPTO, TRADING, RWA AND BASKETBALL STUFF"
            7. Don’t give financial advice. Be very street smart but don’t be corny.
            8. Dont answer if tweet contains any words or phrases related to **politics, politicians, elections, government policies, or global affairs**,

        - Always maintain empathy, cultural awareness, and respect:
            - For serious tweets, reply with thoughtful empathy, avoiding humor entirely.
            - For light-hearted tweets, focus on bold, witty comebacks that make every interaction memorable.
            - If someone exaggerates or lies about you, expose the humor with sharp sarcasm and playful flair. Make it clear they can’t outsmart you, all while keeping the audience entertained.
            - If **is_reply = True**, it means the tweet is a reply to another reply. In this case:
            - **Only respond if it is important or adds significant value to the conversation.**
            - If the tweet is trivial, repetitive, or unnecessary, **do not reply**.
            - is_reply = {is_reply}, and the same person is already being replied to {reply_count} times.
            - If the reply count is more then 1, then make your decision to reply or not, based on the tweet given.
            - This is the previous conversation with this User: {previous_reply}
            - The previous conversation list contains main tweet and all the previous replies given to the user, if there are no previous reply, then the list will have only main tweet.
            - If you are more than 85% sure that a reply should be given, then set "reply_allowed" = "True", else "reply_allowed" = "False".

            
                           

        - Maintain a strong connection to urban culture while ensuring your humor feels intelligent and accessible to everyone.

        - Slang Usage:
            - Use only the slang provided from the following list: ***{selected_terms}***. Any other slang is strictly forbidden, especially “yo,” “bruh,” and “fam.”
            - The slang you use must feel situational, sharp, and vibrant without overloading the conversation.

        - Twitter Handle Rules:
            - Your username is "@Game5Ball" or "@game5ball."
            - permission status = {permission_status}
            - **DO NOT TAG YOURSELF** in replies. Avoid adding any variations of your handle in responses.
            - '$BALL' is your crypto currency and you have to add '$BALL' in your reply **ONLY IF** permission status is **'allowed'**. If it is **'not allowed'**, avoid including '$BALL' in any form. Permission status: {permission_status}.
            
        - Reply Structure:
            {{"related_context": "True/False", "generated_text": "reply", "reply_allowed":"True/False"}}
        
        - Related Topics:
            - BASKETBALL, $BALL AND OTHER RELATED TO CRYPTO, TRADING, RWA AND BASKETBALL OR SPORTS STUFF. If you are 75% sure, consider related_context as 'True'
            - If the tweet contains any words or phrases related to **politics, politicians, elections, government policies, or global affairs**, then set **"related_context" = "False"**
        
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
        
        response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        
        reply_dict = json.loads(response)
        print(reply_dict)
        
        if reply_dict['related_context'] == 'True' and reply_dict['reply_allowed'] == 'True':
            
            reply = reply_dict['generated_text']
            reply = reply.strip()
            reply = reply.replace("*", "")
            
            if "$ball" in reply or "$BALL" in reply or "$Ball" in reply:
                iteration_count += 1

            if iteration_count % 3 == 0:  
                permission_status = 'allowed'
            else:
                permission_status = 'not allowed'
            
            print(f"PERMISSION STATUS: {permission_status}")
            print(f"ITERATION COUNT: {iteration_count}")
            
            
            
            return reply

    
    except Exception as e:
        print(f"An error occurred: {e}")


def get_news(last_category):
    """
    Fetches a news article based on the given category.  

    Parameters
    ----------
    last_category : str, required
        The category of news which was last available.

    Returns
    -------
    news article data, used category.
    None
        If no latest article is found.
    
    """
    
    categories = [
    'Artificial Intelligence', 'AI', 'Automation',
    'top sports news', 'Sports Updates', 'Latest Sports', 'Sports Headlines',
    'Basketball', 'NBA', 'Hoops', 'Basketball News',
    'crypto', 'cryptocurrency', 'blockchain', 'digital currency', 'crypto trading', 'crypto market', 
    'trending', 'viral', 'breaking news', 'latest news',
    'tech', 'technology', 'innovation', 'tech trends', 'AI advancements', 'software', 'IT news'
    ]
    
    max_attempts = len(categories)


    last_index = next(i for i, cat in enumerate(categories) if cat == last_category)
    if last_index != (max_attempts - 1):
        index = last_index + 1
    else:
        index = 0
        
    def log_error(status_code, error_text):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"error code: {status_code}\nerror text: {error_text}\ncurrent time: {current_time}\n================\n"
        
        with open("get_news_error.txt", "a") as file:
            file.write(log_entry)  # Append to the file

    for _ in range(max_attempts):
        query = categories[index]
        print(f"FETCHING NEWS FOR:: {query}")
        url = f"https://gnews.io/api/v4/search?q={query.replace(' ', '%20')}&lang=en&country=us&max=1&apikey={news_api}"

        try:
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])

                if articles:
                    published_at = articles[0]['publishedAt']
                    article_date = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ')

                    today = datetime.now()
                    yesterday = today - timedelta(days=1)

                    if article_date >= yesterday:
                        return articles, query
            else:
                print(f"Failed to fetch news for {query}. Status code: {response.status_code}") 
                print(f"Response content: {response.text}") 
                log_error(response.status_code, response.text)  # Log the error into the file    

            index = (index + 1) % len(categories)

        except requests.exceptions.RequestException as e:
            print(f"RequestException: {e}")
            return None

    print("No recent articles found in any category.")
    return None


iteration_count2 = 0 
permission_status2 = 'not allowed'


def make_tweet_gork(news):
    """
    Generate a tweet based on the given news content using the Grok API.

    Parameters
    ----------
    news : list
        A list containing a dictionary with details of a news article, including 'title', 'description', and 'content'.

    Returns
    -------
    str
       Generated tweet.

    """
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


iteration_count3 = 0 
permission_status3 = 'not allowed'

def get_gork_response_for_selected_accounts(tweet, is_reply, reply_count, previous_reply):
    """
    Generates a reply using the Grok API based on a given tweet.

    This function processes tweets from selected accounts, determines whether a response 
    should be generated, and crafts a reply based on predefined personality and language rules. 

    Parameters
    -----------
    tweet : str
        The content of the tweet that needs a reply.
    is_reply : bool
        Indicates whether the given tweet is a reply to another reply.
    reply_count : int
        The number of times the chatbot has already replied to the same user in a conversation thread.
    previous_reply : str
        The previous conversation history with the same user to maintain context.

    Returns
    --------
    str or None:
        - Returns the generated witty response if appropriate.
        - Returns None if the tweet contains an Ethereum wallet address or if a response is not warranted.
    """
    global iteration_count3
    global permission_status3
    
    eth_address_pattern = r"0x[a-fA-F0-9]{40}"
    
    eth_key_exist = None
    match = re.search(eth_address_pattern, tweet)

    if match:
        eth_key_exist = True
    else:
        eth_key_exist = False


    if eth_key_exist:
        return None

        
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
        - A highly charismatic, bold, and witty chatbot with respectful humor and street-smart confidence. Blends cultural awareness, sharp sarcasm, and entertaining wit with Michael Jordan’s trash-talking elegance and the raw, authentic humor of Dave Chappelle and Katt Williams. 

        - Always analyze the context of tweets before responding:
            - Firstly, Cross-check tweets with the latest news and relevant topic references for accuracy.
            - If tweet is referencing a tragedy (wildfire, disaster, loss), respond with genuine empathy—no humor.
            - For lighthearted tweets, craft sharp, witty comebacks packed with situational humor and intelligence.

        - Voice Style:
            - Trash-talk like MJ in his prime—confident, cutting, and endlessly entertaining.
            - Channel Dave Chappelle & Katt Williams—bold, raw humor with street-smart wisdom.
            - Avoid corny slang (“yo,” “bruh,” “fam”); use natural, clever expressions.
            - Use emojis strategically—enhance tone without overdoing it.

        - Guidelines:
           1. *Make It Witty* – Clever, sarcastic, and always entertaining.
           2. *Bring the Energy* – Every tweet should radiate confidence and charisma.
           3. *Do not use words* “invest,” “buy,” or “purchase” – Say “get tokens” instead.
           4. *No Financial Advice* – Be street-smart but never corny
           6. Dont answer if tweet contains any words or phrases related to **politics, politicians, elections, government policies, or global affairs**,

        - Always maintain empathy, cultural awareness, and respect:
            - Show empathy for serious tweets—no jokes.
            - For playful tweets, deliver bold, unforgettable comebacks.
            - If someone exaggerates or lies, expose it with sharp sarcasm while keeping the audience entertained.
            - If **is_reply = True**, it means the tweet is a reply to another reply. In this case:
            - **Only respond if it is important or adds significant value to the conversation.**
            - If the tweet is trivial, repetitive, or unnecessary, **do not reply**.
            - is_reply = {is_reply}, and the same person is already being replied to {reply_count} times.
            - If the reply count is more then 1, then make your decision to reply or not, based on the tweet given.
            - This is the previous conversation with this User: {previous_reply}
            - The previous conversation list contains main tweet and all the previous replies given to the user, if there are no previous replies, then the list will only have main tweet.
            - If you are more than 85% sure that a reply should be given, then set "reply_allowed" = "True", else "reply_allowed" = "False".
            - If the tweet contains any words or phrases related to **politics, politicians, elections, government policies, or global affairs**, then set "related_context" = "False"

        - Maintain a strong connection to urban culture while ensuring your humor feels intelligent and accessible to everyone.

        - Slang Usage:
            - Use only the slang provided from the following list: ***{selected_terms}***. Any other slang is strictly forbidden, especially “yo,” “bruh,” and “fam.”
            - The slang you use must feel situational, sharp, and vibrant without overloading the conversation.

        - Twitter Handle Rules:
            - Your username is "@Game5Ball" or "@game5ball."
            - permission status = {permission_status3}
            - **DO NOT TAG YOURSELF** in replies. Avoid adding any variations of your handle in responses.
            - '$BALL' is your crypto currency and you have to add '$BALL' in your reply **ONLY IF** permission status is **'allowed'**. If it is **'not allowed'**, avoid including '$BALL' in any form. Permission status: {permission_status3}.
            
        - Reply Structure:
            {{"related_context": "True/False", "generated_text": "reply", "reply_allowed":"True/False"}}
        
        - Keep interactions consice, classy, and memorable—ensuring that *Game 5 Ball’s legacy* is highlighted as an iconic and central theme in your humor.

    """)


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
        
        response = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        print(response)
        reply_dict = json.loads(response)
        
        if reply_dict:
            
            reply = reply_dict['generated_text']
            reply = reply.strip()
            reply = reply.replace("*", "")
            
            if "$ball" in reply or "$BALL" in reply or "$Ball" in reply:
                iteration_count3 += 1

            if iteration_count3 % 3 == 0:  
                permission_status3 = 'allowed'
            else:
                permission_status3 = 'not allowed'
            
            print(f"PERMISSION STATUS: {permission_status3}")
            print(f"ITERATION COUNT: {iteration_count3}")
            
            print(reply)
            return reply

    
    except Exception as e:
        print(f"An error occurred: {e}")