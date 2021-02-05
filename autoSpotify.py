import json
from builtins import print
from secrets import spotify_user_id, spotify_token
import requests
import youtube_dl
import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from bs4 import BeautifulSoup

api_key = ""


def get_list_from40():
    url = "https://los40.com/lista40/"
    web_response = requests.get(url)

    soup = BeautifulSoup(web_response.content, "html.parser")

    results = soup.find_all(class_="info_grupo")
    songs_uri = []
    for para in results:
        new_uri = get_spotify_uri(para.find("p").text)
        if new_uri:
            songs_uri.append(new_uri)
    return songs_uri


def get_user_playlist():
    query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)

    response = requests.get(
        query,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(spotify_token)
        }
    )
    response_json = response.json()
    playlist_name = {}
    for item in response_json["items"]:
        playlist_name[item["name"]] = {
            "id": item["id"],
            "name": item["name"]
        }

    return playlist_name


def get_playlist_songs(playlist_id):
    query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

    response = requests.get(
        query,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(spotify_token)
        }
    )
    response_json = response.json()
    playlist_songs = []

    for item in response_json["items"]:
        playlist_songs.append(item["track"]["uri"])

    return playlist_songs


def create_playlist():
    # playlist id: info to return
    playlist_id = ""

    # Check if the playlist exists:
    user_playlists = get_user_playlist()

    for item in user_playlists:
        if item == "Python playlist":
            playlist_id = user_playlists[item]["id"]
            break

    if not playlist_id:
        # Created through json file
        request_body = json.dumps({
            "name": "Python playlist",
            "description": "",
            "public": False
        })
        query = "https://api.spotify.com/v1/users/{}/playlists".format(spotify_user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        # Return the id of the playlist
        playlist_id = response_json["id"]

    return playlist_id


def get_spotify_uri(song_name):

    query = 'https://api.spotify.com/v1/search?q={}&type=track&limit=1'.format(song_name)

    response = requests.get(
        query,
        headers={
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(spotify_token)
        }
    )

    # Response to json format
    response_json = response.json()
    response_json = response_json["tracks"]["items"]
    # Get the song
    if len(response_json) > 0:
        # We add uri data in playlists check https://developer.spotify.com/console/post-playlist-tracks/
        song = response_json[0]["uri"]
        return song
    else:
        return ""


def get_top_music_videos():
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

    request = youtube.videos().list(
        part="snippet",
        chart="mostPopular",
        maxResults=20,
        regionCode="ES",
        videoCategoryId="10"
    )

    response = request.execute()
    uris = []
    for item in response["items"]:
        youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])
        print(youtube_url)
        # get song name
        video = youtube_dl.YoutubeDL({'outtmpl': '%(id)s%(ext)s', 'quiet':True}).extract_info(youtube_url, download= False)
        print(video)
        if video["track"]:
            print("track",video["track"])
            new_uri = get_spotify_uri(video["track"])
            if new_uri:
                uris.append(new_uri)
    return uris


def add_songs(uris):
    playlist_id = create_playlist()

    # Avoid add songs already added
    playlist_songs = get_playlist_songs(playlist_id)
    final_uri = []
    for uri in uris:
        if uri not in playlist_songs:
            final_uri.append(uri)

    request_data = json.dumps(final_uri)
    query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
    response = requests.post(
        query,
        data=request_data,
        headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
        }
    )


def main():
    uris = get_top_music_videos()
    uris += get_list_from40()
    add_songs(uris)


if __name__ == "__main__":
    main()
