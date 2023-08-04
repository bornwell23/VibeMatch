"""
This file is a general-purpose file for various functionality that is not directly tied to a feature
Primarily this contains logging and documentation utilities, but also contains definition values for audio data
"""


import os
import platform
import subprocess


class FolderDefinitions:
    Songs = "songs"
    Docs = "docs"
    Remover = "remover"


class Arg:
    def __init__(self, long, short, desc, expected_type):
        assert isinstance(long, str), f"Arg name is not a string: '{long}'"
        assert isinstance(short, str) and len(short) == 1, f"Short name for {long} is not a single character: '{short}'"
        assert isinstance(desc, str), f"Description for {long} is not a string"
        self.long = long
        self.short = short
        self.desc = desc
        self.expected = expected_type
        self.value = None
        self.called = False

    def __str__(self):
        return self.long

    def set_value(self, value, expected_type):
        if isinstance(value, str):
            if ',' in value:  # may be a list
                if value.find(',') <= value.find('.') and value.count('.'):  # list of files
                    self.value = value.split(',')
                else:  # probably not a list? are there other scenarios?
                    self.value = value
            else:  # definitely not a list, just a string
                if value.isnumeric():
                    self.value = int(value)
                elif '.' in value and value.replace('.', '').isnumeric():
                    self.value = float(value)
                elif value.lower() == "true":
                    self.value = True
                elif value.lower() == "false":
                    self.value = False
                else:  # what is this?
                    self.value = value
        else:  # not a string... what is it?
            self.value = value
        if expected_type:
            assert isinstance(value, expected_type), f"Value '{value}' for arg '{self.long}' is not of the expected type '{expected_type}'"
        else:
            assert isinstance(value, type(None)), f"Not expecting a value for {self.long}!"

    def usage_string(self):
        usage = f"--{self.long} or -{self.short}"
        if self.expected:
            t = f"{self.expected}".split("'")[1]
            usage += f" <{t}>"
        usage += f": {self.desc}"
        return usage


class ArgParser:
    Add = Arg("add", "a", "Add two audio files - requires two -i params or -i 'param1,param2'", str)
    Cut = Arg("cut", "c", "Cut a portion of the audio file - takes a millisecond position parameter", int)
    Fade = Arg("fade", "f", "Crossfade between two audio files - takes a millisecond duration parameter", int)
    Find = Arg("find", "f", "Find a song - takes a string/substring search parameter e.g. Despacito instead of the url to the track", str)
    Get = Arg("get", "g", "Get a song - takes a string url/id parameter e.g. https://open.spotify.com/track/2Ns9qqEAYMclhGyfABG8GJ", str)
    Help = Arg("help", "h", "Display help menu", None)
    Input = Arg("input", "i", "Input file(s) - takes a string parameter, consisting of a comma delimited files, use quotes if spaces are in file names", str)
    Mixing = Arg("mixing", "m", "Determine whether or not input songs are good for mixing", None)
    Mix = Arg("mix", "x", "Mix the two songs, based on audio analysis", None)
    Output = Arg("output", "o", "Output file - takes a string parameter", str)
    Overlay = Arg("overlay", 'l', "Overlay two audio segments on top of each other - takes a millisecond position parameter to start overlay", int)
    Play = Arg("play", "p", "Play audio - requires -i param for audio to play", str)
    Speed = Arg("speed", "s", "Change the input audio's speed - takes an int BPM or float multiplier", float)
    VibeMatch = Arg("match", "v", "Determine whether or not the input songs are have the same vibe", None)

    all_args = [Add, Cut, Fade, Find, Get, Help, Input, Mixing, Mix, Output, Play, Speed, VibeMatch]
    instance = None

    def __init__(self, args):
        """
        Builds an argument parser object
        Args:
            args: (list) list of parameters to parse as run-time arguments, generally sys.argv[1:]
        """
        if ArgParser.instance:
            Logger.write("Arg parser already exists! What are you trying to do!? Not parsing args again...")
            return
        i = 0
        while i < len(args):
            found = False
            for arg in ArgParser.all_args:
                parsed = args[i]
                if parsed == f"--{arg.long}" or parsed == f"-{arg.short}":
                    arg.called = True
                    found = True
                    if arg.expected is not None:
                        assert len(args) >= i+1, f"Args incomplete. Param {parsed} needs a value"
                        arg.set_value(args[i+1], arg.expected)
                        i += 1  # skip param
            i += 1
            if not found:
                err_str = f"Unexpected argument '{parsed}'? Run with -{ArgParser.Help.short} or --{ArgParser.Help.long} to see usage information"
                Logger.write(err_str, LogLevel.Error)
                raise ValueError(err_str)
        ArgParser.instance = self


