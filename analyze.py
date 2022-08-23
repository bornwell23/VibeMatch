"""
This file is meant for analyzing audio and finding interesting features and/or points in audio
"""


from pydub import utils, AudioSegment
try:
    from utilities import Logger, FolderDefinitions, FileFormats
except:
    from VibeMatch.utilities import Logger, FolderDefinitions, FileFormats


def load_analysis(file_name, audio: AudioSegment = None):
    """
    Loads a file to the format used by librosa
    Args:
        file_name: (string) the file name to load
        audio: (AudioSegment) the optional audio data to grab the existing frame rate from

    Returns:
        (tuple of ndarray and float) the audio data returned from librosa.load
    """
    from librosa import load
    if not audio:
        audio = AudioSegment.from_file(file_name)
    audio_data = load(file_name, sr=audio.frame_rate)
    Logger.write(f"Loaded '{file_name}'")
    return audio_data


def get_tempo_and_beat_indices(audio_data):
    """
    Gets the bpm from the audio analysis
    Args:
        audio_data: (tuple of ndarray and float) the audio data returned from librosa.load

    Returns: (tuple of float, ndarray) the bpm and seconds indices of the beats

    """
    from librosa import beat, frames_to_time, onset
    import numpy as np
    onset_env = onset.onset_strength(y=audio_data[0], sr=audio_data[1], aggregate=np.median)
    tempo, beats = beat.beat_track(onset_envelope=onset_env, sr=audio_data[1])
    return tempo, frames_to_time(beats, sr=audio_data[1])


def show_beat_analysis(audio_data, percent=100):
    """
    Shows a beat analysis displaying where beats are and how strong they are
    Args:
        audio_data: (tuple of ndarray and float) the audio data returned from librosa.load
        percent: (int) how much of the song to show, e.g. 25 shows the first quarter of the song. this data is crowded
    """
    import matplotlib.pyplot as plt
    from librosa import beat, onset, times_like, util
    import numpy as np
    hop_length = 512
    audio_data = audio_data[0][:int(len(audio_data[0])/(100/percent))], audio_data[1]
    fig, ax = plt.subplots(nrows=1)
    onset_env = onset.onset_strength(y=audio_data[0], sr=audio_data[1], aggregate=np.median)
    tempo, beats = beat.beat_track(onset_envelope=onset_env, sr=audio_data[1])
    times = times_like(onset_env, sr=audio_data[1], hop_length=hop_length)
    ax.plot(times, util.normalize(onset_env),
               label='Onset strength')
    ax.vlines(times[beats], 0, 1, alpha=0.5, color='r',
                 linestyle='--', label='Beats')
    ax.legend()
    plt.show()


def show_harmonic_vs_percussive(audio_data):
    """
    Shows a chart of harmonic analysis vs percussive analysis
    Useful for understanding the makeup the of a song
    Args:
        audio_data: (tuple of ndarray and float) the audio data returned from librosa.load
    """
    from matplotlib import pyplot as plt
    from librosa import effects, display
    fig, (ax, ax2) = plt.subplots(nrows=2)
    ax.set(xlim=[6.0, 6.01], title='Full Track Analysis', ylim=[-0.25, 0.25])
    display.waveshow(audio_data[0], sr=audio_data[1], ax=ax, marker='.', label='Full signal')
    y_harm, y_perc = effects.hpss(audio_data[0])
    display.waveshow(y_harm, sr=audio_data[1], alpha=0.4, ax=ax2, label='Harmonic')
    display.waveshow(y_perc, sr=audio_data[1], color='r', alpha=0.4, ax=ax2, label='Percussive')
    ax.label_outer()
    ax.legend()
    ax2.legend()
    plt.show()


def get_metadata(audio):
    """
    return the metadata from the audio file
    Args:
        audio: (string) the file path to an audio file

    Returns:
        (dict) the metadata dictionary
    """
    return utils.mediainfo(audio)


def find_intro_ms(audio_segment):
    """
    Attempts to find the millisecond position of the end of the intro
    Args:
        audio_segment: (AudioSegment) the audio to analyze

    Returns:
        (int) the end of the introduction section
    """
    return 0


def find_outro_ms(audio_segment):
    """
    Attempts to find the millisecond position of the beginning of the outro
    Args:
        audio_segment: (AudioSegment) the audio to analyze

    Returns:
        (int) the beginning of the outro section
    """
    return 0


def get_avg_db(audio_segment):
    """
    Gets the average decibel value of the audio segment
    Args:
        audio_segment: (AudioSegment)

    Returns:
        (float) the decibel value
    """
    return 0


if __name__ == "__main__":
    # metadata = get_metadata(f"{FolderDefinitions.Songs}/Will Sparks - Come With Me.m4a")
    analysis = load_analysis(f"{FolderDefinitions.Songs}/Will Sparks - Come With Me.{FileFormats.Default}")
    # Logger.write(get_tempo_and_beat_indices(analysis))
    show_beat_analysis(analysis)
    # show_harmonic_vs_percussive(analysis)
