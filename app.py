"""
Using PKCE OAuth2 Flow: https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow#request-user-authorization
adapted to python, flask


ISSUES (8/27/24)
	1. Works in Chrome but not in Safari. 
	2. Adjust results & recs tables + input field to dynamically adjust
"""
import pdb

from flask import Flask, render_template, redirect, request, session, jsonify
from flask_session import Session
from datetime import datetime
from cs50 import SQL
import urllib.parse
import requests, os
import authorizeme
import helpers as H	#my own python file

app = Flask(__name__)
app.secret_key = 'Kjske-6VXxb-9p3vW-oIUt6'

#Taken from CS50 lecture material
app.config["SESSION_PERMANENT"] = False         #treated like a session cookie, deletes session when browser/server quit
app.config["SESSION_TYPE"] = "filesystem"       #contents of session stored in servers files, not in cookie. for privacy
Session(app)

#Setup sqlite database
db = SQL("sqlite:///songs.db")

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
	return render_template("home.html")

@app.route("/login")
def login(): 	#Adapted from Spotify documentation
	print("Debug: login route reached!")
	if request.method == "GET":
		scopes  = ['user-modify-playback-state', 'streaming', 'playlist-modify-private', 'playlist-modify-public']      #List of all desired scopes for application, including adding/modifying
                	                                                                                                        #playlists and allowing music playback.
		scope = ' '.join(scopes)        #Concatenate string of scopes joining by a space.

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

@app.route("/logout")
def logout():
	session.clear()
	return redirect("/")

@app.route("/callback", methods=["GET","POST"])
def callback():
	print("Debug: callback route reached!")

	#check for error by not presence of "code" in the callback url 
	if 'error' in request.args:
		return request.args.get("error")
	
	if STATE != request.args.get("state"):	#state code returned from Spotify server during authorization request must match saved STATE value from constants
		#return "state values do not match"
		return "State value mismatch!"

	if 'code' in request.args:
		print("fuck yeahh")
		#pdb.set_trace()
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
		print("before redirect")
		return redirect("/home")

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


@app.route("/home", methods=['GET','POST'])
def home():
	print("Debug: home route reached!")
	if request.method == "GET":
		if 'access_token' not in session:
			return redirect("/login")
		if datetime.now().timestamp() > session['expiration']:
			return redirect("/refresh-token")

		response = song_search(session['access_token'], "Blackbird")
#		print_songs(response)
		
		return render_template("home.html")
	elif request.method == "POST":
		#		pdb.set_trace()
		query = request.form.get("title-input")
		response = song_search(session['access_token'], query, limit=10)
		if response.status_code != 200:
			return response.text
		songs = print_songs(response)

		return render_template("results.html", songs=songs[:10])

@app.route("/recs", methods=['GET','POST'])
def recs():
	if request.method == 'POST':
		path = request.form.get("request_type")	#This is the name label on the recs list buttons. 
		song_id = request.form.get("song_id")

		if path == "put":		#Use put request to allow playback in user's personal spotify device. So far not working.
			# Build playback PUT request
			ACCESS_TOKEN = session['access_token']
			endpoint = API_BASE_URL + "me/player/play"
			
			headers = { 
					"Authorization": f"Bearer {ACCESS_TOKEN}",
	      				"Content-Type": "application/json"
	      				}

			params = {
					"context_uri": f"spotify:track:{song_id}"	
					}
			requests.put(endpoint, data=params, headers=headers)
			return render_template("recs.html", songs=songs)

		data = recommend(session['access_token'], song_id)	#Runs recommend function with token in session, based on speed and seed of queried song.				
		songs = parse_tracks(session['access_token'], data)
		for song in songs:	
			db.execute("INSERT INTO songs (Title, artist, bpm, song_id) VALUES (?, ?, ?, ?)", song['Title'], song['artist'], song['tempo'], song['id'])

		return render_template("recs.html", songs=songs)
	elif request.method == "GET":	#path requested by page numbers in recs list
		#Use a sqlite3 database to save tracks in recommended list. each time POST is requested, db is overwritten by results list
		#and each get request from the page buttons will extract the offset number of tracks desired.
		pass	

def song_search(ACCESS_TOKEN, song_title, limit=10):
	#	ACCESS_TOKEN = session['access_token'] 
	headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}"
                }
	endpoint = "https://api.spotify.com/v1/search"

	params = {
                'q': song_title,
                'type': 'track',
                'limit': limit
                }

	response = requests.get(endpoint, headers=headers, params=params)
	return response

def print_songs(response):
	data = response.json()
	tracks = data.get('tracks',{}).get('items',[])
	songs = []
	for track in tracks:
		title = track.get('name')
		songid = track.get('id')
		artist = track.get('artists', [{}])[0].get('name')
		songs.append({"Title":title, "artist":artist, "id":songid})
	return songs

def features(ACCESS_TOKEN, song_id):
        headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}"
                }
        endpoint = f"https://api.spotify.com/v1/audio-features/{song_id}"

        response = requests.get(endpoint, headers=headers)
        return response.json()

def tempo(ACCESS_TOKEN, song_id):
        data  = features(ACCESS_TOKEN, song_id)
        bpm = data.get('tempo')
        return round(bpm, 1)

def recommend(ACCESS_TOKEN, song_id = '5mg6sU732O35VMfCYk3lmX'):      #"Ven Devorame Otra Vez"
        headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}"
                }
        bpm = tempo(ACCESS_TOKEN, song_id)
        target = round(bpm)
        min_bpm = target * 0.95
        max_bpm = target * 1.05
        limit = 50
        tracks = [song_id]
        #set_trace()
        lim = f'limit={limit}'
        seed_tracks = 'seed_tracks='+(',').join(tracks)
        seed_genres = 'seed_genres=salsa'
        min_tempo = f"min_tempo={min_bpm}"
        max_tempo = f"max_tempo={max_bpm}"
        target_tempo = f"target_tempo={target}"

        endpoint = "https://api.spotify.com/v1/recommendations"
        param_list = [lim, seed_tracks, seed_genres, min_tempo, max_tempo, target_tempo]

        url = endpoint + '?' + ('&').join(param_list)

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
                print(f"Error: {response.status_code}, {response.text}")
                return None
        print(f"{response.status_code}")
        return response.json()

def parse_tracks(ACCESS_TOKEN, data):
	tracks = data.get("tracks", [])
	songs = []

	for track in tracks:
		title = track.get("name", "")
		song_id = track.get("id", "")
		bpm = tempo(ACCESS_TOKEN, song_id)
		artist = track.get("artists", [{}])[0].get("name", "")
		songs.append({"Title": title, "artist": artist, "tempo": bpm, "id": song_id})

	return songs  # Ensure the return statement is indented correctly

if __name__ == "__main__":
    app.run(port=8000, debug=True)