class FileFormats:
    """
    A class containing audio file formats
    """
    Mp4 = "mp4"
    M4a = "m4a"
    Wav = "wav"
    Mp3 = "mp3"
    Default = M4a


class TimeSegments:
    """
    A class containing the time blocks in milliseconds
    """
    Second = 1000
    Minute = Second * 60
    Hour = Minute * 60


def get_bpm_multiplier(original: float, target: float):
    """
    Returns the multiplier for the bpm shift from original to target
    Used in beat matching
    Args:
        original: (float) BPM of the audio
        target: (float) target BPM

    Returns:
        (float) the multiplier e.g. 1.23
    """
    return target/original


class Notes:
    """
    A class containing notes/keys and functions to convert between the int representation and string name
    """
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


class Scales:
    """
    A class that contains the notes that correspond to the various scales
    """
    Full = [Notes.C, Notes.Csharp, Notes.D, Notes.Dsharp, Notes.E, Notes.F, Notes.Fsharp, Notes.G, Notes.Gsharp, Notes.A, Notes.Asharp, Notes.B]
    Ionion = [Notes.C, Notes.D, Notes.E, Notes.F, Notes.G, Notes.A, Notes.B]
    Lydian = [Notes.C, Notes.D, Notes.E, Notes.Fsharp, Notes.G, Notes.A, Notes.B]
    Mixolydian = [Notes.C, Notes.D, Notes.E, Notes.F, Notes.G, Notes.A, Notes.Bflat]
    Dorian = [Notes.C, Notes.D, Notes.Eflat, Notes.F, Notes.G, Notes.A, Notes.Bflat]
    Aeolian = [Notes.C, Notes.D, Notes.Eflat, Notes.F, Notes.G, Notes.Aflat, Notes.Bflat]
    Phrygian = [Notes.C, Notes.Dflat, Notes.Eflat, Notes.F, Notes.G, Notes.Aflat, Notes.Bflat]
    Locrian = [Notes.C, Notes.Dflat, Notes.Eflat, Notes.F, Notes.Gflat, Notes.Aflat, Notes.Bflat]
    DarkLocrian = [Notes.Dflat, Notes.Eflat, Notes.Gflat, Notes.Aflat, Notes.Bflat]
    LightLydian = [Notes.Fsharp, Notes.G, Notes.A, Notes.B]

    @staticmethod
    def get_scales():
        """
        Returns a list of the scales
        Returns:
            (list of lists) list of the scales
        """
        return [Scales.Full, Scales.Ionion, Scales.Lydian, Scales.Mixolydian, Scales.Dorian,
                Scales.Aeolian, Scales.Phrygian, Scales.Locrian, Scales.DarkLocrian, Scales.LightLydian]

    @staticmethod
    def get_scale_name(scale):
        for name, item in Scales.__dict__.items():
            if isinstance(item, list) and scale == item:
                return name


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
    """
    A class containing minimum values of the attributes that might be compared between songs
    """
    Danceability = 0.0
    Energy = 0.0
    Keys = -1
    Tempo = 0
    TimeSignature = 0
    Mode = 0


class SimilarityMaxValues:
    """
    A class containing maximum values of the attributes that might be compared between songs
    """
    Danceability = 1.0
    Energy = 1.0
    Keys = 11
    Tempo = 200
    TimeSignature = 10
    Mode = 1


