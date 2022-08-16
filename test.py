"""
This file is responsible for testing the code to ensure some semblance of reliable functionality.
This should be run anytime functionality is changed, and should be expanded upon when functionality is added
This file is run in CI/actions on pushes to the main branch
"""


import os
import sys
import pytest
import importlib
from utilities import Logger, LogLevel


def import_lib(lib, explode=False):
    """
    Tries to import a library.
    If that doesn't work, it will return the exception as a string
    Args:
        lib: (string) the library name to import
        explode: (bool) whether or not to raise an exception

    Returns:
        the module, or an exception message
    """
    try:
        return importlib.import_module(lib.strip())
    except Exception as import_exception:
        if explode:
            raise import_exception
        else:
            return f"{import_exception}"


def import_libs(libs):
    """
    Imports a list of libraries to ensure they can be loaded
    Args:
        libs: (list) containing strings corresponding to modules to import
    """
    error_libs = []
    for lib in libs:
        imported = import_lib(lib)
        if isinstance(imported, str):  # failed to load, this is an exception string
            error_libs.append(imported)
    if len(error_libs):
        raise ImportError(f"Unable to import the following libraries: {','.join(error_libs)}. " +
                          "Please run 'pip install -r requirements.txt'")


def import_libs_with_paths(lib_list):
    """
    Imports a list of libraries to ensure they can be loaded
    Mentions the file path the import came from if the import fails
    Args:
        lib_list: (list of tuples containing two strings)
    """
    error_libs = []
    for lib, path in lib_list.items():
        imported = import_lib(lib)
        if isinstance(imported, str):  # failed to load, this is an exception string
            error_libs.append((lib, path, imported))
    if len(error_libs):
        errs = [f"Cannot import '{lib}' in {path} because: {err}" for lib, path, err in error_libs]
        err_str = '\n'.join(errs)
        import_str = ','.join([lib for lib, _, _ in error_libs])
        raise ImportError(f"Unable to import the following libraries: {err_str}. Please run 'pip install {import_str}'")


def get_required_libs():
    """
    Gets the list of required libs from requirements.txt
    Returns:
        (list) list of strings
    """
    with open("requirements.txt", 'r') as reqs:
        libs = reqs.readlines()
    for i in range(len(libs)):
        libs[i] = libs[i].strip('\n \t')
        if libs[i] == "pdoc3":  # special handling for this one which uses a different name on import
            libs[i] = "pdoc"
    return libs


def test_anything_works():
    """
    Asserts that tests are working
    """
    assert 2 == 2, "2 does not equal 2!?"
    with pytest.raises(Exception):
        assert 2 == 3, "2 equals 3!?"


def test_libs():
    """
    Imports the libraries included in the requirements file to ensure they can all be used
    """
    libs = get_required_libs()
    try:
        import_libs(libs)
    except ImportError as import_error:
        Logger.write(f"{import_error}", LogLevel.Error)
        try:
            import subprocess
            subprocess.check_call("pip install -r requirements.txt".split(' '))
        except Exception:
            raise Exception(f"Unable to import libraries, and unable to run pip install automatically: {import_error}")


def test_missing_libs():
    """
    Checks for libraries used that are missing from requirements.txt, also tries to import them to ensure they exist
    """
    libs = dict()
    for root, dirs, files in os.walk("."):  # recursively traverses the current directory
        for file in files:  # the list of files for each respective directory
            if file.endswith(".py"):
                path_name = os.path.join(root, file)  # create the full path to use and print
                with open(path_name, 'r') as py_file:
                    txt = py_file.readlines()  # read all lines into a list
                    for line in txt:
                        if line.startswith("import "):
                            lib_to_import = line[line.find("import ")+7:].strip("\n \t")  # grab the library that's imported
                            libs[lib_to_import] = path_name
    import_libs_with_paths(libs)


