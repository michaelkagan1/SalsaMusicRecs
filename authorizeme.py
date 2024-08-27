import requests, secrets, string, hashlib

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

