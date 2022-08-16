"""
This file is responsible for connecting to the sqlite database and inserting/extracting data
Currently, only the Features table exists and is usable
"""


import sqlite3
from json_schema import features
from utilities import Logger


def get_features_db():
    """
    Connects to the spotify sqlite database file
    Returns:
        (Sqlite Connection) the database connection object
    """
    return sqlite3.connect('spotify.db')


def close_db(con):
    """
    Closes the sqlite database connection
    Args:
        con: (Sqlite Connection) the database connection object
    """
    con.close()


def create_features_table():
    """
    Creates the audio features table in the sqlite database
    Returns:
        (bool) True if the database was created correctly
    """
    con = get_features_db()
    cursor = con.cursor()
    cursor.execute("Create Table if not exists Features (danceability Real, energy Real, key Integer, loudness Real, " +
                   "mode Integer, speechiness Real, acousticness Real, instrumentalness Real, liveness Real, " +
                   "valence Real, tempo Real, type Varchar(32), id Varchar(32) UNIQUE, uri Varchar(64), " +
                   "track_href Varchar(64), analysis_url Varchar(64), duration_ms Integer, time_signature Integer)")
    return True


def save_audio_features_to_db(json_data):
    """
    Save audio feature data to the sqlite database
    Args:
        json_data: (dict) the audio feature data

    Returns:
        (int) how many rows were added. this should always be 1
    """
    assert json_data.keys() == features.keys(), "Supplied feature data doesn't match the expected keys from json_schema.features"
    con = get_features_db()
    cursor = con.cursor()
    empty = ", ".join(['?'] * len(features.keys()))
    split_data = tuple(json_data[key] for key in features.keys())
    cursor.execute(f"Insert or Ignore into Features values ({empty})", split_data)
    con.commit()
    rows = cursor.rowcount
    close_db(con)
    return rows


def get_audio_features(n=1):
    """
    Grab audio feature rows from the sqlite database
    Args:
        n: (int) how many rows to grab

    Returns:
        (list of audio feature dictionaries) the audio features grabbed
    """
    con = get_features_db()
    cursor = con.cursor()
    cursor.execute("Select * From Features")
    results = cursor.fetchmany(n)
    close_db(con)
    return [dict(zip(features.keys(), result)) for result in results]


if __name__ == "__main__":
    create_features_table()
    import spotify
    # save_audio_features_to_db(spotify.get_audio_features(spotify.find_song("Come With Me", "Will Sparks")[0].get("id", "")))
    all_features = get_audio_features(10000)
    Logger.write(all_features)
