"""
This file is responsible for connecting to the spotify.com rest api
It is used to request album, artist, and track information, with special focus on audio features and audio
It also provides a function for downloading mp3s via youtube from a spotify link
"""


import math
import os
import requests
import time
try:
    from database import FeaturesDatabase
    from utilities import Logger, LogLevel, MixingSimilarityThresholds, SimilarityMaxValues, \
        SimilarityMinValues, FolderDefinitions, get_song_path, get_path_template
except:
    from VibeMatch.database import FeaturesDatabase
    from VibeMatch.utilities import Logger, LogLevel, MixingSimilarityThresholds, SimilarityMaxValues, \
        SimilarityMinValues, FolderDefinitions, get_song_path, get_path_template
try:
    from spotdl.search import SpotifyClient
    from spotdl.search.song_gatherer import from_spotify_url as song_from_url
except:
    from spotdl.utils.spotify import SpotifyClient
    from spotdl.utils.web import song_from_url as song_from_url


assert os.path.exists(".env"), "Please create a '.env' file with CLIENT_ID='your spotify api id'\nCLIENT_SECRET='your spotify api key' to use spotify functionality"
CLIENT_ID, CLIENT_SECRET = (line.split('=')[1].replace('\'', '').replace('\n', '').replace('"', '').strip() for line in open(".env").readlines())

AUTH_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'


class SpotifyClientWrapper:
    _instance = None

    @staticmethod
    def get_client():
        if SpotifyClientWrapper._instance:
            return SpotifyClientWrapper._instance
        else:
            SpotifyClientWrapper._instance = SpotifyClient.init(CLIENT_ID, CLIENT_SECRET, False)
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


def get_audio_features(track_id, custom_folder=None):
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
    tracks = r.json()["items"]
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
    else:
        # kmeans clustering?
        pass
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
    
    try:
        return song_from_url(url)
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
    import os
    from spotdl.download.downloader import DownloadManager
    SpotifyClientWrapper.get_client()

    folder = custom_folder if custom_folder else FolderDefinitions.Songs
    os.makedirs(folder, exist_ok=True)
    path_template = get_path_template(folder)
    d = DownloadManager({"download_threads": 4,
                         "path_template": path_template,
                         "output_format": "m4a"})
    if not isinstance(track_data, list):
        track_data = [track_data]
    to_download = []
    features = None
    for song in track_data:
        url = extract_song_url(song)
        tid = get_id_from_url(url)
        try:
            song_obj = get_song_dl_object(url)
            if song_obj:
                try:
                    features = get_audio_features(tid, custom_folder)
                    to_download.append(song_obj)
                except Exception as e:
                    Logger.write(f"Unable to download {tid}: {e}")
        except Exception as obj_e:
            Logger.write(f"Unable to download {tid}: {obj_e}")
    if len(to_download):
        Logger.write(f"Downloading {len(to_download)} songs")
        d.download_multiple_songs(to_download)
        Logger.write(f"Downloaded {len(to_download)} songs")
        # while len(d.download_tracker.get_song_list()):
        #     time.sleep(1)
        return d, features["file_name"] if features else None
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
            associated_features.append(get_audio_features(track["id"], custom_folder=custom_folder))
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
        Logger.write("Unable to find any songs", LogLevel.Error)
        return
    features = []
    for track in tracks:
        try:
            features.append(get_audio_features(track["track"]["id"], custom_folder))
        except Exception as e:
            Logger.write(f"Unable to get data for {track['track']['id']}: {e}")
    if download:
        d, path = download_songs([track["track"]["id"] for track in tracks], custom_folder)
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
    if not len(tracks):
        Logger.write("Unable to find any songs", LogLevel.Error)
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
        Logger.write("Unable to find any songs", LogLevel.Error)
        return
    features = []
    for track in tracks:
        try:
            features.append(get_audio_features(track["track"]["id"], custom_folder))
        except Exception as e:
            Logger.write(f"Unable to get data for {track['track']['id']}: {e}")
    if download:
        d, path = download_songs([track["track"]["id"] for track in tracks], custom_folder)
    return d, path, features


def download(info, download=True, custom_folder=None):
    if type(info) is str:
        if "playlist" in info:
            d, path, features = download_playlist(info, download=download, custom_folder=custom_folder)
        elif "artist" in info:
            d, path = download_artist(info, download=download, custom_folder=custom_folder)
        elif "album" in info:
            d, path = download_album(info, download=download, custom_folder=custom_folder)
        else:
            d, path = download_songs(info, custom_folder=custom_folder)
    elif type(info) is list:
        for i in info:
            d, path = download(i, download, custom_folder)
    else:
        return None, None
    return d, path


