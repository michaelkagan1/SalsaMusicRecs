"""Flask app configuration"""
from cs50 import SQL
from dotenv import load_dotenv
import authorizeme
import os

#SECRET_KEY, CLIENT_ID, CLIENT_SECRET taken from .env file
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
CLIENT_ID =  os.getenv('CLIENT_ID')
CLIENT_SECRET =  os.getenv('CLIENT_SECRET')

#Taken from CS50 lecture material
SESSION_PERMANENT = False         #treated like a session cookie, deletes session when browser/server quit
SESSION_TYPE = "filesystem"       #contents of session stored in servers files, not in cookie. for privacy

#State and random codes used in OAuth2 authentication
CODE_VERIFIER = authorizeme.randomString(50)
CODE_CHALLENGE = authorizeme.hash(CODE_VERIFIER)
STATE = authorizeme.randomString(16)

#Setup sqlite database
db = SQL("sqlite:///songs.db")

#Set up constants for authorization data -- Adapted from "Spotify API OAuth - Automate Getting User Playlists (Complete Tutorial)" by Imdad Codes youtube video "aka: VIDEO"
REDIRECT_URI = "http://localhost:8000/callback"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"
