"""
This file is a general-purpose file for various functionality that is not directly tied to a feature
Primarily this contains logging and documentation utilities
"""


class Notes(dict):
    __dict__ = dict()
    A = 9
    __dict__["A"] = 9
    Aflat = 8
    __dict__["Aflat"] = 8
    Asharp = 10
    __dict__["Asharp"] = 10
    B = 11
    __dict__["B"] = 11
    Bflat = 10
    __dict__["Bflat"] = 10
    Bsharp = 0
    __dict__["Bsharp"] = 0
    C = 0
    __dict__["C"] = 0
    Cflat = 11
    __dict__["Cflat"] = 11
    Csharp = 1
    __dict__["Csharp"] = 1
    D = 2
    __dict__["D"] = 2
    Dflat = 1
    __dict__["Dflat"] = 1
    Dsharp = 3
    __dict__["Dsharp"] = 3
    E = 4
    __dict__["E"] = 4
    Eflat = 3
    __dict__["Eflat"] = 3
    Esharp = 5
    __dict__["Esharp"] = 5
    F = 5
    __dict__["F"] = 5
    Fsharp = 6
    __dict__["Fsharp"] = 6
    G = 7
    __dict__["G"] = 7
    Gflat = 6
    __dict__["Gflat"] = 6
    Gsharp = 8
    __dict__["Gsharp"] = 8
    Rest = -1  # aka none
    __dict__["Rest"] = -1  # aka none

    @staticmethod
    def from_string(note: str):
        return Notes.__dict__.get(f"{note[0].upper()}{note[1:].lower()}")

    @staticmethod
    def from_int(note: int):
        possible = [n for n in Notes.__dict__ if note == Notes.__dict__[n]]
        if not possible:
            raise Exception(f"Cannot find note corresponding to value {note}")
        return possible[0]


class DefaultSimilarityThresholds:
    """
    A collection of default values for calculating similarity
    """
    Danceability = 0.2
    Energy = 0.2
    Keys = 12
    Tempo = 10
    TimeSignature = 0
    Mode = 1


class MixingSimilarityThresholds:
    """
    A collection of default values for calculating mix-ability
    """
    Danceability = 0.2
    Energy = 0.2
    Keys = 1
    Tempo = 4
    TimeSignature = 0
    Mode = 0


class SimilarityMinValues:
    Danceability = 0.0
    Energy = 0.0
    Keys = -1
    Tempo = 0
    TimeSignature = 0
    Mode = 0


class SimilarityMaxValues:
    Danceability = 1.0
    Energy = 1.0
    Keys = 11
    Tempo = 200
    TimeSignature = 10
    Mode = 1


class LogLevel:
    """
    The Log Level class used in the Logger to determine when messages should be printed
    """
    Error = 0
    Info = 1
    Debug = 2


def generate_documentation():
    """
    Calls pdoc to generate the html documentation for the python code
    """
    import subprocess
    import os

    assert not subprocess.check_call(f"pdoc -d google --output-dir docs {os.getcwd()}".split(' ')), "Pdoc command failed!"


class Logger:
    """
    The very bare-bones logging class which can be used globally or locally
    """
    instance = None

    def __init__(self, log_level=LogLevel.Info, is_global=True):
        self.log_level = log_level
        if is_global:
            Logger.instance = self

    def _write(self, msg, level=LogLevel.Info):
        """
        low level write function that is called from a logger instance
        Args:
            msg: (any) message to print
            level: (LogLevel) level to print at
        """
        if level <= self.log_level:
            print(msg)

    @staticmethod
    def get_logger(level_if_empty=LogLevel.Info):
        if Logger.instance:
            return Logger.instance
        else:
            return Logger(level_if_empty)

    @staticmethod
    def write(msg, log_level=LogLevel.Info):
        Logger.get_logger(log_level)._write(msg, log_level)

    @staticmethod
    def get_log_level(level_if_empty=LogLevel.Info):
        return Logger.get_logger(level_if_empty).log_level

    @staticmethod
    def set_log_level(level=LogLevel.Info):
        Logger.get_logger(level).log_level = level


# Global log
LOG = Logger(log_level=LogLevel.Info)


if __name__ == "__main__":
    LOG.write("Generating documentation")
    generate_documentation()

