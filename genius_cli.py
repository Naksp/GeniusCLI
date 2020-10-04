import config

import json
import requests
from bs4 import BeautifulSoup
import bs4

# API data
base_url = "https://api.genius.com"
headers = {'Authorization': 'Bearer ' + config.access_token}

web_url = "https://genius.com"

#Search Parameters
search_url = base_url + "/search"
song_title = ""
artist_name = ""

song_title = input("Song Title: ")
artist_name = input("Artist Name: ")
if not any([song_title, artist_name]):
    print("Must enter song and artist")
    exit()

params = {'q': song_title}

def get_lyrics_from_song_api_path(song_api_path):
    #Accesses page of song_api_path and parses html for lyrics
    #:param song_api_path: api_path of song, parsed from search results
    #:return: lyrics of desired song
    song_url = base_url + song_api_path
    response = requests.get(song_url, headers=headers)
    r_json = response.json()
    page_path = r_json["response"]["song"]["path"]
    page_url = web_url + page_path
    page = requests.get(page_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    soup = soup.find(class_="lyrics")
    lyrics = soup.get_text()
    return lyrics
    
# Send search request
response = requests.get(search_url, params=params, headers=headers)
response_json = response.json()

# Parse search results for matching artist
song_info = None
for hit in response_json["response"]["hits"]:
    artist = hit["result"]["primary_artist"]["name"]
    if artist.lower() == artist_name.lower():
        song_info = hit
        break

# Parse for song api_path
if song_info:
    api_path = song_info["result"]["api_path"]
    lyrics = get_lyrics_from_song_api_path(api_path)
    print(lyrics)
else:
    print("Song not found.")