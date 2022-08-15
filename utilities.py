import sqlite3
from json_schema import features


class LogLevel:
    Error = 0
    Info = 1
    Debug = 2


def get_features_db():
    return sqlite3.connect('spotify.db')


def close_db(con):
    con.close()


def create_features_table():
    con = get_features_db()
    cursor = con.cursor()
    cursor.execute('Create Table if not exists Features (name Text, course Text, roll Integer)')


def save_audio_features_to_db(json_data):
    assert json_data.keys() == features.keys(), "Supplied feature data doesn't match the expected keys from json_schema.features"
    con = get_features_db()
    cursor = con.cursor()
    empty = ", ".join(['?' * len(features.keys())])
    split_data = (json_data[key] for key in features.keys())
    cursor.execute(f"Insert into Features values ({empty})", split_data)
    con.commit()


class Logger:
    instance = None

    def __init__(self, log_level=LogLevel.Info):
        self.log_level = log_level
        Logger.instance = self

    def write(self, msg, level=LogLevel.Info):
        if level >= self.log_level:
            print(msg)

    @staticmethod
    def get_logger(level_if_empty=LogLevel.Info):
        if Logger.instance:
            return Logger.instance
        else:
            return Logger(level_if_empty)

# Global log
LOG = Logger(log_level=LogLevel.Info)


if __name__ == "__main__":
    create_features_table()
