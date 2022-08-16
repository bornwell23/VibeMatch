"""
This file is responsible for connecting to the spotify.com rest api
It is used to request album, artist, and track information, with special focus on audio features and audio
It also provides a function for downloading mp3s via youtube from a spotify link
"""


import requests
import database
from utilities import Logger, LogLevel


CLIENT_ID = 'fbeba438f388448580065678175f42d5'
CLIENT_SECRET = '6dc5546c66b543caaf467bc89fe9738c'

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'


def get_access_token(client_id, secret):
    """
    Gets a spotify authorization token using id and secret token
    Args:
        client_id: (string) the spotify account's user name
        secret: (string) the spotify account's auth token

    Returns:
        (string) the api authorization token
    """
    auth_response = requests.post(AUTH_URL, {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': secret,
    })

    auth_response_data = auth_response.json()
    return auth_response_data['access_token']


def build_access_headers():
    """
    Gets an access token to use for subsequent requests using the client authentication function
    Returns:
        (dict) the header dict containing the authorization data
    """
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    return headers


def get_audio_features(track_id):
    """
    Gets audio feature data such as bpm, key, etc
    Args:
        track_id: (string) the track uri

    Returns:
        (dict) the json data of a track
    """
    assert isinstance(track_id, str) and len(track_id) == 22, f"Track id {track_id} is not the correct form"
    r = requests.get(f"{BASE_URL}audio-features/{track_id}", headers=build_access_headers())
    features = r.json()
    database.save_audio_features_to_db(features)  # automatically save all audio features obtained to the database
    Logger.write(r, LogLevel.Debug)
    return features


def get_audio_analysis(track_id):
    """
    Gets audio analysis data
    Args:
        track_id: (string) the track uri

    Returns:
        (dict) the json data of a track
    """
    assert isinstance(track_id, str) and len(track_id) == 22, f"Track id {track_id} is not the correct form"
    r = requests.get(f"{BASE_URL}audio-analysis/{track_id}",
                     params={"market": "US"},
                     headers=build_access_headers())
    analysis = r.json()
    Logger.write(r, LogLevel.Debug)
    return analysis


def get_multiple_audio_analysis(track_ids):
    """
    Gets audio analysis data
    Args:
        track_ids: (list of strings) the track uris

    Returns:
        (dict) the json data of a track
    """
    assert isinstance(track_ids, list), f"Track id list '{track_ids}' is not the correct form"
    r = requests.get(f"{BASE_URL}audio-analysis/{','.join(track_ids)}",
                     params={"market": "US"},
                     headers=build_access_headers())
    analysis = r.json()
    Logger.write(r, LogLevel.Debug)
    return analysis


def get_track_info(track_id):
    """
    Gets track info from an id
    Args:
        track_id: (string) the track uri

    Returns:
        (dict) the json data of a track
    """
    assert isinstance(track_id, str) and len(track_id) == 22, f"Track id {track_id} is not the correct form"
    r = requests.get(f"{BASE_URL}tracks/{track_id}",
                     params={"market": "US"},
                     headers=build_access_headers())
    analysis = r.json()
    Logger.write(r, LogLevel.Debug)
    return analysis


def get_track_name_from_feature(feature_json):
    """
    Gets a track's name from the audio feature data using the track id
    Args:
        feature_json: (dict) the audio feature data

    Returns:
        (string) the name of the track
    """
    return get_track_info(feature_json.get('id')).get('name')


def find_song(song_name=None, artist=None, album=None):
    """
    Get data for a song based on title and optionally artist and/or album
    Args:
        song_name: (string) name of the song
        artist:
        album:

    Returns:

    """
    songs = []
    offset = 0
    while not len(songs) and offset <= 1000:
        query = ""
        if song_name:
            query += f"{song_name}"
        if artist:
            query += f" {artist}"
        if album:
            query += f" {album}"
        r = requests.get(f"{BASE_URL}search",
                         params={'q': query, 'type': "track", "limit": 50, "offset": offset, "market": "US"},
                         headers=build_access_headers())
        songs = r.json().get("tracks", "tracks").get("items", "items")
        if not len(songs):
            Logger.write(f"Unable to find '{song_name}'", LogLevel.Error)
            return []
        if song_name:
            songs = [song for song in songs if song.get("name", "name") == song_name]
        if artist:
            songs = [song for song in songs if any(a.get("name", "name") == artist for a in song.get("artists", "artists"))]
        if album:
            songs = [song for song in songs if any(a.get("name", "name") == album for a in song.get("album", "album"))]
        offset += 50
    Logger.write(songs, LogLevel.Debug)
    return songs


