import database
import spotify
from utilities import Logger, LogLevel, DefaultSimilarityThresholds, MixingSimilarityThresholds, Scales


def value_match_with_threshold(value1, value2, threshold: float = 0):
    return abs(value1 - value2) <= threshold


def keys_match(k1, k2, threshold=DefaultSimilarityThresholds.Keys):
    return value_match_with_threshold(k1, k2, threshold)


def keys_in_same_scale(k1, k2, approved: list = None):
    """
    Determines if the provided keys are in the same scale, and optionally an approved scale
    Args:
        k1: (string) key 1
        k2: (string) key 2
        approved: (list) list of approved scales

    Returns:
        (string) the scale name that they match in
    """
    approved = Scales.get_scales() if not approved else [approved] if not isinstance(approved, list) else approved
    for scale in Scales.get_scales():
        if scale not in approved:
            continue
        if k1 in scale and k2 in scale:
            return Scales.get_scale_name(scale)
    return False


def danceability_match(d1, d2, threshold=DefaultSimilarityThresholds.Danceability):
    return value_match_with_threshold(d1, d2, threshold)


def energy_match(e1, e2, threshold=DefaultSimilarityThresholds.Energy):
    return value_match_with_threshold(e1, e2, threshold)


def mode_match(m1, m2):
    return value_match_with_threshold(m1, m2, 0)


def tempo_match(t1, t2, threshold=DefaultSimilarityThresholds.Tempo):
    return value_match_with_threshold(t1, t2, threshold)


def time_signature_match(t1, t2, threshold=DefaultSimilarityThresholds.TimeSignature):
    return value_match_with_threshold(t1, t2, threshold)


def vibes_match(feature1, feature2):
    danceability = danceability_match(feature1.get("danceability"), feature2.get("danceability"))
    energy = energy_match(feature1.get("energy"), feature2.get("energy"))
    tempo = tempo_match(feature1.get("tempo"), feature2.get("tempo"))
    Logger.write(f'danceability:{feature1.get("danceability")} vs {feature2.get("danceability")}, ' +
                 f'energy:{feature1.get("energy")} vs {feature2.get("energy")}, ' +
                 f'tempo:{feature1.get("tempo")} vs {feature2.get("tempo")}',
                 LogLevel.Debug)
    return danceability and energy and tempo


def good_for_mixing(feature1, feature2):
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
