"""
This file is responsible for connecting to the spotify.com rest api
It is used to request album, artist, and track information, with special focus on audio features and audio analysis.
It also provides functions for downloading mp3s via youtube from a spotify link.

Note: This module requires spotdl version 4.2.10. This version is pinned in requirements.txt to ensure compatibility.
Other versions may not work due to API changes.

Dependencies:
    - spotdl==4.2.10
    - python-dotenv (for reading .env file)
    - requests (for making HTTP requests)

Environment Variables:
    - CLIENT_ID: Spotify API client ID
    - CLIENT_SECRET: Spotify API client secret
"""


import math
import os
from pathlib import Path
from pydub import AudioSegment
import requests
import time
try:
    from database import FeaturesDatabase
    from utilities import Logger, LogLevel, MixingSimilarityThresholds, Settings, SimilarityMaxValues, \
        SimilarityMinValues, FolderDefinitions, get_song_path, get_path_template, FileFormats
except:
    from VibeMatch.database import FeaturesDatabase
    from VibeMatch.utilities import Logger, LogLevel, MixingSimilarityThresholds, Settings, SimilarityMaxValues, \
        SimilarityMinValues, FolderDefinitions, get_song_path, get_path_template, FileFormats
from spotdl.download.downloader import Downloader, DownloaderError
from spotdl.console.download import download
from spotdl.types.options import DownloaderOptions
from spotdl.utils.spotify import SpotifyClient, SpotifyError

assert os.path.exists(".env"), "Please create a '.env' file with CLIENT_ID='your spotify api id'\nCLIENT_SECRET='your spotify api key' to use spotify functionality"
CLIENT_ID, CLIENT_SECRET = (line.split('=')[1].replace('\'', '').replace('\n', '').replace('"', '').strip() for line in open(".env").readlines()[0:2])

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'


class SpotifyClientWrapper:
    _instance = None

    @staticmethod
    def get_client():
        if SpotifyClientWrapper._instance:
            return SpotifyClientWrapper._instance
        else:
            SpotifyClientWrapper._instance = SpotifyClient.init(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_auth=False, headless=True)
            return SpotifyClientWrapper._instance


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


def get_track_audio_features(track_id, custom_folder=None):
    """
    Gets audio feature data such as bpm, key, etc
    Args:
        track_id: (string) the track uri
        custom_folder: (string) a folder other than songs/

    Returns:
        (dict) the json data of a track
    """
    assert isinstance(track_id, str) and len(track_id) == 22, f"Track id {track_id} is not the correct form"
    r = requests.get(f"{BASE_URL}audio-features/{track_id}", headers=build_access_headers())
    features = r.json()
    info = get_track_info(track_id)
    features["file_name"] = get_song_path(info, custom_folder)
    FeaturesDatabase.get_instance().save_audio_features_to_db(features)  # automatically save all audio features obtained to the database
    Logger.write(r, LogLevel.Debug)
    return features


def get_multiple_audio_features(track_ids, custom_folder=None):
    """
    Gets audio feature data such as bpm, key, etc

    Args:
        track_ids (_type_): _description_
        custom_folder (_type_, optional): _description_. Defaults to None.
    """
    assert isinstance(track_ids, list), f"Track id list '{track_ids}' is not the correct form"
    r = requests.get(f"{BASE_URL}audio-features/{','.join(track_ids)}", headers=build_access_headers())
    features = r.json()
    for feature in features["audio_features"]:
        info = get_track_info(feature["id"])
        feature["file_name"] = get_song_path(info, custom_folder)
        FeaturesDatabase.get_instance().save_audio_features_to_db(feature)  # automatically save all audio features obtained to the database
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


def get_id_from_url(url):
    """
    Gets the id from a url
    Args:
        url:

    Returns:

    """
    assert "open." in url, "Url provided is not a correct spotify link"
    end = url.find('?')
    if end == -1:
        end = len(url)
    if "track" in url:
        id = url[url.find("track/")+6:end]
    elif "playlist" in url:
        id = url[url.find("playlist/")+6:end]
    elif "album" in url:
        id = url[url.find("album/")+6:end]
    elif "artist" in url:
        id = url[url.find("artist/")+6:end]
    return id


