"""
This file contains example data responses from spotify for comparing against
"""


features = {
    'danceability': 0.554,  # based on tempo, rhythm stability, beat strength, and overall regularity
    'energy': 0.966,  # represents intensity - based on dynamic range, loudness, timbre, onset rate, and general entropy
    'key': 6,  # -1 = No key, 0 = B♯/C, 1 = C♯/D♭, 2 = D, 3 = D♯/E♭, 4 = E, 5 = E♯/F, 6 = F♯/G♭, 7 = G, 8 = G♯/A♭, 9 = A, 10 = A♯/B♭ 11 = B/C♭
    'loudness': -3.745,  # decibel range typically range between -60 and 0 db.
    'mode': 1,  # major = 1, minor = 0
    'speechiness': 0.106,  # >0.66 probably entirely words, 0.33<value<0.66 contain both, <0.33 most likely music
    'acousticness': 0.00109,  # confidence that the track is acoustic
    'instrumentalness': 0.838,  # whether or not the track is primarily instrumental (non-vocal sounds)
    'liveness': 0.415,  # whether or not a track is live. >.8 is considered live
    'valence': 0.193,  # high valence songs are more positive, low valence songs are more negative
    'tempo': 132.035,  # BPM
    'type': 'audio_features',
    'id': '651YhrvzeVfOa8yIifIhUM',
    'uri': 'spotify:track:651YhrvzeVfOa8yIifIhUM',
    'track_href': 'https://api.spotify.com/v1/tracks/651YhrvzeVfOa8yIifIhUM',
    'analysis_url': 'https://api.spotify.com/v1/audio-analysis/651YhrvzeVfOa8yIifIhUM',
    'duration_ms': 225682,  # duration/60000 == minutes
    'time_signature': 4,
    "file_name": ""  # this is added by us
}


track_info = {
    'album': {
        'album_type': 'single',
        'artists': [
            {
                'external_urls': {
                    'spotify': 'https://open.spotify.com/artist/1u7OVFmWah4wQhOPIbUb8U'
                },
                'href': 'https://api.spotify.com/v1/artists/1u7OVFmWah4wQhOPIbUb8U',
                'id': '1u7OVFmWah4wQhOPIbUb8U',
                'name': 'Will Sparks',
                'type': 'artist',
                'uri': 'spotify:artist:1u7OVFmWah4wQhOPIbUb8U'
            }
        ],
        'external_urls': {
            'spotify': 'https://open.spotify.com/album/2zv3qPvu34uzmNJjSdjQ7E'
        },
        'href': 'https://api.spotify.com/v1/albums/2zv3qPvu34uzmNJjSdjQ7E',
        'id': '2zv3qPvu34uzmNJjSdjQ7E',
        'images': [
            {
                'height': 640,
                'url': 'https://i.scdn.co/image/ab67616d0000b27332b16b1912e9e61086c41dea',
                'width': 640
            },
            {
                'height': 300,
                'url': 'https://i.scdn.co/image/ab67616d00001e0232b16b1912e9e61086c41dea',
                'width': 300
            },
            {
                'height': 64,
                'url': 'https://i.scdn.co/image/ab67616d0000485132b16b1912e9e61086c41dea',
                'width': 64
            }
        ],
        'name': 'Come With Me',
        'release_date': '2022-08-12',
        'release_date_precision': 'day',
        'total_tracks': 1,
        'type': 'album',
        'uri': 'spotify:album:2zv3qPvu34uzmNJjSdjQ7E'
    },
    'artists': [
        {
            'external_urls': {
                'spotify': 'https://open.spotify.com/artist/1u7OVFmWah4wQhOPIbUb8U'
            },
            'href': 'https://api.spotify.com/v1/artists/1u7OVFmWah4wQhOPIbUb8U',
            'id': '1u7OVFmWah4wQhOPIbUb8U',
            'name': 'Will Sparks',
            'type': 'artist',
            'uri': 'spotify:artist:1u7OVFmWah4wQhOPIbUb8U'
        }
    ],
    'disc_number': 1,
    'duration_ms': 230909,
    'explicit': False,
    'external_ids': {
        'isrc': 'NLZ542201095'
    },
    'external_urls': {
        'spotify': 'https://open.spotify.com/track/1h1IERBZcsq6HVYbvLkmoT'
    },
    'href': 'https://api.spotify.com/v1/tracks/1h1IERBZcsq6HVYbvLkmoT',
    'id': '1h1IERBZcsq6HVYbvLkmoT',
    'is_local': False,
    'is_playable': True,
    'name': 'Come With Me',
    'popularity': 46,
    'preview_url': 'https://p.scdn.co/mp3-preview/8d9d9077367e6059349722f561f129a4ea17d876?cid=fbeba438f388448580065678175f42d5',
    'track_number': 1,
    'type': 'track',
    'uri': 'spotify:track:1h1IERBZcsq6HVYbvLkmoT'
}
