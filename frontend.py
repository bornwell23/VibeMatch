import time
try:
    import utilities
    import spotify
    import merge
    import match
except Exception as local_import_error:
    print("Not running locally:", local_import_error)
    import VibeMatch.utilities as utilities
    import VibeMatch.spotify as spotify
    import VibeMatch.merge as merge
    import VibeMatch.match as match


def display_help():
    utilities.Logger.write("Usage as follows 'python -m VibeMatch', 'python -m vibe', or just 'vibe', with arguments:")
    for arg in utilities.ArgParser.all_args:
        utilities.Logger.write(arg.usage_string())


def speed(source, dest, target):
    pass


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


def get(id):
    d, path = spotify.download(id)
    i = 5
    while i > 0 and d.download_tracker.get_song_list():
        print(i)
        time.sleep(1)
    print(f"open: {path}")
    utilities.open_to_file(path)

def match(sources):
    assert isinstance(sources, list)
    end = len(sources)
    features = []
    for i in range(end):
        features.append(spotify.get_audio_features(sources[i]))
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
    in_audio = None
    out_audio = None
    if parsed_args.Input.called:
        in_audio = parsed_args.Input.value
    if parsed_args.Output.called:
        out_audio = parsed_args.Output.value
    if parsed_args.Speed.called:
        speed(in_audio, out_audio, parsed_args.Speed.value)
    if parsed_args.Fade.called:
        fade(in_audio, out_audio, parsed_args.Fade.value)
    if parsed_args.Overlay.called:
        overlay(in_audio, out_audio, parsed_args.Overlay.value)
    if parsed_args.Add.called:
        append(in_audio, out_audio)
    if parsed_args.Cut.called:
        cut(in_audio, out_audio, parsed_args.Cut.value)
    if parsed_args.Find.called:
        find(parsed_args.Find.value)
    if parsed_args.Get.called:
        get(parsed_args.Get.value)
    if parsed_args.VibeMatch.called:
        match(in_audio)
    if parsed_args.Mixing.called:
        mixing(in_audio)
    if parsed_args.Mix.called:
        spin(in_audio, out_audio)

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