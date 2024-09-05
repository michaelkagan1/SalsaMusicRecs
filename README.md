# **Salsa Song Recs** 
### [Video demo](https://youtu.be/5BVYp-aCEqI)

### To run the file
1. Obtain a spotify API Client ID and Client Secret by creating a spotify app in the [spotify developer page](https://developer.spotify.com)
	- Add the callback URI: `http://localhost:8000/callback`
2. Make a random string that will be your secret key.
3. Create a environment file named `.env` in the main flask app directory with the following code. Be sure to avoid any spaces or quotes.
```
SECRET_KEY=your_secret_key_here
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
```

4. Run app on port 8000 with the following code: `flask run --port=8000` (that's what my callback URI uses)

## App Overview and Description

This flask-based python app allows a user to discover salsa songs at a desired speed/tempo/bpm. This is particularly useful for salsa teachers (such as myself) to find an adequate-paced song for teaching and demonstrating moves. It's also useful for dancers that want to control the speed they practice at. The app uses the Spotify API and uses a searched song as the seed query for finding more recommendations. 

## User and GUI Overview
1. The first thing a user sees when navigating to my app is a blank, dark themed page with a Spotify logo at the bottom and a disabled search bar. 
2. The login button routes users through to the spotify account login and scope permissions checkpoint. 
3. After logging in and granting permission, a user can enter a song into the search field. 
4. The results page shows a table of the top 10 track results for the user's song query. On the right, an embedded spotify player is loaded with the first song in the list. A user can preview songs by clicking the play button in the results table, which loads that song into the embedded player. A user can not use the embedded player like a standalone spotify app. Each song in the results has an option to *Get recs*. 
5. The final recs - recommendations - page delivers up to 50 song recommendations based on the original queried song. They are found by matching the main criterium, which is target tempo, as well as using the seed song and seed genre - salsa.
6. Along with the recs table, there is a similar embedded spotify player on the right of the screen. The new element is a set of page controls at the bottom of songs list. Each page contains up to 10 songs.

The navbar at the top has a button to log in. My app uses the spotify api, therefor it requires users to go through the OATH2.0 authorization. 

## File Overview
Here is a list of files with a brief description in my application folder:
- app.py	(main flask app controller, with all routes, and all api call functions)
- config.py	(not included - helper config app, containing app secrets, such as secret key, and token information, as well as endpoint uris, and sqlite database initiation)
- songs.db	(sqlite3 database used to store recommended song request response. db was overwritten everytime a query was made) 
- authorizeme.py	(helper python file with my functions used for generating random, url-save strings used for tokens and secrets, as well as hashing said strings)
- requirements.txt	(txt file containing necessary libraries for program to run)
- templates/
	- layout.html	(General layout html with header navbar and footer, as well as jinja template blocks)
	- home.html	(Empty template adding a search function to the layout template. Disabled if no user logged in)
	- header.html	(navbar portion which is included in layout. uses jinja if loop to display a login, or home and logout button)
	- results.html	(Table results html template which uses jinja loops to generate a list of table rows with song data and interactive buttons)
	- player.html	(Player which is populated by a javascript code, which extracts track id data from the jinja-generated song rows)
	- recs.html	(Same as results, with one button removed and pagination added)
	- pagination.html	(generates page buttons displayed under the results, also using jinja loop)
- static/
	- spotify.png


## Challenges

This project was a huge learning process for me every step of the way. However it included a few particularly difficult roadblocks that took the most time to figure out. 

#### OATH2.0 & hashing (and API calls in general)
A first for me, it took a lot of time looking at the spotify documentation and online examples to get comfortable with the syntax for submitting requests and parsing responses. 
Meanwhile, authorization was tricky for several reasons. Everytime I thought I found ***the*** bug, it turned out there was another, yet undiscovered one lurking somewhere behind it. Of these issues, the random string hashing and base64 encoding was the trickiest. However, even when I was sure I had that figured out, I couldn't proceed until I solved the issue with...

#### Safary privacy restrictions
Yes, safari privacy restrictions. After spending well over 2 days reading the spotify api documentation, watching youtube tutorials, rewriting code and fruitless conversations with my best friend, chatGPT, I decided to run the flask app on google chrome instead. ***poof*** It worked. It turns out, incognito mode in safari was restricting certain functionality (I still don't know what), but chrome incognito mode did not. Only much later did I realize, I can in fact run my app in safari, just not in incognito. 

#### Pagination
The trouble with coding the pagination for me was 3-fold. 

1. The actual algorithm for dynamically generating the page buttons, while constraining them to 3 buttons max, never exceeding the range of 1 to the final page of songs. This was a problem because I didn't know whether the ideal solution should be coded in my flask app (in conjuction with Jinja templating), in my html code as a JS script (appending html children), or as a separate JS helper file. The solution to this was simple in the end - I used a helper python function in my flask app. Given a target page, it returned the indeces of the starting and ending pages, as well as the starting and ending songs in the display page This function was less than 20 lines. I chose this path, because I was most familiar with python, and a friend made me realize - that was the reason for flask in the first place. 
2.  Pagination made me face the issue of saving the songs somehow. If not, the app might re-send api requests to spotify and reload my recs list, potentially with new songs, so I wouldn't have a static results table. I never tried this, but this was my suspicion. This led me down the path of making a simple sqlite database, which I used to save recommendation responses and generate new pages and song lists. Every time a new post request is made to my *"/recs"* route, the db is wiped and repopulated with the new results.
3. Centering my page buttons! This was a trivial but important lessson in basic html styling that took longer for me to learn that I would have liked. Moral of the story: when you have multiple nested tags and html elements, bootstrap classes can and will easily interfere with eachother. It's important to backtrack, even across templates to make sure that only the necessary element parent has the needed styling class. In my case, I had redundant classes for flexbox, or for centering my text, even across 2 html templates. This was resolved when I simplified my code.

## Future Steps:
Currently, the app is only accessible on my local device and while it works, it's in dev mode only. I want to deploy it to a host server like AWS and also apply for a Quota Extension Request, so it could be available for general use. After that, I would like to add further functionality to find recommendations based on different search criteria, for example: language, country, or different genres. Use cases could be: music for working out, mixing songs for creative media projects, or finding songs with specific speeds for dance choreographies of different styles. 
