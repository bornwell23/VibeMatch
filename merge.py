"""
This file is responsible for merging audio files together

Key functionality from the pydub library used include

Get audio segments using list syntax
new_segment = original[start_pos_in_ms:end_pos_in_ms]

Change volume by n dB
new_segment = original + n  # or - for reduce

Add audio segments
new_segment = original_1 + original_2

Repeat audio
new_segment = original * 2

Fade
new_segment = original.fade_in(duration_ms)  # or fade_out()

Crossfade
new_segment = original.append(end, crossfade=crossfade_ms)
"""


import os
from pydub import AudioSegment, effects
try:
    from utilities import LogLevel, Logger, FileFormats, TimeSegments, get_bpm_multiplier, play, FolderDefinitions
    from spotify import get_audio_features
except:
    from VibeMatch.utilities import LogLevel, Logger, FileFormats, TimeSegments, get_bpm_multiplier, play, FolderDefinitions
    from VibeMatch.spotify import get_audio_features


def get_beginning(audio_segment, ms):
    """
    Gets the first specified amount of milliseconds of audio
    Args:
        audio_segment: (AudioSegment) the audio to split
        ms: (int) the millisecond position to split on

    Returns:
        (AudioSegment) the audio chunk
    """
    return audio_segment[:ms]


def get_end(audio_segment, ms):
    """
    Gets the last specified amount of milliseconds of audio
    Args:
        audio_segment: (AudioSegment) the audio to split
        ms: (int) the millisecond position to split on

    Returns:
        (AudioSegment) the audio chunk
    """
    return audio_segment[ms:]


def split_audio(audio_segment, position):
    """
    Splits the audio in 2 chunks based on the position provided
    Args:
        audio_segment: (AudioSegment) the audio to split
        position: (int) the millisecond position to split on

    Returns:
        (2-item tuple of AudioSegments) the two audio chunks
    """
    return get_beginning(audio_segment, position), get_end(audio_segment, position)


def get_audio_section(audio_segment, start_pos, end_pos):
    """
    Gets a section of the audio between the two positions
    Args:
        audio_segment: (AudioSegment) the audio chunk
        start_pos: (int) the millisecond position to start at
        end_pos: (int) the millisecond position to end on

    Returns:
        (AudioSegment) the audio chunk
    """
    return audio_segment[start_pos:end_pos]


def shift_tempo(sound: AudioSegment, speed=1.0):
    """
    Changes the speed of the audio, so as to shift the tempo/BPM
    Attempts to smooth the shift so that it sounds natural and doesn't create a chipmunk effect
    Args:
        sound: (AudioSegment) the sound to affect
        speed: (float) the multiplier

    Returns:
        (AudioSegment) the audio that has been shifted
    """
    return effects.speedup(sound, speed)


def match_beat(source: AudioSegment, source_file: str, target_file: str):
    from pydub.utils import mediainfo
    from database import FeaturesDatabase
    features_db = FeaturesDatabase.get_instance()
    source_features = features_db.get_features_from_file_name(source_file)
    target_features = features_db.get_features_from_file_name(target_file)
    source_bpm = source_features["tempo"]
    target_bpm = target_features["tempo"]
    return shift_tempo(source, get_bpm_multiplier(source_bpm, target_bpm))


def export(audio, out_file):
    """
    Exports an audio file to a given file name
    Args:
        audio: (AudioSegment) the audio to export to a file
        out_file: (string) the name of the file to write to

    Returns:
        (string) the name of the file, or an error string
    """
    out_f = audio.export(out_file, format=FileFormats.Mp4)
    if out_f is not None:
        try:
            out_f.close()
        except Exception as close_exception:
            pass
        return out_file
    return "No file created"


def overlay(file1, file2, new_name=None, position=0, gain=0.0):
    """
    Overlays two audio files at a given position. position of 0 means they play on top of each other
    Args:
        file1: (string) the first file name
        file2: (string) the second file name
        new_name: (string) the new file name
        position: (int) how many milliseconds to wait until overlaying
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
    # in1 = f"{FolderDefinitions.Songs}/merged.mp4"
    # track_id = spotify.find_song("Come With Me", "Will Sparks")[0]["id"]
    # recommended = spotify.get_track_recommendations_from_track(track_id, 1, mixable=True)[0]
    # in2 = f"{FolderDefinitions.Songs}/{recommended['artists'][0]['name']} - {recommended['name']}.{FileFormats.M4a}"
    # spotify.download_songs(recommended)
    # pos = TimeSegments.Minute * 6 + TimeSegments.Second * 58
    # file_name = overlay(in1, in2, f"3xM.{FileFormats.Default}", position=pos, gain=-0.0)
    # in1 = f"{FolderDefinitions.Songs}/Hardwell - I FEEL LIKE DANCING.mp3"
    # in2 = "{FolderDefinitions.Songs}/Will Sparks - Come With Me.m4a"
    # Logger.write(f"Merging '{in1}' and '{in2}'")
    # pos = TimeSegments.Minute * 3 + TimeSegments.Second * 30
    # file_name = overlay(in1, in2, f"merged.{FileFormats.Default}", position=pos, gain=-0.0)

    # come_with_me = f"{FolderDefinitions.Songs}/Will Sparks - Come With Me.{FileFormats.Default}"
    # audio = AudioSegment.from_file(come_with_me, FileFormats.Default)
    # faster = shift_tempo(audio, get_bpm_multiplier(132, 160))
    # file_name = f"{FolderDefinitions.Songs}/Faster Come With Me.{FileFormats.Mp4}"
    # export(faster, file_name)

    from utilities import get_song_path
    darkness = "https://open.spotify.com/track/585nN5GXqQIfc6pGXkBCJK?si=bbb01abb58e54996"  # ben nicky darkness
    tananum = "https://open.spotify.com/track/7fTOmqPsWSzcTcRfdRCfNM?si=beded226f60047db"  # tana num
    spotify.download_songs([darkness, tananum])
    d_file = get_song_path(spotify.get_track_info(spotify.get_track_id_from_url(darkness)))
    d_audio = AudioSegment.from_file(d_file, FileFormats.Default)
    t_file = get_song_path(spotify.get_track_info(spotify.get_track_id_from_url(tananum)))
    t_audio = AudioSegment.from_file(t_file, FileFormats.Default)
    file_name = f"{FolderDefinitions.Songs}/New Darkness.{FileFormats.Default}"
    d_faster = match_beat(d_audio, d_file, t_file)
    export(d_faster, file_name)

    import sys
    if "play" in sys.argv:
        play(file_name)
