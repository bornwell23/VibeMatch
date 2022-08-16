"""
This file is responsible for merging audio files together
"""


import os
from utilities import LogLevel, Logger, FileFormats, TimeSegments
from pydub import AudioSegment


def export(audio, out_file):
    """
    Exports an audio file to a given file name
    Args:
        audio: (AudioSegment) the audio to export to a file
        out_file: (string) the name of the file to write to

    Returns:
        (string) the name of the file, or an error string
    """
    out_f = audio.export(out_file, format=FileFormats.Default)
    if out_f is not None:
        try:
            out_f.close()
        except Exception as close_exception:
            pass
        return out_file
    return "No file created"


def overlay(file1, file2, new_name=None, position=0, gain=0.0):
    """
    Crossfades two audio files at a given position. crossfade of 0 means they play one after the other
    Args:
        file1: (string) the first file name
        file2: (string) the second file name
        new_name: (string) the new file name
        position: (int) how many milliseconds to crossfade
        gain: (float) audio gain for the audio being overlaid onto

    Returns:
        (string) the name of the file created
    """
    sound1 = AudioSegment.from_file(file1)
    sound2 = AudioSegment.from_file(file2)
    blank_audio = AudioSegment.silent(len(sound2) + len(sound1) - position, sound1.frame_rate)
    sound1 = sound1 + blank_audio  # add blank audio to the first sound, which will then be overlaid with the new audio
    combined = sound1.overlay(sound2, gain_during_overlay=gain, position=position)
    return export(combined, os.path.join(os.path.split(file1)[0], new_name))


def crossfade(file1, file2, new_name=None, fade=0):
    """
    Crossfades two audio files at a given position. crossfade of 0 means they play one after the other
    Args:
        file1: (string) the first file name
        file2: (string) the second file name
        new_name: (string) the new file name
        fade: (int) how many milliseconds to crossfade

    Returns:
        (string) the name of the file created
    """
    sound1 = AudioSegment.from_file(file1)
    sound2 = AudioSegment.from_file(file2)
    combined = sound1.append(sound2, crossfade=fade)
    return export(combined, os.path.join(os.path.split(file1)[0], new_name))


if __name__ == "__main__":
    import spotify
    in1 = "songs/merged.mp4"
    track_id = spotify.find_song("Come With Me", "Will Sparks")[0]["id"]
    recommended = spotify.get_track_recommendations_from_track(track_id, 1, mixable=True)[0]
    in2 = f"songs/{recommended['artists'][0]['name']} - {recommended['name']}.{FileFormats.M4a}"
    spotify.download_songs(recommended)
    pos = TimeSegments.Minute * 6 + TimeSegments.Second * 58
    file_name = overlay(in1, in2, f"3xM.{FileFormats.Default}", position=pos, gain=-0.0)
    # in1 = "songs/Hardwell - I FEEL LIKE DANCING.mp3"
    # in2 = "songs/Will Sparks - Come With Me.m4a"
    # Logger.write(f"Merging '{in1}' and '{in2}'")
    # pos = TimeSegments.Minute * 3 + TimeSegments.Second * 30
    # file_name = overlay(in1, in2, f"merged.{FileFormats.Default}", position=pos, gain=-0.0)
    import sys
    if "play" in sys.argv:
        from pydub.playback import play
        if os.path.exists(file_name):
            song = AudioSegment.from_file(file_name, FileFormats.Default)
            play(song)
        else:
            Logger.write(f"{file_name} not found")