def get_artist(artist_id):
    """
    Gets the artist data from an artist id
    Args:
        artist_id: (string) the artist uri

    Returns:
        (dict) the artist data
    """
    assert isinstance(artist_id, str) and len(artist_id) == 22, f"Artist id {artist_id} is not the correct form"
    r = requests.get(f"{BASE_URL}artists/{artist_id}",
                     params={'include_groups': 'album', 'limit': 1000, "market": "US"},
                     headers=build_access_headers())
    artist = r.json()
    Logger.write(artist)
    return artist


def get_related_artists(artist_id):
    """
    Gets the list of related artists from an artist id
    Args:
        artist_id: (string) the artist uri

    Returns:
        (dict) the related artist data
    """
    assert isinstance(artist_id, str) and len(artist_id) == 22, f"Artist id {artist_id} is not the correct form"
    r = requests.get(f"{BASE_URL}artists/{artist_id}/related-artists",
                     params={'include_groups': 'album', 'limit': 1000, "market": "US"},
                     headers=build_access_headers())
    albums = r.json()
    Logger.write(albums, LogLevel.Debug)
    return albums


def get_artist_albums(artist_id):
    """
    Gets the album data from an artist id
    Args:
        artist_id: (string) the artist uri

    Returns:
        (dict) the album data
    """
    assert isinstance(artist_id, str) and len(artist_id) == 22, f"Artist id {artist_id} is not the correct form"
    r = requests.get(f"{BASE_URL}artists/{artist_id}/albums",
                     params={'include_groups': 'album', 'limit': 50, "market": "US"},
                     headers=build_access_headers())
    albums = r.json()["items"]
    Logger.write(albums, LogLevel.Debug)
    return albums


def get_album_tracks(album_id):
    """
    Gets the track data from an album id
    Args:
        album_id: (string) the album uri

    Returns:
        (dict) the track data
    """
    assert isinstance(album_id, str) and len(album_id) == 22, f"Album id {album_id} is not the correct form"
    r = requests.get(f"{BASE_URL}albums/{album_id}/tracks",
                     params={"market": "US"},
                     headers=build_access_headers())
    tracks = r.json()["items"]
    Logger.write(tracks, LogLevel.Debug)
    return tracks


def get_track_recommendations_from_track(track_id, n=10, mixable=False):
    """
    Gets recommendations from a track id
    Args:
        track_id: (string) the track uri
        n: (int) how many tracks to get
        mixable: (bool) whether or not the tracks need to be mixable

    Returns:
        (list of track data dicts) the recommended tracks
    """
    from utilities import MixingSimilarityThresholds, SimilarityMaxValues, SimilarityMinValues
    assert isinstance(track_id, str) and len(track_id) == 22, f"Track id {track_id} is not the correct form"
    param_data = {"market": "US", "limit": n, "seed_tracks": track_id}
    if mixable:
        features = get_audio_features(track_id)
        param_data["max_key"] = min(features["key"] + MixingSimilarityThresholds.Keys, SimilarityMaxValues.Keys)
        param_data["min_key"] = max(features["key"] - MixingSimilarityThresholds.Keys, SimilarityMinValues.Keys)
        param_data["max_danceability"] = min(features["danceability"] + MixingSimilarityThresholds.Danceability, SimilarityMaxValues.Danceability)
        param_data["min_danceability"] = max(features["danceability"] - MixingSimilarityThresholds.Danceability, SimilarityMinValues.Danceability)
        param_data["max_energy"] = min(features["energy"] + MixingSimilarityThresholds.Energy, SimilarityMaxValues.Energy)
        param_data["min_energy"] = max(features["energy"] - MixingSimilarityThresholds.Energy, SimilarityMinValues.Energy)
        param_data["max_mode"] = min(features["mode"] + MixingSimilarityThresholds.Mode, SimilarityMaxValues.Mode)
        param_data["min_mode"] = max(features["mode"] - MixingSimilarityThresholds.Mode, SimilarityMinValues.Mode)
        param_data["max_time_signature"] = min(features["time_signature"] + MixingSimilarityThresholds.TimeSignature, SimilarityMaxValues.TimeSignature)
        param_data["min_time_signature"] = max(features["time_signature"] - MixingSimilarityThresholds.TimeSignature, SimilarityMinValues.TimeSignature)
        param_data["max_tempo"] = min(features["tempo"] + MixingSimilarityThresholds.Tempo, SimilarityMaxValues.Tempo)
        param_data["min_tempo"] = max(features["tempo"] - MixingSimilarityThresholds.Tempo, SimilarityMinValues.Tempo)
    r = requests.get(f"{BASE_URL}recommendations",
                     params=param_data,
                     headers=build_access_headers())
    json_data = r.json()
    tracks = json_data["tracks"]
    Logger.write(tracks, LogLevel.Debug)
    return tracks


