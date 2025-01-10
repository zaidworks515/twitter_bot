from dotenv import load_dotenv
import os

env = load_dotenv()
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
access_token = os.getenv('ACCESS_TOKEN')
access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')
bearer_token = os.getenv('BEARER_TOKEN')
client_id = os.getenv('CLIENT_ID')
client_secret_id = os.getenv('CLIENT_SECRET')
port = os.getenv('PORT')


"""========== db credentials =========="""
host = os.getenv('HOST')
user = os.getenv('USER')
database = os.getenv('DATABASE')
password = os.getenv('PASSWORD')

