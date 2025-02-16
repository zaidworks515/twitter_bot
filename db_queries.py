import mysql.connector
from mysql.connector import Error
from config import host, user, password, database


def create_connection():
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        # if connection.is_connected():
        #     print("Connected to MySQL database")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None
    
    
def insert_results(tagged_tweet_id=None, author_id=' ', tagged_tweet=None, replied_comments=None, post_status=None, conversation_id=None):   
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:    
            insert_query = """INSERT INTO tweet_record (tagged_tweet_id, author_id, tagged_tweet, replied_comments, post_status, conversation_id) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, (tagged_tweet_id, author_id, tagged_tweet, replied_comments, post_status, conversation_id))
            connection.commit()
            return cursor.lastrowid or 'can not save posted a tweet.' # Yeh created id return krega
        except Error as e:
            connection.rollback()
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"

    
def check_status(tagged_tweet_id, conversation_id, author_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT * FROM tweet_record WHERE tagged_tweet_id = %s", (tagged_tweet_id,))

            results = cursor.fetchall()
            cursor.execute("SELECT COUNT(*) FROM tweet_record WHERE conversation_id = %s AND author_id = %s", (conversation_id, author_id,))

            reply_result = cursor.fetchone()

            reply_count = reply_result[0]
            

            is_reply = "True" if reply_result[0] > 0 else "False"
            

            conversation_chain = []
            if is_reply == "True":
                cursor.execute("SELECT author_id, tagged_tweet, replied_comments FROM tweet_record WHERE conversation_id = %s AND author_id = %s ORDER BY id ASC", (conversation_id, author_id))
                all_replies = cursor.fetchall()
                
                for reply in all_replies:
                    conversation_chain.append({"User": reply[1], "AI_Response": reply[2]})

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


def check_tweets(tweet_category, from_date, to_date):

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = """
                SELECT * FROM make_tweets
                WHERE tweet_category = %s AND DATE(created_at) BETWEEN %s AND %s
            """
            cursor.execute(query, (tweet_category, from_date, to_date))
            
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

 
def insert_results_make_tweets(news_title=None, news_description=' ', generated_tweet=None, tweet_category=None, post_status=None):   
    connection = create_connection()
    if connection:
        print('connection established')
        cursor = connection.cursor()
        try:    
            insert_query = """INSERT INTO make_tweets (news_title, news_description, generated_tweet, tweet_category, post_status) 
            VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, (news_title, news_description, generated_tweet , tweet_category, post_status))
            connection.commit()
            print('data inserted in db')
            return cursor.lastrowid or 'can not posted a tweet.' # Yeh created id return krega
        except Error as e:
            connection.rollback()
            return f"An error occurred: {e}"
        finally:
            cursor.close()
            connection.close()
    else:
        return "Unable to connect to the database"

