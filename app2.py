"""
Spotify API access using regular Authorization Code workflow.
No Code verifier or code-challenge used.
"""

import pdb
from flask import Flask, redirect, render_template, session, request
from flask_session import Session
import authorizeme
import urllib.parse

#Setup App with flask app
app = Flask(__name__)
app.secret_key = 'Kjske-6VXxb-9p3vW-oIUt6'

#Setup session config and session
app.config["SESSION_PERMANENT"] = False         #treated like a session cookie, deletes session when browser/server quit
app.config["SESSION_TYPE"] = "filesystem"       #contents of session stored in servers files, not in cookie. for privacy
Session(app)

#Setup global parameters for client info & authorization routes
CLIENT_ID = "2d5ddacbcfa74e2583a50fac031e5325"
CLIENT_SECRET = "c50abc283e004e989f1523c2d5aa8dfe"
STATE = authorizeme.randomString(16)

AUTH_ENDPOINT = "https://accounts.spotify.com/authorize"
TOKEN_ENDPOINT = "https://accounts.spotify.com/api/token"
REDIRECT_URI = "http://localhost:8000/callback"

@app.route("/")
def enter():
	return "Welcome to my spotify app. To proceed, <a href='/login'>Login with Spotify</a>"

@app.route("/login", methods=['GET','POST'])
def login():
	#Setup parameters
	scope = 'playlist-modify-private'
	params = {
			"client_id": CLIENT_ID,
			"response_type": "code",
			"redirect_uri": REDIRECT_URI,
			"state": STATE,
			"scope": scope,
			"show_dialog": True
			}

	#Create + encode URL for requesting auth
	authorize_path = AUTH_ENDPOINT + '?' + urllib.parse.urlencode(params)
#	authorize_path = authorize_path.replace('+','%20')
	
	#Redirect to authorize uri
	print(authorize_path)
	return redirect(authorize_path)
	
@app.route("/callback")
def callback():
	#Catch exceptions with request.args
	print("Callback route reached.")
	if "error" in request.args:
		return request.args.get('error')  

	if request.args.get("state") != STATE:
		return "State mismatch error"
	
	#extract data from response using request.args
	auth_code = request.args.get("code")

	#Setup parameters for post requst
	params = {
			"grant_type": "authorization_code",
			"code": auth_code,
			"redirect_uri": REDIRECT_URI
			}

	#Setup headers for post requst
	id_secret_64 = authorizeme.encode64(f"{CLIENT_ID}:{CLIENT_SECRET}")	#Assemble base 64 encoded string of "Client_id:Client_secret"

	header = {
			"Authorization": f"Basic {id_secret_64}",
			"Content-Type": "application/x-www-form-urlencoded"
			}

	#Send post request to token uri
	response = requests.post(TOKEN_ENDPOINT, data=params, headers=header)

	#Catch exceptions in response url using (check for error or state mismatch)
	if response.status_code != 200:
		return response.status_code, response.content

	#Save token, refresh, expiration in session
	data = response.json()
	session['token']  
	session['expiration']

	return "Callback page"

if __name__ == "__main__":
	app.run(port = 8000, debug=True)
