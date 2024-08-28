import requests, secrets, string, hashlib, base64

def randomString(length = 50):
	valid = string.ascii_letters + string.digits + "_.-~"	#valid characters for use in code verifier string
	randstring = ''.join( [secrets.choice(valid) for i in range(length)] )	#produce string with length number of random choices from valid characters list
	return randstring

def hash(string):
	h = hashlib.sha256()
	encoded = bytes(string, 'utf-8') 
	h.update(encoded)
	hashed = h.digest()
	hashed64 = base64.urlsafe_b64encode(hashed).rstrip(b'=').decode('utf-8')
	return hashed64

def encode64(string):
	byt_string = string.encode('utf-8')
	encoded_bytes = base64.urlsafe_b64encode(byt_string)
#	based64 = base64.urlsafe_b64decode(encoded_bytes).decode('utf-8')
	based64 = encoded_bytes.decode('utf-8')
	return based64

