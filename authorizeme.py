import requests, secrets, string, hashlib

def requestOAuth():
	#send get request to /authorize endpoint
	#parameters include code_challenge + code_challenge_method   
	client_id = "2d5ddacbcfa74e2583a50fac031e5325"		#Client id taken from spotify developer api registered app information
	scopes  = ['user-modify-playback-state', 'streamint', 'playlist-modify-private', 'playlist-modify-public']	#List of all desired scopes for application, including adding/modifying 
															#playlists and allowing music playback.
	scope = ' '.join(scopes)	#Concatenate string of scopes joining by a space.
	state = randomString(16)	#Generate random string of 16 characters using same generator as for code verifier.
	
	#Generate random string of 50 for code verifier. Hash to produce code challenge. Helper functions below
	codeVerifier = randomString(50)
	code_challenge = hash(codeVerifier)


	endpoint = "https://accounts.spotify.com/authorize"	#authorization endpoint for obtaining authorization
	params = {
		"client_id": client_id, 
		"response_type": "code",
		"redirect_uri": "http://localhost:5000/callback",	#must be included in app details in spotify developer page
		"state": state,
		"scope": scope,
		"code_challenge_method": "S256",
		"code_challenge": code_challenge		
		}
	
	response = requests.get(endpoint, params=params)

	return response

def randomString(length = 50):
	valid = string.ascii_letters + string.digits + "_.-~"	#valid characters for use in code verifier string
	randstring = ''.join( [secrets.choice(valid) for i in range(length)] )	#produce string with length number of random choices from valid characters list
	return randstring

def hash(string):
	h = hashlib.sha256()
	encoded = bytes(string, 'utf-8') 
	h.update(encoded)
	hashed = h.hexdigest()
	return hashed