def play(audio):
    """
    Plays the audio specified
    Args:
        audio: (AudioSegment|string) the audio to play
    """
    from pydub import AudioSegment, playback
    if isinstance(audio, AudioSegment):
        playback.play(audio)
    elif isinstance(audio, str) and os.path.exists(audio):
        song = AudioSegment.from_file(audio, FileFormats.Default)
        playback.play(song)
    else:
        Logger.write(f"{audio} not found")


def get_song_path(song, folder=None):
    """
    Gets the file path for the song provided
    Args:
        song: (dict) song data retrieved from spotify
        folder: (string) song download folder

    Returns:
        (string) the expected file path of the song
    """
    assert isinstance(song, dict), "provided song data doesn't contain necessary information"
    return f"{folder if folder else FolderDefinitions.Songs}/{song['artists'][0]['name']} - {song['name']}.{FileFormats.Default}"


def get_path_template(folder):
    return os.path.join(os.getcwd(), folder + "/{artist} - {title}.{ext}")


def open_to_file(file_path):
    # FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')

    # explorer would choke on forward slashes
    file_path = os.path.normpath(file_path)

    # if os.path.isdir(file_path):
    #     subprocess.run([FILEBROWSER_PATH, file_path])
    # elif os.path.isfile(file_path):
    #     subprocess.run([FILEBROWSER_PATH, '/select,', file_path])

    if platform.system() == "Windows":
        os.startfile(file_path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", file_path])
    else:
        subprocess.Popen(["xdg-open", file_path])


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

    cur_dir = os.getcwd()
    assert cur_dir.endswith("VibeMatch"), "Documentation generation must run from the VibeMatch root directory"
    os.chdir("..")
    pdoc_command = f"pdoc --html --output-dir VibeMatch/{FolderDefinitions.Docs} {cur_dir} --force"
    res = subprocess.check_call(pdoc_command.split(' '))
    files = os.listdir(f"VibeMatch/{FolderDefinitions.Docs}/VibeMatch")
    for f in files:
        try:
            os.remove(f"VibeMatch/{FolderDefinitions.Docs}/{f}")  # remove old file
        except Exception as remove_exception:  # seems the original file doesn't exist?
            pass
        try:
            os.rename(f"VibeMatch/{FolderDefinitions.Docs}/VibeMatch/{f}", f"VibeMatch/{FolderDefinitions.Docs}/{f}")  # move file to proper location
        except Exception as rename_exception:  # seems the file doesn't exist?
            pass
    os.rmdir(f"VibeMatch/{FolderDefinitions.Docs}/Vibematch")  # remove the directory
    os.chdir(cur_dir)
    assert not res, "Pdoc command failed!"


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
        """
        Gets the existing global instance if it exists or makes a new one otherwise
        Args:
            level_if_empty: (LogLevel) the level to use if there isn't an instance

        Returns:
            (Logger) the global logging object
        """
        if Logger.instance:
            return Logger.instance
        else:
            return Logger(level_if_empty)

    @staticmethod
    def write(msg, log_level=LogLevel.Info):
        """
        writes a string using the global logger
        Args:
            msg: (any) the message to write
            log_level: (LogLevel) the level to write at
        """
        Logger.get_logger(log_level)._write(msg, log_level)

    @staticmethod
    def get_log_level(level_if_empty=LogLevel.Info):
        """
        Gets the current global log level
        Args:
            level_if_empty: (LogLevel) a level to use if there isn't an existing logger

        Returns:
            (LogLevel) the log level of the global instance
        """
        return Logger.get_logger(level_if_empty).log_level

    @staticmethod
    def set_log_level(level=LogLevel.Info):
        """
        Sets the global logger level
        Args:
            level: (LogLevel) the log level to use
        """
        Logger.get_logger(level).log_level = level


# Global log
LOG = Logger(log_level=LogLevel.Info)


if __name__ == "__main__":
    LOG.write("Generating documentation")
    generate_documentation()