def get_id_from_url(url:str):
    """
    Gets the id from a url
    Args:
        url: (string) the open.spotify.com url e.g. https://open.spotify.com/track/4tuWS8iuaCr0o7rH81bVIo?si=47b8cc3848074098

    Returns:
        (string): the uri e.g. 4tuWS8iuaCr0o7rH81bVIo
    """
    if len(url) == 22:
        assert url.isalnum(), "Url/Uri doesn't meet requirements, should be a 22 character alphanumeric string"
        return url  # already in uri format
    assert "open." in url, "Url provided is not a correct spotify link"
    end = url.find('?')
    if end == -1:
        end = len(url)
    return url[url.rfind("/")+1:end]


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


def find_song(song_name:str=None, artist:str=None, album:str=None):
    """
    Get data for a song based on title and optionally artist and/or album
    Args:
        song_name: (string) name of the song
        artist: (string) artist of the song
        album: (string) album of the song

    Returns:
        (list) list of track data
    """
    found = []
    songs = []
    offset = 0
    qtype = "track"
    while not len(songs) and offset <= 1000:
        query = ""
        if song_name:
            song_name = song_name.strip()
            query += f"{song_name}"
        elif album:
            qtype = "album"
        elif artist:
            qtype = "artist"
        if artist:
            artist = artist.strip()
            query += f" {artist}"
        if album:
            album = album.strip()
            query += f" {album}"
        r = requests.get(f"{BASE_URL}search",
                         params={'q': query, 'type': qtype, "limit": 50, "offset": offset, "market": "US"},
                         headers=build_access_headers())
        songs = r.json() 
        if qtype == "track":
            songs = songs.get("tracks", {}).get("items", [])
        elif qtype == "album":
            songs = songs.get("albums", {})[0]
        elif qtype == "artists":
            songs = songs.get("artists", {})[0]
        if not len(songs):
            if not len(found):
                Logger.write(f"Unable to find '{song_name}'", LogLevel.Error)
                return []
        else:
            if song_name:
                songs = [song for song in songs if song.get("name", "n/a").lower() == song_name.lower()]
            if artist:
                songs = [song for song in songs if any(a.get("name", "n/a").lower() == artist.lower() for a in song.get("artists", "artists"))]
            if album:
                songs = [song for song in songs if song.get("album", {}).get("name", "n/a").lower() == album.lower()]
            found.extend(songs)
            offset += 50
    Logger.write(songs, LogLevel.Debug)
    return found


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


def get_playlist_tracks(playlist):
    """
    Gets the track data from a playlist
    Args:
        playlist: (string) the playlist uri

    Returns:
        (dict) the track data
    """
    assert isinstance(playlist, str) and len(playlist) == 22, f"Album id {playlist} is not the correct form"
    r = requests.get(f"{BASE_URL}playlists/{playlist}/tracks",
                     params={"market": "US"},
                     headers=build_access_headers())
    json_data = r.json()
    tracks = []
    tracks.extend(json_data["items"])
    while json_data.get("next", None):
        r = requests.get(json_data["next"], headers=build_access_headers())
        json_data = r.json()
        tracks.extend(json_data["items"])
    Logger.write(tracks, LogLevel.Debug)
    return tracks


def get_track_recommendations_from_track(track_id, n=10, need_mixable=False, query_api=True):
    """
    Gets recommendations from a track id
    Args:
        track_id: (string) the track uri
        n: (int) how many tracks to get
        need_mixable: (bool) whether or not the tracks need to be mixable

    Returns:
        (list of track data dicts) the recommended tracks
    """
    assert isinstance(track_id, str) and len(track_id) == 22, f"Track id {track_id} is not the correct form"
    param_data = {"market": "US", "limit": n, "seed_tracks": track_id}
    if query_api:
        if need_mixable:
            features = get_track_audio_features(track_id)
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
    else:
        # kmeans clustering?
        pass
    tracks = json_data["tracks"]
    Logger.write(tracks, LogLevel.Debug)
    return tracks


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


