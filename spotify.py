import requests


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
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    return headers


def get_audio_features(track_id):
    r = requests.get(f"{BASE_URL}audio-features/{track_id}", headers=build_access_headers())\
    features = r.json()
    print(r)
    return features


def get_artist_albums(artist_id):
    r = requests.get(BASE_URL + 'artists/' + artist_id + '/albums',
                     headers=build_access_headers(),
                     params={'include_groups': 'album', 'limit': 50})
    albums = r.json()
    print(albums)
    return albums


def get_album_tracks(album_id):
    r = requests.get(BASE_URL + 'albums/' + album_id + '/tracks',
                     headers=build_access_headers())
    tracks = r.json()#["items"]
    print(tracks)
    return tracks


if __name__ == "__main__":
    get_audio_features("651YhrvzeVfOa8yIifIhUM")
    get_artist_albums("36QJpDe2go2KgaRleHCDTp")
