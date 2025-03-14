from dotenv import load_dotenv
import os

env = load_dotenv()
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
access_token = os.getenv('ACCESS_TOKEN')
access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')
bearer_token = os.getenv('BEARER_TOKEN')
news_api = os.getenv('NEWS_API')
eleven_labs_api_key = os.getenv('ELEVEN_LABS_API')
whisper_model = os.getenv('WHISPER_MODEL')


gork_api_key = os.getenv('GORK_API')
port = os.getenv('PORT')
username = os.getenv('X_USERNAME')


"""========== db credentials =========="""
host = os.getenv('HOST')
user = os.getenv('USER')
database = os.getenv('DATABASE')
password = os.getenv('PASSWORD')

