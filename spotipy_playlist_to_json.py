import json
import spotipy
from _credentials_spotipy import *
from spotipy.oauth2 import SpotifyClientCredentials

spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=my_client_id,
        client_secret=my_client_secret,
    )
)

dict_key = {
    -1: "Not identified",
    0: "C",
    1: "C#/Db",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    6: "F#/Gb",
    7: "G",
    8: "Ab",
    9: "A",
    10: "Bb",
    11: "Cb/B",
}
dict_mode = {0: "Minor", 1: "Major"}
dict_timesig = {3: "3/4", 4: "4/4", 5: "5/4", 6: "6/4", 7: "7/4"}

while True:
    playlist_link = input("Enter a link to a Spotify playlist:\n")
    try:
        playlist = spotify.playlist(playlist_link)
        playlist_name = playlist["name"]
        print(f"\nPlaylist found: {playlist_name}")
        break
    except spotipy.exceptions.SpotifyException:
        print("\nCouldn't find a playlist with the input link.")
        print("The link should look like:")
        print("https://open.spotify.com/playlist/abcd1234\n")

track_urls = []
for j in playlist["tracks"]["items"]:
    track_link = j["track"]["external_urls"]["spotify"]
    track_urls.append(track_link)

track_dict_list = []
for enum, track_id in enumerate(track_urls, 1):
    print(f"    Working on track {enum}/{len(track_urls)}")

    track_info = spotify.track(track_id=track_id)
    track_name = track_info["name"]
    track_artists = [artist["name"] for artist in track_info["artists"]]
    track_album = track_info["album"]["name"]
    track_album_art = track_info["album"]["images"][0]["url"]

    audio_features = spotify.audio_features(track_id)
    track = audio_features[0]
    dance = int(round(track["danceability"] * 100, 0))
    energy = int(round(track["energy"] * 100, 0))
    key_val = track["key"]
    key = dict_key[key_val]
    loud = round(track["loudness"], 1)
    mode_val = track["mode"]
    mode = dict_mode[mode_val]
    speech = int(round(track["speechiness"] * 100, 0))
    acoust = int(round(track["acousticness"] * 100, 0))
    instr = int(round(track["instrumentalness"] * 100, 0))
    live = int(round(track["liveness"] * 100, 0))
    vale = int(round(track["valence"] * 100, 0))
    tempo = int(round(track["tempo"], 0))
    durs = int(track["duration_ms"] / 1000)
    timesig_val = track["time_signature"]
    timesig = dict_timesig[timesig_val]

    dict_transformed = {
        "artist": track_artists,
        "track_album": track_album,
        "track_album_art": track_album_art,
        "track_name": track_name,
        "danceability": dance,
        "energy": energy,
        "key_val": key_val,
        "key": key,
        "loudness": loud,
        "mode_val": mode_val,
        "mode": mode,
        "speechiness": speech,
        "acousticness": acoust,
        "instrumentalness": instr,
        "liveness": live,
        "valence": vale,
        "tempo": tempo,
        "duration": durs,
        "timesig_val": timesig_val,
        "timesig": timesig,
    }
    track_dict_list.append(dict_transformed)

with open("track_info.json", "w") as f:
    json.dump(track_dict_list, f, indent=3)
