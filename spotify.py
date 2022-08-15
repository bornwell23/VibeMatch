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


if __name__ == "__main__":
    find_song(song_name="Come With Me", artist="Will Sparks")
    get_audio_features("651YhrvzeVfOa8yIifIhUM")
    albums = get_artist_albums("36QJpDe2go2KgaRleHCDTp")
    for album in albums:
        get_album_tracks(album.get("id"))
