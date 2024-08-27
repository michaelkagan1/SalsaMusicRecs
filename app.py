"""
Using PKCE OAuth2 Flow: https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow#request-user-authorization
adapted to python, flask

ISSUES (8/27/24)
	1. If I log in in incognito, doesn't direct me to accept permissions, but rather redirects me to accounts.spotify.com/en/status
	2. Then, if I revisit my localserver, I'm shown permission requests. This should've happened automatically.
	3. Callback route not reached. Seems like spotify either redirects to /login/password, or even to my requested callback, but doesn't even trigger first print statement in said route.
	3. 
"""
import pdb

from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from datetime import datetime
import urllib.parse
import requests
import authorizeme	#my own python file

app = Flask(__name__)
app.secret_key = 'Kjske-6VXxb-9p3vW-oIUt6'

#Taken from CS50 lecture material
app.config["SESSION_PERMANENT"] = False         #treated like a session cookie, deletes session when browser/server quit
app.config["SESSION_TYPE"] = "filesystem"       #contents of session stored in servers files, not in cookie. for privacy
Session(app)

#Set up constants for authorization data -- Adapted from "Spotify API OAuth - Automate Getting User Playlists (Complete Tutorial)" by Imdad Codes youtube video "aka: VIDEO"
#USER_ID = 'mishka94'
CLIENT_ID = '2d5ddacbcfa74e2583a50fac031e5325'
CLIENT_SECRET = 'c50abc283e004e989f1523c2d5aa8dfe'
CODE_VERIFIER = authorizeme.randomString(50)
CODE_CHALLENGE = authorizeme.hash(CODE_VERIFIER)
STATE = authorizeme.randomString(16)
REDIRECT_URI = "http://localhost:8000/callback"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"

@app.route("/", methods=["GET","POST"])
def index():
	print("Debug: index route reached!")
	return "Welcome to my recommendation app.To proceed, <a href='/login'>Login to Spotify</a>" #Adapted from VIDEO. 

@app.route("/login")
def login(): 	#Adapted from Spotify documentation
	#pdb.set_trace()
	print("Debug: login route reached!")
	if request.method == "GET":
		"""
		scopes  = ['user-modify-playback-state', 'streaming', 'playlist-modify-private', 'playlist-modify-public']      #List of all desired scopes for application, including adding/modifying
                	                                                                                                        #playlists and allowing music playback.
		scope = ' '.join(scopes)        #Concatenate string of scopes joining by a space.
		"""
		scope = 'playlist-modify-public'
		print(scope)

		params = { 
			"client_id": CLIENT_ID, 
			"response_type": "code",
			"redirect_uri": REDIRECT_URI,       #must be included in app details in spotify developer page
			"state": STATE,
			"scope": scope,
			"code_challenge_method": "S256",
			"code_challenge": CODE_CHALLENGE,	#added trailing comma to test debugging. matching documentation, doubt it'll help
			}   
		
		auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"	#adapted from VIDEO
		auth_url = auth_url.replace('+','%20')				#+s in url string changed to %20. Might not be necessary, but gave it a shot in debugging
		return redirect(auth_url)


@app.route("/callback", methods=["GET","POST"])
def callback():
	pdb.set_trace()
	print("Debug: callback route reached!")

	#check for error by not presence of "code" in the callback url 
	if 'error' in request.args:
		return request.args.get("error")
	
	if STATE != request.args.get("state"):	#state code returned from Spotify server during authorization request must match saved STATE value from constants
		#return "state values do not match"
		pass
	if 'code' in request.args:
		print("fuck yeahh")
		authorization_code = request.args.get("code")	#authorization code returned from Spotify server during auth request

		params = {
				"grant_type": "authorization_code",
				"code": authorization_code,
				"redirect_uri": REDIRECT_URI,
				"client_id": CLIENT_ID,
				"code_verifier": CODE_VERIFIER
			}
		headers = { 
				"Content-Type": "application/x-www-form-urlencoded"
	     		}
		
		#Submit post request to token url and save response
		response = requests.post(TOKEN_URL, data=params, headers=headers)

		#check status code of response. if not 200, catch error. Then proceed
		if response.status_code != 200:
			return "Error encountered: \n\n" + response.text
		data = response.json()	#convert response to json format, then fetch access token and refresh token values
		session['access_token'] = data.get("access_token")
		session['refresh_token'] = data.get("refresh_token")
		session['expiration'] = datetime.now().timestamp() + data.get("expires_in")

		return redirect("/home")

@app.route("/home", methods=['GET','POST'])
def home():
	pdb.set_trace()
	print("Debug: home route reached!")
	if 'access_token' not in session:
		return redirect("/login")
	if datetime.now().timestamp() > session['expiration']:
		return redirect("/refresh-token")

	return "Fuck Yeah!"

@app.route("/refresh-token")
def refresh_token():
	print("Debug: refresh_token route reached!")
	#Check cases where session doesn't contain refresh token (user not logged in), and if token not expired yet
	if 'refresh_token' not in session:
		return redirect("/login")

	if datetime.now().timestamp() < session['expiration']:	#if current time is less than expiration, go HOME!
		return redirect("/home")

	params = {
			"grant_type": "refresh_token",
			"refresh_token": session['refresh_token'],
			"client_id": CLIENT_ID
		}

	headers = {
			"Content-Type": "application/x-www-form-urlencoded",
		}

	response = requests.post(TOKEN_URL, data=params, headers=headers)	#Obtain response from post request

	#Eliminate error case where status code is not 200
	if response.status_code != 200:
		print("Error on token refresh!\n" + response.text)

	data = response.json()
	session['access_token'] = data.get("access_token")
	session['expiration'] = datetime.now().timestamp() + data.get("expires_in")
	
	return redirect("/home")

if __name__ == "__main__":
    app.run(port=8000, debug=True)

