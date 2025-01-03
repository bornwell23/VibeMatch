"""
This file is meant for analyzing audio and finding interesting features and/or points in audio
"""

# import torch
# import torchaudio
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
    return round(float(tempo), 2), frames_to_time(beats, sr=audio_data[1])


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


def write_audio(file_name, y, sr, file_format=FileFormats.Wav):
    import soundfile
    soundfile.write(file_name, y[12 * sr:17 * sr], sr, format=file_format)


def vocal_separation(y, sr, track, metric="cosine", time_width=2, margin_i=2, margin_v=10, power=2):
    import numpy as np
    import librosa


    # write_audio("test.wav", y, sr, file_format=FileFormats.Wav)

    # And compute the spectrogram magnitude and phase
    S_full, phase = librosa.magphase(librosa.stft(y))

    # We'll compare frames using cosine similarity, and aggregate similar frames
    # by taking their (per-frequency) median value.
    #
    # To avoid being biased by local continuity, we constrain similar frames to be
    # separated by at least 2 seconds.
    #
    # This suppresses sparse/non-repetetitive deviations from the average spectrum,
    # and works well to discard vocal elements.

    S_filter = librosa.decompose.nn_filter(S_full,
                                           aggregate=np.median,
                                           metric=metric,
                                           width=int(librosa.time_to_frames(time_width, sr=sr)))

    # The output of the filter shouldn't be greater than the input
    # if we assume signals are additive.  Taking the pointwise minimum
    # with the input spectrum forces this.
    S_filter = np.minimum(S_full, S_filter)

    # We can also use a margin to reduce bleed between the vocals and instrumentation masks.
    # Note: the margins need not be equal for foreground and background separation

    mask_i = librosa.util.softmask(S_filter,
                                   margin_i * (S_full - S_filter),
                                   power=power)

    mask_v = librosa.util.softmask(S_full - S_filter,
                                   margin_v * S_filter,
                                   power=power)

    # Once we have the masks, multiply them with the input spectrum to separate the components
    S_foreground = mask_v * S_full
    S_background = mask_i * S_full

    y_background = librosa.istft(S_background * phase)

    y_foreground = librosa.istft(S_foreground * phase)
    # Play back a 5-second excerpt with only vocals
    write_audio(f"test_foreground_{metric}_{time_width}_{margin_i}_{margin_v}_{power}.wav", y_foreground, sr, file_format=FileFormats.Wav)
    # Play back a 5-second excerpt without vocals
    write_audio(f"test_background_{metric}_{time_width}_{margin_i}_{margin_v}_{power}.wav", y_background, sr, file_format=FileFormats.Wav)


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
    import sklearn.neighbors as neighbors  # for getting nn_filter params
    import datetime

    song_name = f"{FolderDefinitions.Songs}/Will Sparks - Come With Me.{FileFormats.Default}"
    # metadata = get_metadata(song_name)
    # analysis = load_analysis()
    # Logger.write(get_tempo_and_beat_indices(analysis))
    # show_beat_analysis(analysis)
    # show_harmonic_vs_percussive(analysis)
    y, sr = load_analysis(song_name)
    from librosa import effects
    y_harm, y_perc = effects.hpss(y)  # , margin=(1.0, 5.0)
    write_audio("harmonic.wav", y_harm, sr)
    write_audio("percussive.wav", y_perc, sr)
    # metrics = sorted(neighbors.VALID_METRICS['brute'])
    # time_taken = {
    #     "braycurtis": {10*60},
    #     "canberra":{ 12*60},
    #     "chebyshev": { 6*60},
    #     "cityblock": { 7*60},
    #     "correlation": { 9*60},
    #     "cosine": { 2*60},
    #     "dice": { 13*60 },  # data converted
    #     "euclidean": { 2*60 },
    #     "hamming": { 10*60},
    #     "haversine": {}, # did not work
    #     "jaccard": {8*60 },  # data converted
    #     "kulsinski": {8 * 60 }, # data converted
    #     "l1": {8*60 },
    #     "l2": {2*60 },
    #     "mahalanobis": { 2*60*60 }, # yet to complete after 2.1 hours
    # }
    # metrics = [metric for metric in metrics if metric not in time_taken]
    # for v in range(0, 1):
    #     for i in range(1, 2):
    #         for t in range(1, 2):
    #             for m in metrics:
    #                 for p in range(1, 2):
    #                     start = datetime.datetime.now()
    #                     Logger.write(f"Running with params {m}, {t}, {i}, {v}, {p} at {start}")
    #                     try:
    #                         vocal_separation(y, sr, song_name, metric=m, time_width=t, margin_i=i, margin_v=v, power=p)
    #                         try:
    #                             end = datetime.datetime.now()
    #                             Logger.write(f"Created with params {m}, {t}, {i}, {v}, {p} at {end} in {end-start}")
    #                             with open(f"{m}.txt", 'w') as f:
    #                                 f.write(f"{end-start}")
    #                         except:
    #                             pass
    #                     except Exception as e:
    #                         try:
    #                             Logger.write(f"Failed to create with params {m}, {t}, {i}, {v}, {p}: {e} at {datetime.datetime.now()}")
    #                         except:
    #                             pass

