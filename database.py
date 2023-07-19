"""
This file is responsible for connecting to the sqlite database and inserting/extracting data
Currently, only the Features table exists and is usable
"""


import sqlite3
try:
    from json_schema import features
    from utilities import Logger
except:
    from VibeMatch.json_schema import features
    from VibeMatch.utilities import Logger


class FeaturesDatabase:
    _instance = None

    @staticmethod
    def get_instance():
        if FeaturesDatabase._instance:
            return FeaturesDatabase._instance
        else:
            FeaturesDatabase._instance = FeaturesDatabase()
            return FeaturesDatabase._instance

    def __init__(self):
        if FeaturesDatabase._instance:
            Logger.write("Features database wrapper already exists")
        else:
            self.con = self.get_features_db()
            self.created = False
            self.create_features_table()

    def get_features_db(self):
        """
        Connects to the spotify sqlite database file
        Returns:
            (Sqlite Connection) the database connection object
        """
        self.con = sqlite3.connect('spotify.db')
        return self.con

    def close_db(self):
        """
        Closes the sqlite database connection
        """
        self.con.close()

    def create_features_table(self):
        """
        Creates the audio features table in the sqlite database
        Returns:
            (bool) True if the database was created correctly
        """
        if self.created:
            return self.created
        cursor = self.con.cursor()
        cursor.execute("Create Table if not exists Features (danceability Real, energy Real, key Integer, loudness Real, " +
                       "mode Integer, speechiness Real, acousticness Real, instrumentalness Real, liveness Real, " +
                       "valence Real, tempo Real, type Varchar(32), id Varchar(32) UNIQUE, uri Varchar(64), " +
                       "track_href Varchar(64), analysis_url Varchar(64), duration_ms Integer, time_signature Integer, file_name VarChar(128))")
        self.created = True
        return self.created

    def save_audio_features_to_db(self, json_data):
        """
        Save audio feature data to the sqlite database
        Args:
            json_data: (dict) the audio feature data

        Returns:
            (int) how many rows were added. this should always be 1
        """
        assert json_data.keys() == features.keys(), "Supplied feature data doesn't match the expected keys from json_schema.features"
        cursor = self.con.cursor()
        empty = ", ".join(['?'] * len(features.keys()))
        split_data = tuple(json_data[key] for key in features.keys())
        cursor.execute(f"Insert or Ignore into Features values ({empty})", split_data)
        self.con.commit()
        rows = cursor.rowcount
        return rows

    def get_features_from_file_name(self, file_name):
        """
        Grabs audio features where the file name matches
        Args:
            file_name: (string) file name of the song - should match the output from utilities.get_song_path

        Returns:
            (dict|None) the audio features else None
        """
        cursor = self.con.cursor()
        cursor.execute(f"Select * From Features where file_name='{file_name}'")
        results = cursor.fetchone()
        if isinstance(results, tuple):
            return dict(zip(features.keys(), results))
        else:
            return None

    def get_audio_features(self, n=1):
        """
        Grab audio feature rows from the sqlite database
        Args:
            n: (int) how many rows to grab

        Returns:
            (list of audio feature dictionaries) the audio features grabbed
        """
        cursor = self.con.cursor()
        cursor.execute("Select * From Features")
        results = cursor.fetchmany(n)
        if isinstance(results, list) and len(results) > 0 and isinstance(results[0], tuple):
            return [dict(zip(features.keys(), result)) for result in results]
        else:
            return None


if __name__ == "__main__":
    FeaturesDatabase.get_instance().create_features_table()
    import spotify
    #FeaturesDatabase.get_instance().save_audio_features_to_db(spotify.get_audio_features(spotify.find_song("Come With Me", "Will Sparks")[0].get("id", "")))
    all_features = FeaturesDatabase.get_instance().get_audio_features(10000)
    Logger.write(f"{len(all_features)} features: {all_features}")
    # file_names = sorted([f["file_name"] for f in all_features])
    # detour_features = [features for features in all_features if features["file_name"].startswith("songs/detour")]
    # Logger.write(f"Detour: {len(detour_features)} features: {detour_features}")
