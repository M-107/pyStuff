import json
import spotipy
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from spotipy.oauth2 import SpotifyClientCredentials

spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id="#",
        client_secret="#",
    )
)


def get_baseline(y):
    out_y = y
    lam = 100
    p = 0.1
    niter = 20
    len_y = len(y)
    diag_matrix = sparse.diags([1, -2, 1], [0, -1, -2], shape=(len_y, len_y - 2))
    w = np.ones(len_y)
    for i in range(niter):
        diag_back = sparse.spdiags(w, 0, len_y, len_y)
        z = diag_back + lam * diag_matrix.dot(diag_matrix.transpose())
        out_y = spsolve(z, w * y)
        w = p * (y > out_y) + (1 - p) * (y < out_y)
    return out_y


dict_key = {
    -1: "Could not identify the key of the song",
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
dict_mode = {0: "Not identified", 1: "Major", 2: "Minor"}
dict_timesig = {3: "3/4", 4: "4/4", 5: "5/4", 6: "6/4", 7: "7/4"}

playlist_id = "https://open.spotify.com/playlist/3OQ7On2OadyIkyrlnLnBFJ?si=d1ca5bf75049481d"
track_list = spotify.playlist(playlist_id)
track_urls = []

for j in track_list["tracks"]["items"]:
    track_link = j["track"]["external_urls"]["spotify"]
    track_urls.append(track_link)

track_dict_list = []

for enum, track_id in enumerate(track_urls, 1):
    print(f"Working on track {enum}/{len(track_urls)}")
    audio_analysis = spotify.audio_analysis(track_id=track_id)

    time = []
    loudness = []
    for segment in audio_analysis["segments"]:
        time_start = segment["start"]
        time_max = segment["start"] + segment["loudness_max_time"]
        loudness_start = segment["loudness_start"]
        loudness_max = segment["loudness_max"]
        time.append(round(time_start + (time_max - time_start), 5))
        loudness.append(loudness_start + (loudness_max - loudness_start))

    loudness_smooth = get_baseline(loudness)
    loudness_smooth_list = loudness_smooth.tolist()
    loundess_smooth_fin = [round(x, 5) for x in loudness_smooth_list]

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
        "graph_seconds": time,
        "graph_loudness": loundess_smooth_fin,
    }
    track_dict_list.append(dict_transformed)

with open("track_info.json", "w") as f:
    json.dump(track_dict_list, f)
