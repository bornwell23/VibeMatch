"""
This file is a general-purpose file for various functionality that is not directly tied to a feature
Primarily this contains logging and documentation utilities
"""


class DefaultSimilarityThresholds:
    """
    A collection of default values for calculating similarity
    """
    Danceability = 0.1
    Energy = 0.1
    Keys = 0
    Tempo = 1
    TimeSignature = 0


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