def download_songs(track_data, custom_folder=None):
    """
    Downloads song(s) from uris, track objects, or urls
    Also gets audio features, and saves track id to features db for reference
    Args:
        track_data: (any) one or more spotify-mapping data points to get song from
        custom_folder: (string) a folder other than songs/
    Returns:
        tuple: (DownloadManager, str) the download manager to determine if songs are done and the last path used
    """
    spotify_client = SpotifyClientWrapper.get_client()
    folder = custom_folder if custom_folder else FolderDefinitions.Songs
    os.makedirs(folder, exist_ok=True)
    downloader_options = DownloaderOptions(
        format=FileFormats.M4a,
        output=get_path_template(folder),
        bitrate=Settings.Bitrate,
    )
    downloader = Downloader(downloader_options)
    if not isinstance(track_data, list):
        track_data = [track_data]
    to_download = []
    features = None
    for song in track_data:
        url = extract_song_url(song)
        tid = get_id_from_url(url)
        try:
            try:
                if Settings.GetFeatures:
                    features = get_track_audio_features(tid, custom_folder)
                to_download.append(url)
            except Exception as e:
                Logger.write(f"Unable to download {tid}: {e}")
        except Exception as obj_e:
            Logger.write(f"Unable to download {tid}: {obj_e}")
    if len(to_download):
        Logger.write(f"Downloading {len(to_download)} songs")
        download(query=to_download, downloader=downloader)
        Logger.write(f"Downloaded {len(to_download)} songs")
        # while len(d.download_tracker.get_song_list()):
        #     time.sleep(1)
        return downloader, folder
    else:
        Logger.write("No songs to download. Are they already downloaded? or perhaps don't exist?", LogLevel.Error)


def get_features_of_associated_songs(track_id, n=100, layers=0, mixable=False, download=False, custom_folder=None):
    """
    Gets audio features from songs associated to the provided track
    This function can be called recursively
    This function can optionally download the songs as well
    It is primarily intended for mass-scale audio scraping in preparation for larger testing
    Args:
        track_id: (string) a track uri
        n: (int) number of songs to get
        layers: (int) how many recursion layers to traverse
        mixable: (bool) whether or not the music needs to be mixable
        download: (bool) whether or not to download the files
        custom_folder: (string) a folder other than songs/

    Returns:
        (list of dicts) the list of audio features from the tracks found
    """
    tracks = get_track_recommendations_from_track(track_id, n, need_mixable=mixable)
    if not len(tracks):
        Logger.write("Unable to find any recommended songs", LogLevel.Error)
        return
    associated_features = []
    for track in tracks:
        if layers:
            associated_features += get_features_of_associated_songs(track["id"], n=n, layers=layers-1, mixable=mixable, download=download, custom_folder=custom_folder)
        try:
            associated_features.append(get_track_audio_features(track["id"], custom_folder=custom_folder))
        except Exception as e:
            Logger.write(f"Unable to get data for {track['id']}: {e}")
    if download:
        download_songs([track["id"] for track in tracks], custom_folder)
    return associated_features


def download_playlist(playlist:str, download=True, custom_folder=None):
    """
    Downloads a whole playlist
    Args:
        playlist: (str) the playlist uri or url
        download: (bool) whether or not to download the files
        custom_folder: (string) a folder other than songs/
    Returns:
        (DownloadManager object) the DownloadManager used to get the tracks
        (str) path used to download, to show user where files went
        (list of dicts) the list of audio features from the tracks found
    """
    tracks = get_playlist_tracks(get_id_from_url(playlist))
    if not len(tracks):
        Logger.write("Unable to find any songs from playlist", LogLevel.Error)
        return
    features = []
    to_download = []
    for track in tracks:
        track = track["track"]
        try:                
            track["file_name"] = get_song_path(track, custom_folder)
            if not os.path.exists(track["file_name"]):
                to_download.append(track)
            else:
                Logger.write(f"Skipping {track['name']} - {track['artists'][0]['name']}")
        except Exception as e:
            Logger.write(f"Unable to get data for {track['id']}: {e}")
    if Settings.GetFeatures:
        track_features = get_multiple_audio_features([track["id"] for track in tracks], custom_folder)
        features.extend(track_features)
    if download:
        Logger.write(f"Skipping {len(tracks) - len(to_download)} songs")
        d, path = download_songs(to_download, custom_folder)
    return d, path, features


def download_artist(artist:str, download=True, custom_folder=None):
    """
    Downloads an artists discography
    Args:
        artist: (str) the artist uri or url
        download: (bool) whether or not to download the files
        custom_folder: (string) a folder other than songs/
    Returns:
        (list of DownloadManager objects) the list of DownloadManagers used to get the albums
        (str) path used to download, to show user where files went
        (list of dicts) the list of audio features from the tracks found
    """
    albums = get_artist_albums(get_id_from_url(artist))
    if not len(albums):
        Logger.write("Unable to find any songs from artist", LogLevel.Error)
        return
    features = []
    downloaders = []
    for album in albums:
        d, path, featureset = download_album(album["id"], download=download, custom_folder=custom_folder)
        features.extend(featureset)
        downloaders.extend(d)
    return downloaders, path, features


