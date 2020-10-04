import config

import json
import requests

base_url = "https://api.genius.com"
headers = {'Authorization': 'Bearer ' + config.access_token}

search_url = base_url + "/search"
song_title = "Humble"
artist_name = "Kendrick Lamar"
params = {'q': song_title}

def get_url_path_from_song_api_path(song_api_path):
    song_url = base_url + song_api_path
    response = requests.get(song_url, headers=headers)
    r_json = response.json()
    print(r_json["response"]["song"]["path"])

response = requests.get(search_url, params=params, headers=headers)

response_json = response.json()

# Parse search results for matching artist
song_info = None
for hit in response_json["response"]["hits"]:
    if hit["result"]["primary_artist"]["name"] == artist_name:
        song_info = hit
        break

# Parse for song api_path
if song_info:
    api_path = song_info["result"]["api_path"]
    get_url_path_from_song_api_path(api_path)
