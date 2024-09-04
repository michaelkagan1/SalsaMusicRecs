"""
Using PKCE OAuth2 Flow: https://developer.spotify.com/documentation/web-api/tutorials/code-pkce-flow#request-user-authorization
adapted to python, flask

Michael Kagan 2024
"""
from flask import Flask, render_template, redirect, request, session, jsonify
from flask_session import Session
from datetime import datetime
import urllib.parse
import requests, os, math, time
from config import *

app = Flask(__name__)
app.config.from_pyfile("config.py")	#config.py contains: app-secret-key, client id/secret, session configs, code verifier/challenge, endpoint URIs, & database uri
Session(app)

@app.route("/", methods=["GET","POST"])
def index():
	return render_template("home.html")

@app.route("/login")
def login(): 	#Adapted from Spotify documentation
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
	db.execute("DELETE FROM songs")	#remove previously queried data in songs database 
	return redirect("/")

@app.route("/callback", methods=["GET","POST"])
def callback():

	#check for error by not presence of "code" in the callback url 
	if 'error' in request.args:
		return render_template("layout.html", error=request.args.get("error"))

	if STATE != request.args.get("state"):	#state code returned from Spotify server during authorization request must match saved STATE value from constants
		return render_template("layout.html", error="State value mismatch!")

	if 'code' in request.args:
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

@app.route("/refresh-token")
def refresh_token():
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
		return redirect('/login')	
	data = response.json()
	session['access_token'] = data.get("access_token")
	session['expiration'] = datetime.now().timestamp() + data.get("expires_in")
	
	return redirect("/home")


@app.route("/home", methods=['GET','POST'])
def home():
	if request.method == "GET":
		if 'access_token' not in session:
			return redirect("/login")
		if datetime.now().timestamp() > session['expiration']:
			return redirect("/refresh-token")

		response = song_search(session['access_token'], "Blackbird")
		
		return render_template("home.html")
	elif request.method == "POST":
		if 'access_token' not in session:
			return redirect("/login")
		if datetime.now().timestamp() > session['expiration']:
			return redirect("/refresh-token")
		query = request.form.get("title-input")
		response = song_search(session['access_token'], query, limit=10)
		if response.status_code != 200:
			return response.text
		songs = print_songs(response)

		return render_template("results.html", songs=songs[:10])

@app.route("/recs", methods=['GET','POST'])
def recs():
	#Check for access_token precence and validity
	if 'access_token' not in session:
			return redirect("/login")
	if datetime.now().timestamp() > session['expiration']:
		return redirect("/refresh-token")

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
		#Clear database saved songs from previous (recommend) query
		db.execute("DELETE FROM songs")

		data = recommend(session['access_token'], song_id)	#Runs recommend function with token in session, based on speed and seed of queried song.				
		songs = parse_tracks(session['access_token'], data)
		for song in songs:	
			db.execute("INSERT INTO songs (title, artist, song_id) VALUES (?, ?, ?)", song['title'], song['artist'], song['song_id'])

	songs = db.execute("SELECT * FROM songs")
	(songi, songf, pagei, pagef) = pagination(page=1)	
	return render_template("recs.html", songs=songs[songi:songf], page=1, pagei=pagei, pagef=pagef)

@app.route("/recs/<int:page>")	#Only used with get requests
def page_route(page):
	(songi, songf, pagei, pagef) = pagination(page)	
	if page in range(pagei, pagef+1):
		songs = db.execute("SELECT * FROM songs")
		return render_template("recs.html", songs=songs[songi:songf], page=page, pagei=pagei, pagef=pagef)
	else:
		return render_template("layout.html", error="Page out of range!")



""" 

Helper functions for api calls defined below 

"""


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
        return response.json()

def parse_tracks(ACCESS_TOKEN, data):
	tracks = data.get("tracks", [])
	songs = []

	for track in tracks:
		title = track.get("name", "")
		song_id = track.get("id", "")
		#bpm = tempo(ACCESS_TOKEN, song_id)
		artist = track.get("artists", [{}])[0].get("name", "")
		#songs.append({"title": title, "artist": artist, "bpm": bpm, "song_id": song_id})
		songs.append({"title": title, "artist": artist, "song_id": song_id})
		time.sleep(.02)
	return songs  # Ensure the return statement is indented correctly
def pagination(page):
	query =  db.execute('SELECT COUNT (*) AS count FROM songs')	#queries all songs from database
	num_songs = query[0]['count']		#counts total songs available
	maxpage = math.ceil(num_songs/10)	#finds max number of pages to generate. 

	pagei = max(page - 1, 1)		#first page is the larger of 1 or page - 1 
	pagef = min(page + 1, maxpage)		#final page is the smaller of maxpage or page + 1
	numpages = pagef-pagei + 1		#numpages keeps track of number of pages generated
	while numpages < min(3, maxpage):	#adds pages until max pages is generated, capped out at 3 pages. 
		if pagef<maxpage:
			pagef += 1
			numpages += 1
		else:
			pagei -= 1
			numpages += 1

	songi = (page-1) * 10			#first song, referenced by which page
	songf = min( (songi + 10) ,num_songs-1)	#final song, either initial song + 10 or the last song, whichever is smaller

	return songi, songf, pagei, pagef	#returns all 4 numbers to the route page rendering. Used in jinja2 loop in the html to generate the relevant song list and page links
"""
if __name__ == "__main__":
    app.run(port=8000, debug=False)
    """
