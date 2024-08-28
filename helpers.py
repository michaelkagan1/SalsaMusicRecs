#Helper functions used with Flask app. Access token managed by flask via session import. 
import requests, os, pdb
from flask import session
"""
ACCESS_TOKEN = ""
def token():
	global ACCESS_TOKEN
	ACCESS_TOKEN = session['access_token']
	return
"""

def song_search(ACCESS_TOKEN, song_name, limit=10):
	headers = { 
	    "Authorization": f"Bearer {ACCESS_TOKEN}"
                }   
	endpoint = "https://api.spotify.com/v1/search"

	params = { 
                'q': song_name,
                'type': 'track',
                'limit': limit
                }   


	response = requests.get(endpoint, headers=headers, params=params)
	return response

def print_songs(response):
        data = response.json()
        tracks = data.get('tracks',{}).get('items',[])

        for track in tracks:
                name = track.get('name')
                songid = track.get('id')
                artist = track.get('artists', [{}])[0].get('name')
                print(f"Song: {name}, Artist: {artist}, song_id: {songid}")
                print("\n")
        return

def song_search(song_id):
        headers = { 
                        "Authorization": f"Bearer {ACCESS_TOKEN}"
                }   

        endpoint = f"https://api.spotify.com/v1/tracks/{song_id}"

        response = requests.get(endpoint, headers=headers)
    
        if response.status_code != 200:
                print(f"Error: {response.status_code}, {response.text}")
                return None

        data = response.json()
        name = data.get("name","")
        artist = data.get("artists", [{}])[0].get("name","")
        return name, artist
    
def features(song_id):
        headers = { 
                "Authorization": f"Bearer {ACCESS_TOKEN}"
                }   
        endpoint = f"https://api.spotify.com/v1/audio-features/{song_id}"

        response = requests.get(endpoint, headers=headers)    
        return response.json()

def tempo(song_id):
        data  = features(song_id)    
        bpm = data.get('tempo')
        return bpm 

def make_playlist(name = "Auto Tempo Playlist MK"):
        endpoint = f'https://api.spotify.com/v1/users/{user_id}/playlists'
        headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}"
                'Content-Type: application/json'
                }
        params = {
                "name": name,
                "description": "based on given song and tempo",
                "public": "true"
                }
        response = requests.post(endpoint, headers=headers, json=params)

        if response.status_code != 200:
                print(f"Error: {response.status_code}, {response.text}")
                return None

        data = response.json()
        print(data)
        playlist_id = data.get("id", "")
        return playlist_id

def add_song(song_id, playlist_id):

        return


def recommend(song_id = '5mg6sU732O35VMfCYk3lmX'):      #"Ven Devorame Otra Vez"
        headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}"
                }
        bpm = GST.tempo(song_id)
        target = round(bpm)
        min_bpm = target * 0.95
        max_bpm = target * 1.05
        limit = 10
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

def parse_tracks(data):
        tracks = data.get("tracks",[])
        songs = []

        for track in tracks:
                name = track.get("name", "")
                song_id = track.get("id", "")
                artist = track.get("artists", [{}])[0].get("name","")
                songs.append([name, artist, song_id])

        for song in songs:
                print(f"Title: {song[0]}\t\t Artist: {song[1]}\t\t id: {song[2]}")
        return

