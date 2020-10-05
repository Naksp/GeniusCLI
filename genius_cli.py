import config

import argparse
from bs4 import BeautifulSoup
from dataclasses import dataclass
import json
import requests
import sys

@dataclass
class Sort:
    # Class used to hold search display variables
    order: str
    length: int

def pprint(response):
    # Prints response in a more readable way
    pretty_json = json.loads(response.text)
    print(json.dumps(pretty_json, indent = 2))

def get_lyrics_from_song_api_path(base_url, web_url, headers, song_api_path):
    # Accesses page of song_api_path and parses html for lyrics
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

def search_for_artist(base_url, web_url, search_url, params, headers, sort):
    # Gets list of artists songs and prompts user to choose one do display
    response = requests.get(search_url, params=params, headers=headers)
    response_json = response.json()
    artist_path = None
    artist_path = response_json["response"]["hits"][0]["result"]["primary_artist"]["api_path"]
    if not artist_path:
        print("Couldn't find artist.")
        exit()
    artist_name = response_json["response"]["hits"][0]["result"]["primary_artist"]["name"]

    artist_url = base_url + artist_path + "/songs?sort=" + sort.order
    response = requests.get(artist_url, headers=headers)
    response_json = response.json()

    # Print songs according to sort
    print("Showing songs by " + artist_name + ":")
    songs = []
    for song in response_json["response"]["songs"]:
        songs.append(song["title"])
    for number, song in enumerate(songs, 1):
        print(number, song)

    # Promt user for song choice
    while True:
        try:
            song_num = int(input('\033[1m' + "Enter song number to search: " + '\033[0m'))
        except ValueError:
            print("Input must be an integer between 1 and " + str(sort.length))
            continue
        if 0 < song_num <= len(songs):
            break
        else:
            print("Number must be between 1 and " + str(sort.length))

    # Get song path from previous response
    for song in response_json["response"]["songs"]:
        if song["title"] == songs[song_num-1]:
            song_api_path = song["api_path"]
            break
    lyrics = get_lyrics_from_song_api_path(base_url, web_url, headers, song_api_path)
    print(lyrics)
    exit()

def main(argv):
    # API data
    base_url = "https://api.genius.com"
    headers = {'Authorization': 'Bearer ' + config.access_token}
    web_url = "https://genius.com"

    #Search Parameters
    search_url = base_url + "/search"
    song_title = ""
    artist_name = ""
    sort = Sort("popularity", 20)

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
        search_for_artist(base_url, web_url, search_url, params, headers, sort)
    elif not artist_name:
        # Search for song name by all artists
        params = {'q': song_title}
        
    else:
        # Search for song and artist
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
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("Interrupted...Exiting.")
        sys.exit(1)