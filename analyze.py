"""
This file is meant for analyzing audio and finding interesting features and/or points in audio
"""


from utilities import Logger
import librosa


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
    Logger.write("Nothing to analyze")