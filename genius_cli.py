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

@dataclass
class Song:
    title: str
    artist: str
    lyrics: str

def print_lyrics(song, out_file=None):
    if out_file:
        print('\n' + song.title + '\n' + song.artist + '\n', file=out_file)
        print(song.lyrics.lstrip(), file=out_file)
    else:
        print('\n' + '\033[1m' + song.title + '\033[0m' + '\n' + song.artist + '\n')
        print(song.lyrics.lstrip())

def pprint(response):
    # Prints response in a more readable way
    # Just used for testing
    pretty_json = json.loads(response.text)
    print(json.dumps(pretty_json, indent = 2))

def get_song_object_from_song_api_path(base_url, web_url, headers, song_api_path):
    # Accesses page of song_api_path and parses html for lyrics
    song_url = base_url + song_api_path
    response = requests.get(song_url, headers=headers)
    response_json = response.json()
    song_title = response_json["response"]["song"]["title"]
    artist_name = response_json["response"]["song"]["primary_artist"]["name"]
    page_path = response_json["response"]["song"]["path"]
    page_url = web_url + page_path
    page = requests.get(page_url)
    # Parse html
    soup = BeautifulSoup(page.text, 'html.parser')
    soup = soup.find(class_="lyrics")
    song = Song(song_title, artist_name, soup.get_text())
    # TODO make this return None on failure
    return song

def search_by_artist(base_url, web_url, search_url, headers, sort, artist_name):
    # Gets list of artists songs and prompts user to choose one do display
    artist_path = None
    page_num = 1

    # Parse search results page by page until matching artist is found
    print("\nSearching for artist", end='', flush=True)
    while not artist_path:
        print(".", end='', flush=True)
        params = {'q': artist_name, "page": page_num}
        response = requests.get(search_url + "/", params=params, headers=headers)
        response_json = response.json()
        for hit in response_json["response"]["hits"]:
            if hit["result"]["primary_artist"]["name"].lower() == artist_name:
                artist_path = hit["result"]["primary_artist"]["api_path"]
                artist_name = hit["result"]["primary_artist"]["name"]
                print('\n')
                break
        if not artist_path:
            page_num += 1
    if not artist_path:
        print("Couldn't find artist.")
        sys.exit(0)

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

    song_num = choose_song_from_list(response_json, songs, sort)

    # Get song path from previous response
    for song in response_json["response"]["songs"]:
        if song["title"] == songs[song_num-1]:
            song_api_path = song["api_path"]
            break

    song = get_song_object_from_song_api_path(base_url, web_url, headers, song_api_path)
    if song:
        return song
    else:
        return None

def search_by_song_title(base_url, web_url, search_url, headers, sort, song_title):
    # Get list of matching songs and prompt user to choose one to display
    params = {'q': song_title}
    response = requests.get(search_url, params=params, headers=headers)
    response_json = response.json()
    songs = []
    paths = []
    display_list = []
    for hit in response_json["response"]["hits"]:
        songs.append(hit["result"]["title"])
        paths.append(hit["result"]["api_path"])
        display_list.append(hit["result"]["title"] + " - " + hit["result"]["primary_artist"]["name"])
    for number, song in enumerate(display_list, 1):
        print(number, song)

    song_num = choose_song_from_list(response_json, songs, sort)

    for hit in response_json["response"]["hits"]:
        if hit["result"]["api_path"] == paths[song_num-1]:
            song_api_path = hit["result"]["api_path"]
            break

    song = get_song_object_from_song_api_path(base_url, web_url, headers, song_api_path)
    if song:
        return song
    else:
        return None

def search_by_song_and_artist(base_url, search_url, web_url, headers, song_title, artist_name):
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
        song = get_song_object_from_song_api_path(base_url, web_url, headers, api_path)
        return song
    else:
        return None


def choose_song_from_list(response_json, song_list, sort):
    # Promt user for song choice and return path of desired song
    while True:
        try:
            song_num = int(input('\033[1m' + "Enter song number to search: " + '\033[0m'))
        except ValueError:
            print("Input must be an integer between 1 and " + str(len(song_list)))
            continue
        if 0 < song_num <= len(song_list):
            return song_num
        else:
            print("Number must be between 1 and " + str(len(song_list)))

    # Get song path from previous response
    for song in response_json["response"]["songs"]:
        if song["title"] == song_list[song_num-1]:
            song_api_path = song["api_path"]
            return song_api_path
    return None

def start_search_with_user_input():
    song_title = input("Song Title: ")
    artist_name = input("Artist Name: ")
    init_search_params(song_title, artist_name, None) # No batch file

def init_search_params(song_title, artist_name, batch_files):
    # API data
    base_url = "https://api.genius.com"
    headers = {'Authorization': 'Bearer ' + config.access_token}
    web_url = "https://genius.com"

    #Search Parameters
    search_url = base_url + "/search"
    sort = Sort("popularity", 20)

    if batch_files:
        # Read/write to file
        print("Reading from " + batch_files[0] + "...")
        with open(batch_files[0], 'r') as in_file, open(batch_files[1], 'w') as out_file:
            for line in in_file:
                if line:
                    song_info = line.split(', ')
                    song_title = song_info[0]
                    artist_name = song_info[1].strip()
                    start_search(base_url, web_url, search_url, headers, sort, song_title, artist_name, in_file, out_file)
    else:
        start_search(base_url, web_url, search_url, headers, sort, song_title, artist_name)

def start_search(base_url, web_url, search_url, headers, sort, song_title, artist_name, in_file=None, out_file=None):
    if not any([song_title, artist_name]):
        print("Must enter song or artist")
        start_search_with_user_input()

    if not song_title:
        # Search for songs by artist
        song = search_by_artist(base_url, web_url, search_url, headers, sort, artist_name)

    elif not artist_name:
        # Search for song name by all artists
        song = search_by_song_title(base_url, web_url, search_url, headers, sort, song_title)
        
    else:
        # Search for song and artist
        song = search_by_song_and_artist(base_url, search_url, web_url, headers, song_title, artist_name)

    if song:
        if out_file:
            print_lyrics(song, out_file)
        else:
            print_lyrics(song, False)
    else:
        print("No matching results found.")

def main(argv):
    # Parse arguments
    if argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('-a')
        parser.add_argument('-s')
        parser.add_argument('-b', nargs=2)
        args = parser.parse_args()

        song_title = args.s if args.s else None
        artist_name = args.a if args.a else None
        batch_files = args.b if args.b else None
        init_search_params(song_title, artist_name, batch_files)
    else:
        start_search_with_user_input()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("Interrupted...Exiting.")
        sys.exit(1)