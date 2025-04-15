import mysql.connector
from mysql.connector import Error
from config import host, user, password, database


def create_connection():
    """
    create connection to the database
    """
    try:
        connection = mysql.connector.connect(
            host=host, user=user, password=password, database=database
        )
        # if connection.is_connected():
        #     print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None


def check_block_status(author_id):

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM accounts WHERE author_id = %s", (author_id,))

            results = cursor.fetchone()
            if results:
                status = results[-1]

                return status
            else:
                return "not blocked"
        except Error as e:
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"


def insert_results(
    tagged_tweet_id=None,
    author_id=" ",
    tagged_tweet=None,
    replied_comments=None,
    post_status=None,
    conversation_id=None,
):
    """
    inserts tweets and replies into database against their tweet ids.

    Parameters
    ----------
    tagged_tweet_id : None
    author_id : string
    tagged_tweet : None
    replied_comments : None
    post_status : None
    conversation_id : None

    """
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            insert_query = """INSERT INTO tweet_record (tagged_tweet_id, author_id, tagged_tweet, replied_comments, post_status, conversation_id) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(
                insert_query,
                (
                    tagged_tweet_id,
                    author_id,
                    tagged_tweet,
                    replied_comments,
                    post_status,
                    conversation_id,
                ),
            )
            connection.commit()
            return (
                cursor.lastrowid or "can not save posted a tweet."
            )  # Yeh created id return krega
        except Error as e:
            connection.rollback()
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"


def check_status(tagged_tweet_id, conversation_id, author_id):
    """
    check status of the tweets

    Parameters
    ----------
    tagged_tweet_id : Any
    author_id : Any
    conversation_id : Any

    Returns
    ----------
    post_status
        None, pending or successful
    is_reply
        "True" or "False" (whether the tweet is a reply to another tweet)
    reply_count
        int (how many times we have already replied to the same person within the same conversation),
    conversation_chain
        [{"User": "", "AI_Response": ""}] (all the previous conversation with author)
    """
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT * FROM tweet_record WHERE tagged_tweet_id = %s",
                (tagged_tweet_id,),
            )

            results = cursor.fetchall()
            cursor.execute(
                "SELECT COUNT(*) FROM tweet_record WHERE conversation_id = %s AND author_id = %s",
                (
                    conversation_id,
                    author_id,
                ),
            )

            reply_result = cursor.fetchone()

            reply_count = reply_result[0]

            is_reply = "True" if reply_result[0] > 0 else "False"

            conversation_chain = []
            if is_reply == "True":
                cursor.execute(
                    "SELECT author_id, tagged_tweet, replied_comments FROM tweet_record WHERE conversation_id = %s AND author_id = %s ORDER BY id ASC",
                    (conversation_id, author_id),
                )
                all_replies = cursor.fetchall()

                for reply in all_replies:
                    conversation_chain.append(
                        {"User": reply[1], "AI_Response": reply[2]}
                    )

                # print(f"CONVERSAION CHAIN: {conversation_chain}")

            if results:
                post_status = results[-1][-2]  # Get the latest post_status
                return post_status, is_reply, reply_count, conversation_chain
            else:
                return None, is_reply, reply_count, conversation_chain

        except Error as e:
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"


def check_tweets(from_date, to_date):
    """
    Fetches tweets of a specified category from the database within a given time frame.

    Parameters
    ----------
    tweet_category : str
        The category of tweets to filter (e.g., "sports", "crypto", "entertainment").
    from_date : str
        The start date for fetching tweets (format: YYYY-MM-DD).
    to_date : str
        The end date for fetching tweets (format: YYYY-MM-DD).
    """
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = """
                SELECT * FROM make_tweets
                WHERE DATE(created_at) BETWEEN %s AND %s
            """
            cursor.execute(query, (from_date, to_date))

            results = cursor.fetchall()

            if results:
                return results
            else:
                return None

        except Exception as e:
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"


def check_last_tweet_category():
    """
    Fetches last tweet category.
    return:
    category name
    """
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = """
                SELECT * FROM make_tweets ORDER BY id DESC LIMIT 1 
            """
            cursor.execute(
                query,
            )

            results = cursor.fetchone()

            if results:
                tweet_category = results[-2]

                if tweet_category:
                    return tweet_category
                else:
                    return "AI"
            else:
                return None

        except Exception as e:
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"



def fetch_last_category_tweets(from_date, to_date, tweet_category):
    """
    Fetches tweets of a specified category from the database within a given time frame.

    Parameters
    ----------
    from_date : str
        The start date for fetching tweets (format: YYYY-MM-DD).
    to_date : str
        The end date for fetching tweets (format: YYYY-MM-DD).
    tweet_category : str
        The category of tweets to filter (e.g., "sports", "crypto", "entertainment").

    Returns
    -------
    list or None
        List of matching tweet records or None if no matches.
    """
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = """
                SELECT news_title, news_description FROM make_tweets
                WHERE DATE(created_at) BETWEEN %s AND %s
                AND tweet_category = %s
            """
            cursor.execute(query, (from_date, to_date, tweet_category))

            results = cursor.fetchall()

            if results:
                return results
            else:
                return None

        except Exception as e:
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"
    


def insert_results_make_tweets(
    news_title=None,
    news_description=" ",
    generated_tweet=None,
    tweet_category=None,
    post_status=None,
):
    """
    inserts results into make_tweets table

    parameters
    ----------
    news_title : None,
    news_description : ' ',
    generated_tweet : None,
    tweet_category : None,
    post_status : None

    returns
    ---------
    tweet_id : int
    """
    connection = create_connection()
    if connection:
        print("connection established")
        cursor = connection.cursor()
        try:
            insert_query = """INSERT INTO make_tweets (news_title, news_description, generated_tweet, tweet_category, last_news_category, post_status) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(
                insert_query,
                (
                    news_title,
                    news_description,
                    generated_tweet,
                    tweet_category,
                    tweet_category, # last_news_category is same as tweet_category because it is initially the same, it only changes if news is found but a similar tweet is already posted
                    post_status,
                ),
            )
            connection.commit()
            print("data inserted in db")
            return (
                cursor.lastrowid or "can not posted a tweet."
            )  # Yeh created id return krega
        except Error as e:
            connection.rollback()
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"



def update_last_news_category(new_last_category):
    """
    Updates the last_news_category for the latest inserted tweet

    parameters
    ----------
    new_last_category : str
        The new value for the last_news_category column

    returns
    -------
    str : success or error message
    """
    connection = create_connection()
    if connection:
        print("connection established")
        cursor = connection.cursor()
        try:
            update_query = """
                UPDATE make_tweets
                SET last_news_category = %s
                WHERE id = (SELECT MAX(id) FROM make_tweets)
            """
            cursor.execute(update_query, (new_last_category,))
            connection.commit()
            print("last_news_category updated for the latest entry")
            return "Update successful"
        except Error as e:
            connection.rollback()
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"

