"""
This file determines if two songs are similar enough to be in the same playlist
This could either mean they would be good to listen to in a playlist, or that they should be able to be mixed
"""


import database
import spotify
from utilities import Logger, LogLevel, DefaultSimilarityThresholds, MixingSimilarityThresholds, Scales


def value_match_with_threshold(value1, value2, threshold: float = 0):
    """
    The base function for checking values meet a threshold variation criteria
    Args:
        value1: (any) first value to check
        value2: (any) second value to check
        threshold: (any) the max variation allowed

    Returns:
        (bool) whether or not the values are within the threshold
    """
    return abs(value1 - value2) <= threshold


def keys_match(key1, key2, threshold=DefaultSimilarityThresholds.Keys):
    """
    Checks if the two songs have close enough musical note keys
    Args:
        key1: (int) the first key
        key2: (int) the second key
        threshold: (float) the maximum variation in keys

    Returns:
        (bool) whether or not the keys are close enough
    """
    return value_match_with_threshold(key1, key2, threshold)


def keys_in_same_scale(key1, key2, approved: list = None):
    """
    Determines if the provided keys are in the same scale, and optionally an approved scale
    Args:
        key1: (string) key 1
        key2: (string) key 2
        approved: (list) list of approved scales

    Returns:
        (string) the scale name that they match in
    """
    approved = Scales.get_scales() if not approved else [approved] if not isinstance(approved, list) else approved
    for scale in Scales.get_scales():
        if scale not in approved:
            continue
        if key1 in scale and key2 in scale:
            return Scales.get_scale_name(scale)
    return False


def danceability_match(danceability1, danceability2, threshold=DefaultSimilarityThresholds.Danceability):
    """
    Checks if the two songs have a similar danceability
    Args:
        danceability1: (int) the first danceability value
        danceability2: (int) the second danceability value
        threshold: (float) the maximum variation in danceability

    Returns:
        (bool) whether or not the danceability is close enough
    """
    return value_match_with_threshold(danceability1, danceability2, threshold)


def energy_match(energy1, energy2, threshold=DefaultSimilarityThresholds.Energy):
    """
    Checks if the two songs have a similar energy
    Args:
        energy1: (int) the first energy value
        energy2: (int) the second energy value
        threshold: (float) the maximum variation in energy

    Returns:
        (bool) whether or not the energy is close enough
    """
    return value_match_with_threshold(energy1, energy2, threshold)


def mode_match(mode1, mode2):
    """
    Checks if the two songs have the same mode
    Args:
        mode1: (int) the first mode
        mode2: (int) the second mode

    Returns:
        (bool) whether or not the mode is the same
    """
    return value_match_with_threshold(mode1, mode2, 0)


def tempo_match(tempo1, tempo2, threshold=DefaultSimilarityThresholds.Tempo):
    """
    Checks if the tempos of two songs are close
    Args:
        tempo1: (int) the first tempo
        tempo2: (int) the second tempo
        threshold: (int) the maximum expected variation in tempo, generally 0-10 bpm, much larger would be jarring

    Returns:
        (bool) whether or not the tempos close enough
    """
    return value_match_with_threshold(tempo1, tempo2, threshold)


def time_signature_match(signature1, signature2, threshold=DefaultSimilarityThresholds.TimeSignature):
    """
    Checks if the time signatures of two songs are close
    Args:
        signature1: (int) the first time signature
        signature2: (int) the second time signature
        threshold: (int) the maximum expected variation in time signature, generally 0

    Returns:
        (bool) whether or not the time signatures are close enough
    """
    return value_match_with_threshold(signature1, signature2, threshold)


def vibes_match(feature1, feature2):
    """
    Checks that the two songs generally make sense in the same playlist, i.e. they have similar features
    Args:
        feature1: (dict) the first set of features
        feature2: (dict) the second set of features

    Returns:
        (bool) whether or not the vibes match
    """
    danceability = danceability_match(feature1.get("danceability"), feature2.get("danceability"))
    energy = energy_match(feature1.get("energy"), feature2.get("energy"))
    tempo = tempo_match(feature1.get("tempo"), feature2.get("tempo"))
    Logger.write(f'danceability:{feature1.get("danceability")} vs {feature2.get("danceability")}, ' +
                 f'energy:{feature1.get("energy")} vs {feature2.get("energy")}, ' +
                 f'tempo:{feature1.get("tempo")} vs {feature2.get("tempo")}',
                 LogLevel.Debug)
    return danceability and energy and tempo


def good_for_mixing(feature1, feature2):
    """
    Checks if the songs are good for mixing together e.g. for DJing
    This is based on time signature, bpm, key matching, and then their general vibe
    Args:
        feature1: (dict) the first set of features
        feature2: (dict) the second set of features

    Returns:
        (bool) whether or not the songs seem to be good for matching
    """
    keys = keys_in_same_scale(feature1.get("key"), feature2.get("key"))  # keys_match(feature1.get("key"), feature2.get("key"), threshold=MixingSimilarityThresholds.Keys)
    danceability = danceability_match(feature1.get("danceability"), feature2.get("danceability"), threshold=MixingSimilarityThresholds.Danceability)
    energy = energy_match(feature1.get("energy"), feature2.get("energy"), threshold=MixingSimilarityThresholds.Energy)
    mode = mode_match(feature1.get("mode"), feature2.get("mode"))
    tempo = tempo_match(feature1.get("tempo"), feature2.get("tempo"), threshold=MixingSimilarityThresholds.Tempo)
    time_signature = time_signature_match(feature1.get("time_signature"), feature2.get("time_signature"), threshold=MixingSimilarityThresholds.TimeSignature)
    Logger.write(f'keys: {feature1.get("key")} vs {feature2.get("key")}, ' +
                 f'danceability:{feature1.get("danceability")} vs {feature2.get("danceability")}, ' +
                 f'energy:{feature1.get("energy")} vs {feature2.get("energy")}, ' +
                 f'mode:{feature1.get("mode")} vs {feature2.get("mode")}, ' +
                 f'tempo:{feature1.get("tempo")} vs {feature2.get("tempo")}, ' +
                 f'time_signature:{feature1.get("time_signature")} vs {feature2.get("time_signature")}',
                 LogLevel.Debug)
    return keys and danceability and energy and mode and tempo and time_signature


if __name__ == "__main__":
    Logger.set_log_level(LogLevel.Debug)
    features = database.get_audio_features(2)
    f1 = features[0]
    f2 = features[1]
    key1 = f1.get("key")
    key2 = f2.get("key")
    d1 = f1.get("danceability")
    d2 = f2.get("danceability")
    n1 = spotify.get_track_name_from_feature(f1)
    n2 = spotify.get_track_name_from_feature(f2)
    Logger.write(f"Keys for {n1} and {n2} {'do not' if not keys_match(key1, key2, 1) else ''} match: {key1}, {key2}")
    Logger.write(f"Danceability for {n1} and {n2} {'does not match' if not danceability_match(d1, d2, 1) else 'matches'}: {d1}, {d2}")
    Logger.write(f"{n1} and {n2} are {'' if good_for_mixing(f1, f2) else 'not '}good for mixing")
    Logger.write(f"{n1} and {n2} are {'' if vibes_match(f1, f2) else 'not '}the same vibe")