def download_album(album:str, download=True, custom_folder=None):
    """
    Downloads a whole album
    Args:
        album: (str) the album uri or url
        download: (bool) whether or not to download the files
        custom_folder: (string) a folder other than songs/
    Returns:
        (DownloadManager object) the DownloadManager used to get the album
        (str) path used to download, to show user where files went
        (list of dicts) the list of audio features from the tracks found
    """
    tracks = get_album_tracks(get_id_from_url(album))
    if not len(tracks):
        Logger.write("Unable to find any songs from album", LogLevel.Error)
        return
    features = []
    for track in tracks:
        try:
            features.append(get_track_audio_features(track["track"]["id"], custom_folder))
        except Exception as e:
            Logger.write(f"Unable to get data for {track['track']['id']}: {e}")
    if download:
        d, path = download_songs([track["track"]["id"] for track in tracks], custom_folder)
    return d, path, features


def download_music(info, download=True, custom_folder=None):
    if type(info) is str:
        if "playlist" in info:
            d, path, features = download_playlist(info, download=download, custom_folder=custom_folder)
        elif "artist" in info:
            d, path, features = download_artist(info, download=download, custom_folder=custom_folder)
        elif "album" in info:
            d, path, features = download_album(info, download=download, custom_folder=custom_folder)
        else:
            d, path = download_songs(info, custom_folder=custom_folder)
    elif type(info) is list:
        for i in info:
            d, path = download_music(i, download, custom_folder)
    else:
        return None, None
    return d, path


def download_or_open(song) -> tuple[AudioSegment, str]:
    if "https:" in song or ".com/" in song:
        d, path = download_music(song)
    else:
        path = f"{FolderDefinitions.Songs}/{song}"
    return AudioSegment.from_file(path), path


def build_library_from_track(track_id, min_tracks=1, max_tracks=1000, mixable=False, download=False, custom_folder=None):
    to_obtain = min(max_tracks, 1000)  # at most, 100 at a time
    layers = max(math.floor(math.sqrt(max_tracks) / to_obtain) - 1, 0)  # at least 0 layers
    obtained = 0
    recommendations = []
    while obtained + to_obtain**layers <= max_tracks:
        recommendations = get_features_of_associated_songs(track_id, n=to_obtain, layers=layers, mixable=mixable, download=download, custom_folder=custom_folder)
        obtained += len(recommendations)
    if obtained < min_tracks:
        catch_up_recommendations = get_features_of_associated_songs(track_id, n=min_tracks-obtained, layers=0, mixable=mixable,
                                                           download=download, custom_folder=custom_folder)
        obtained += len(catch_up_recommendations)
        recommendations.extend(catch_up_recommendations)
    return recommendations


if __name__ == "__main__":
    Logger.set_log_level(LogLevel.Info)
    start = time.perf_counter()

    # to_download = find_song(song_name="YOUR SONG NAME", artist="THE ARTIST")[0]
    # download_songs(to_download)

    # get_audio_features("SPOTIFY URI HERE")

    # url_locs = [
                # ("https://open.spotify.com/track/YOUR_SONG_URI", "songs/GENRE"),  # a representative song

    #             ]
    # tracks_downloaded = []  # tracks_downloaded
    # for url, loc in url_locs:
    #     tracks_downloaded.extend(build_library_from_track(get_id_from_url(url), min_tracks=25, max_tracks=50, mixable=False, download=True, custom_folder=loc))
    # Logger.write(f"Downloaded {len(tracks_downloaded)} recommended songs")


    url = "https://open.spotify.com/playlist/YOUR SONG URI HERE"
    download_music(url, download=True, custom_folder="songs/YOUR_PLAYLIST_NAME")

    # from utilities import convert_directory_m4a_to_mp3
    # convert_directory_m4a_to_mp3(r"C:\YOUR_PATH_HERE_CONTAINING_M4A_FILES")

    # playlists = [
    #              ("https://open.spotify.com/playlist/YOUR_PLAYLIST_URI_HERE", "songs/YOUR_PLAYLIST_NAME"),
    #              ]
    # for playlist in playlists:
    #     tracks = download_playlist(playlist[0], download=True, custom_folder=playlist[1])
    #     tracks_downloaded.extend(tracks)
    #     tracks_downloaded.extend(build_library_from_track(random.choice(tracks)["id"], min_tracks=1, max_tracks=25, mixable=True, download=True, custom_folder=playlist[1]))


    end = time.perf_counter()
    Logger.write(f"Finished in {end-start} seconds", LogLevel.Info)