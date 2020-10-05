import config

import sys
import argparse
import json
import requests
from bs4 import BeautifulSoup


def get_lyrics_from_song_api_path(base_url, web_url, headers, song_api_path):
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

def search_for_artist(base_url, search_url, params, headers, sort):
    response = requests.get(search_url, params=params, headers=headers)
    response_json = response.json()
    artist_path = None
    artist_path = response_json["response"]["hits"][0]["result"]["primary_artist"]["api_path"]
    if artist_path:
        print(artist_path)
    artist_url = base_url + artist_path + "/songs?sort=" + sort
    response = requests.get(artist_url, headers=headers)
    response_json = response.json()
    print(response_json)
    
def main(argv):
    # API data
    base_url = "https://api.genius.com"
    headers = {'Authorization': 'Bearer ' + config.access_token}
    web_url = "https://genius.com"
    sort = "popularity"

    #Search Parameters
    search_url = base_url + "/search"
    song_title = ""
    artist_name = ""

    # Parse arguments
    if argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('-a')
        parser.add_argument('-s')
        args = parser.parse_args()
        if args.s is not None:
            song_title = args.s
        if args.a is not None:
            artist_name = args.a
    else:
        song_title = input("Song Title: ")
        artist_name = input("Artist Name: ")

    if not any([song_title, artist_name]):
        print("Must enter song or artist")
        exit()

    if not song_title:
        # Search for songs by artist
        params = {'q': artist_name}
        search_for_artist(base_url, search_url, params, headers, sort)

    elif not artist_name:
        # Search for song name by all artists
        params = {'q': song_title}
        
    else:
        # Send search request
        params = {'q': song_title}
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
            lyrics = get_lyrics_from_song_api_path(base_url, web_url, headers, api_path)
            print(lyrics)
        else:
            print("Song not found.")

if __name__ == "__main__":
    main(sys.argv[1:])