def build_library_from_track(track_id, min_tracks=1, max_tracks=1000, mixable=False, download=False, custom_folder=None):
    to_obtain = min(max_tracks, 100)  # at most, 100 at a time
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
    # come_with_me = find_song(song_name="Come With Me", artist="Will Sparks")[0]
    # download_songs(come_with_me)
    # get_audio_features("651YhrvzeVfOa8yIifIhUM")
    # url_locs = [
                # ("https://open.spotify.com/track/4tuWS8iuaCr0o7rH81bVIo?si=47b8cc3848074098", "songs/fast"),  # HARD by will sparks
                # ("https://open.spotify.com/track/1V6KX61KpHJ9Z4mtGeroUO?si=4a27df9f926649db", "songs/psy"),  # Move by Alchimyst
                # ("https://open.spotify.com/track/7Kqqg2agWjcT0nBVpzqA4B?si=a723a50d2fcf456a", "songs/midtempo"),  # Illusion by Zabo
                # ("https://open.spotify.com/track/0i8cq68GTNkpkMW4lnOTcf?si=c26cedaf1dc04099", "songs/dubstep"),  # Shake the ground by Snails
                # ("https://open.spotify.com/track/0m29SeY8I7rC4iSyWkvFsZ?si=9514c3329b004be8", "songs/fast"),  # Raw Diamonds by Maddix
                # ("https://open.spotify.com/track/4XzeThE3txvCBIrP40tj85?si=c36ac83a295a498b", "songs/progressive"),  # Eternity by Anyma
                # ("https://open.spotify.com/track/06kSBWCsizE75Z2h4yjVPM?si=192366f044e143dc", "songs/hardstyle"),  # Children of Drums by Wildstylez
                # ("https://open.spotify.com/track/1AETcaoFdjSoeTUaPQmY7V?si=0f1266cba62c4986", "songs/hard_trance"),  # All Systems Go by Shugz
                # ("https://open.spotify.com/track/2ihfEczzOpZXd8krs60UDx?si=06c70bcd3cab41ba", "songs/techno"),  # Electric by Maddix
                # ("https://open.spotify.com/track/0ygoI3HcoGScxt879A23Uk?si=48c2e439f4854435", "songs/classics"), # Don't Stop by ATB
                # ("https://open.spotify.com/track/6ZjF7ecMawDKpbMTfo5p46?si=85a598be7b1647f1", "songs/dnb")
    #             ]  # bruises by fox stevenson
    # tracks_downloaded = []  # tracks_downloaded
    # for url, loc in url_locs:
    #     tracks_downloaded.extend(build_library_from_track(get_id_from_url(url), min_tracks=25, max_tracks=50, mixable=False, download=True, custom_folder=loc))
    # Logger.write(f"Downloaded {len(tracks_downloaded)} recommended songs")
    # recommendations = get_track_recommendations_from_track(get_track_id_from_url(url), n=100, mixable=False)
    # feature_data = get_features_of_associated_songs("651YhrvzeVfOa8yIifIhUM", n=10, mixable=True)
    # albums = get_artist_albums("36QJpDe2go2KgaRleHCDTp")
    # for album in albums:
    #     get_album_tracks(album.get("id"))
    #
    # playlist_url = "https://open.spotify.com/playlist/559WNzUJnAwrzKoP4vimMr"  # Detour playlist
    # playlists = [
    #              ("https://open.spotify.com/playlist/30P1IBWC4dc8AeNlgOvCoJ?si=160736d207094c8e", "songs/hard_trance"),
    #              ("https://open.spotify.com/playlist/1Ax0Z8A7inGiCiattYrs1M?si=ec2a6430d2bd41f1", "songs/hardstyle"),
    #              ("https://open.spotify.com/playlist/37i9dQZF1E8Prt0GBY4t1y?si=0df4ad3458a5477b", "songs/techno"),
    #              ("https://open.spotify.com/playlist/2ajM8UMVYv1frggvkosa1I?si=4b21b870cd544ee1", "songs/5_26"),
    #              ("https://open.spotify.com/playlist/7c5U13jj8OL1VP1H42fuOp?si=ea2090c8485f42ef", "songs/psy"),
    #              ("https://open.spotify.com/playlist/37i9dQZF1E8KGA8RTy3liG?si=84364480a08a4989", "songs/dnb")
    #              ]
    # for playlist in playlists:
    #     tracks = download_playlist(playlist[0], download=True, custom_folder=playlist[1])
    #     tracks_downloaded.extend(tracks)
    #     tracks_downloaded.extend(build_library_from_track(random.choice(tracks)["id"], min_tracks=1, max_tracks=25, mixable=True, download=True, custom_folder=playlist[1]))
    # print(f"Downloaded {len(tracks_downloaded)} sons from playlists: ", [track["file_name"] for track in tracks_downloaded])
    # url = "https://open.spotify.com/track/6DDNTyRl29jQMSmRKQ7PN5?si=1a5eed16ad4241fe"
    # get_id_from_url(url)
    # id = get_id_from_url(url)
    # get_audio_features(id)
    # download_songs([id], custom_folder="songs/detour")
    # Logger.write("Done")
    # time.sleep(5)