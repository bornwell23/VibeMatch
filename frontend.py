from pathlib import Path
import time
try:
    import utilities
    import spotify
    import os
    import merge
    import match
    import analyze
except Exception as local_import_error:
    print("Not running locally:", local_import_error)
    import VibeMatch.utilities as utilities
    import VibeMatch.spotify as spotify
    import VibeMatch.merge as merge
    import VibeMatch.match as match
    import VibeMatch.analyze as analyze


def display_help():
    utilities.Logger.write("Usage as follows 'python -m VibeMatch', 'python -m vibe', or just 'vibe', with arguments:")
    for arg in utilities.ArgParser.all_args:
        utilities.Logger.write(arg.usage_string())


def speed(source, dest, target_bpm):
    source_audio, path = spotify.download_or_open(source)
    analysis = analyze.load_analysis(path)
    source_bpm = analyze.get_tempo_and_beat_indices(analysis)[0]
    new_audio = merge.shift_tempo(source_audio, merge.get_bpm_multiplier(source_bpm, target_bpm))
    try:
        os.makedirs(os.path.split(dest)[0], exist_ok=True)
        merge.export(new_audio, dest)
        print(f"Saved file to {dest}")
    except:
        print(f"Couldn't save file to {dest}")
        split = path.split('.')
        backup_path = f"{''.join(split[:-1])}_{target_bpm}bpm.{split[-1]}"
        merge.export(new_audio, backup_path)
        print(f"Saved file to {backup_path}")

def fade(sources, dest, duration):
    pass


def overlay(sources, dest, position):
    pass


def append(sources, dest):
    pass


def cut(source, dest, position):
    pass


def find(substring:str):
    """
    Attempts to find music based on a string search
    Comma-delimited
    e.g. Come With Me, Will Sparks

    Args:
        substring (_type_): _description_
    """
    name = None
    artist = None
    album = None 
    commas = substring.count(',')
    if commas == 2:
        name, artist, album = substring.split(',')
    elif commas == 1:
        name, artist = substring.split(',')
    elif commas == 0:
        name = substring
    else:
        raise Exception("Search string '{substring}' has too many commas, search string should be one of the following formats: name,artist,album or name,artist or name")
    found = spotify.find_song(song_name=name, artist=artist, album=album)
    for f in found:
        print(f"found {f['name']} by {f['artists'][0]['name']}: {f['external_urls']['spotify']}")


def get(id, output=None):
    if not output:
        if ',' in id:
            id, output = id.split(',')
    d, path = spotify.download_music(id, custom_folder=output)
    i = 5
    while i > 0 and d.download_tracker.get_song_list():  # TODO: fix this reference
        print(i)
        time.sleep(1)
    print(f"open: {path}")
    utilities.open_to_file(path)

def match(sources):
    assert isinstance(sources, list)
    end = len(sources)
    features = []
    for i in range(end):
        features.append(spotify.get_track_audio_features(sources[i]))
    for i in range(end):
        if i+1 < end:
            utilities.Logger.write(f"{features[i]} and {features[i+1]} {'' if match.vibes_match() else 'do not '}match")


def mixing(sources):
    pass


def spin(sources, dest):
    pass


def play(source):
    if not isinstance(source, list):
        source = [source]
    for s in source:
        utilities.play(s)


def main():
    import sys
    import os
    parsed_args = utilities.ArgParser(sys.argv[1:])
    if len(sys.argv) == 1 or parsed_args.Help.called:
        display_help()
    input = None
    output = None
    if parsed_args.Input.called:
        input = parsed_args.Input.value
    if parsed_args.Output.called:
        output = parsed_args.Output.value
    if parsed_args.Speed.called:
        speed(input, output, parsed_args.Speed.value)
    if parsed_args.Fade.called:
        fade(input, output, parsed_args.Fade.value)
    if parsed_args.Overlay.called:
        overlay(input, output, parsed_args.Overlay.value)
    if parsed_args.Add.called:
        append(input, output)
    if parsed_args.Cut.called:
        cut(input, output, parsed_args.Cut.value)
    if parsed_args.Find.called:
        find(parsed_args.Find.value)
    if parsed_args.Get.called:
        get(parsed_args.Get.value, output)
    if parsed_args.VibeMatch.called:
        match(input)
    if parsed_args.Mixing.called:
        mixing(input)
    if parsed_args.Mix.called:
        spin(input, output)

    if parsed_args.Play.called:
        cur_dir = os.getcwd()
        if cur_dir.endswith("VibeMatch"):
            audio_path = parsed_args.Play.value
        else:
            audio_path = os.path.abspath(os.path.join("VibeMatch", parsed_args.Play.value))
        assert os.path.exists(audio_path), f"The audio file '{parsed_args.Play.value}' doesn't exist! Cannot play it"
        play(audio_path)

if __name__ == "__main__":
    main()