def test_db_connection():
    """
    Test some basic database interaction
    """
    import spotify
    from database import create_features_table, get_audio_features
    assert create_features_table()
    spotify.get_audio_features("651YhrvzeVfOa8yIifIhUM")
    assert get_audio_features(1)


def test_spotify():
    """
    Test some basic spotify api interaction
    """
    from spotify import find_song, get_audio_features
    find_song(song_name="Come With Me", artist="Will Sparks")
    get_audio_features("651YhrvzeVfOa8yIifIhUM")


def test_spotify_download():
    """
    Tests some basic downloading functionality
    """
    from spotify import download_songs
    import subprocess
    if os.path.exists("songs/Hardwell - I FEEL LIKE DANCING.mp3"):  # already verified this functionality works
        os.remove("songs/Hardwell - I FEEL LIKE DANCING.mp3")
        Logger.write("Removed existing test song, will download on next run")
        return
    try:
        subprocess.check_call("ffmpeg")
    except FileNotFoundError as no_ffmpeg_error:
        import platform
        Logger.write("Ffmpeg is not installed! Cannot download songs. Please install ffpmeg and try again")
        Logger.write("Ffmpeg can be download from https://ffmpeg.org/download.html, or using a package manager such as 'apt-get install ffmpeg'")
        system = platform.system().lower()
        if system == "windows":
            Logger.write("Download it from here https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.7z")
        elif "mac os x" in system:
            Logger.write("Run curl -JL https://evermeet.cx/ffmpeg/getrelease/ffmpeg/7z --output ffmpeg.7z && 7z -xfv ffmpeg.7z")
        elif "nix" in system:
            Logger.write("Run curl -JL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz --output ffmpeg.tar.xz && 7z -xfv ffmpeg.tar.xz")
        return
    download_songs("651YhrvzeVfOa8yIifIhUM")
    assert os.path.exists("songs/Hardwell - I FEEL LIKE DANCING.mp3"), "Song wasn't downloaded"


def test_note_conversion():
    """
    Tests converting notes
    """
    from utilities import Notes
    assert Notes.from_string("Cflat") == 11
    assert Notes.from_int(Notes.Gflat) == "Fsharp"
    assert Notes.from_string("gsharp") == 8


def test_matching():
    """
    Tests some basic matching functionality
    """
    import spotify
    import match
    f1 = spotify.get_audio_features(spotify.find_song(song_name="Come With Me", artist="Will Sparks")[0].get("id"))
    f2 = spotify.get_audio_features("651YhrvzeVfOa8yIifIhUM")
    key1 = f1.get("key")
    key2 = f2.get("key")
    d1 = f1.get("danceability")
    d2 = f2.get("danceability")
    assert not match.keys_match(key1, key2, 1)
    assert match.danceability_match(d1, d2, 1)
    assert match.good_for_mixing(f1, f2)
    assert match.vibes_match(f1, f2)


if __name__ == "__main__":  # main entry point
    args = sys.argv[1:]
    if len(args):  # if there are any command line args
        for arg in args:  # check all command line parameters after the file name
            if arg in locals():  # checks if the parameter is a function in the current file
                locals()[arg]()  # runs the function
    else:
        # get all functions that start with 'test_' i.e. is a pytest function
        test_funcs = [local for local in locals().copy() if local.startswith("test_")]
        total = len(test_funcs)
        passed = 0
        failed = []
        for test in test_funcs:  # for every local attribute of this file that seems to be a test function
            Logger.set_log_level(LogLevel.Error)
            try:
                locals()[test]()  # run the function
                Logger.set_log_level(LogLevel.Info)
                Logger.write(f"Test '{test}' passed")
                passed += 1
            except Exception as test_error:
                Logger.set_log_level(LogLevel.Info)
                fail_msg = f"Test '{test}' failed due to error: {test_error}"
                Logger.write(fail_msg)
                failed.append(test)
        Logger.write(f"{passed} of {total} ({(passed/total)*100:.2f}%) tests passed")
        if len(failed):  # any failed tests exist
            Logger.write(f"Failing tests: {failed}")