def get_song_dl_object(url):
    """
    Converts the track url to a spotdl SongObject
    Args:
        url: (string) the open.spotify.com url for a track

    Returns:
        (SongObject) the song object that will be used by spotdl's downloader
    """
    from spotdl.search import song_gatherer
    try:
        return song_gatherer.from_spotify_url(url)
    except Exception as convert_error:
        error_str = f"{convert_error}"
        if "already downloaded" in f"{convert_error}":
            song_name = error_str[:error_str.find('already downloaded')]
            Logger.write(f"Can't download '{song_name}' because it's already downloaded", LogLevel.Info)
            return None
        else:
            raise convert_error


def extract_song_url(track_data):
    """
    Gets the open.spotify.com url for a given song, with any track information
    Args:
        track_data: (any) the dict or string containing the url/uri

    Returns:
        (string) the open.spotify.com url for the track
    """
    if isinstance(track_data, dict):
        if "external_urls" in track_data:  # track object
            return track_data["external_urls"]["spotify"]
        elif "danceability" in track_data:  # audio features
            return get_track_info(track_data["uri"])["external_urls"]["spotify"]
    elif isinstance(track_data, str):
        if "open." in track_data:  # url
            return track_data
        elif len(track_data) == 22 and track_data.isalnum():  # uri
            return get_track_info(track_data)["external_urls"]["spotify"]


def download_songs(track_data):
    """
    Downloads song(s) from uris, track objects, or urls
    Args:
        track_data: (any) one or more spotify-mapping data points to get song from
    """
    import os
    from spotdl.download.downloader import DownloadManager
    from spotdl.console import SpotifyClient

    SpotifyClient.init(CLIENT_ID, CLIENT_SECRET, False)
    if not os.path.exists("songs"):
        os.mkdir("songs")
    d = DownloadManager({"download_threads": 4, "path_template": os.path.join(os.getcwd(), "songs/{artist} - {title}.{ext}")})
    if not isinstance(track_data, list):
        track_data = [track_data]
    to_download = []
    for song in track_data:
        song_obj = get_song_dl_object(extract_song_url(song))
        if song_obj:
            to_download.append(song_obj)
    if len(to_download):
        d.download_multiple_songs(to_download)
    else:
        Logger.write("No songs to download. Are they already downloaded? or perhaps don't exist?", LogLevel.Error)


def get_features_of_associated_songs(track_id, n=100, layers=0, mixable=False, download=False):
    tracks = get_track_recommendations_from_track(track_id)
    if not len(tracks):
        Logger.write("Unable to find any recommended songs", LogLevel.Error)
        return
    associated_features = []
    for track in tracks:
        if layers:
            associated_features += get_features_of_associated_songs(track["id"], n=n, layers=layers-1, mixable=mixable, download=download)
        associated_features.append(get_audio_features(track["id"]))
    if download:
        download_songs(", ".join([track["id"] for track in tracks]))
    return associated_features


if __name__ == "__main__":
    Logger.set_log_level(LogLevel.Info)
    # come_with_me = find_song(song_name="Come With Me", artist="Will Sparks")[0]
    # download_songs(come_with_me)
    # get_audio_features("651YhrvzeVfOa8yIifIhUM")
    recommendations = get_track_recommendations_from_track("651YhrvzeVfOa8yIifIhUM", n=100, mixable=False)
    feature_data = get_features_of_associated_songs("651YhrvzeVfOa8yIifIhUM", n=10, mixable=True)
    # albums = get_artist_albums("36QJpDe2go2KgaRleHCDTp")
    # for album in albums:
    #     get_album_tracks(album.get("id"))
    #
    Logger.write("Done")
