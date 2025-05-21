# VibeMatch
Keepin the vibe goin brah

The purpose of this repository is to build an automated tool to find similar songs based on input such as a spotify link\
The similarities could include bpm, genre, keys, melodies, vocals, styles, etc

Auxiliary functionality includes:
* storing audio feature data in a sqlite database for local analysis
* mixing two audio files together in various ways
* playing audio

Future plans include but are not limited to:
* Building set lists
* Identifying similar songs using AI
* Automatically identifying drops in songs
* Automatically mixing songs, and eventually playlists
* Query database for known music, faster than querying the spotify API


Github link is: https://github.com/bornwell23/VibeMatch


## Quick Start Guide

### Setup
1. Install Python dependencies:
   ```bash
   # Install dependencies
   python -m pip install -r requirements.txt
   
   # If you have spotdl conflicts, uninstall first
   pip uninstall spotdl
   pip install -r requirements.txt
   ```

2. Install FFmpeg

3. Set up Spotify credentials:
   * Visit [Spotify's getting started page](https://developer.spotify.com/documentation/web-api/tutorials/getting-started#create-an-app)
   * Follow steps for 'Create an app' and 'Request an access token'
   * Create a `.env` file with your credentials:
     ```
     CLIENT_ID='your spotify api id'
     CLIENT_SECRET='your spotify api key'
     ```

### Common Commands

#### Download Music
```bash
# Download a single track
python spotify.py "https://open.spotify.com/track/your_track_id"

# Download a playlist
python spotify.py "https://open.spotify.com/playlist/your_playlist_id"

# Download to a specific folder
python spotify.py "https://open.spotify.com/track/your_track_id" --folder "songs/my_folder"
```

#### Generate Documentation
```bash
# Generate HTML documentation
python utilities.py

# View documentation
# Open docs/index.html in your web browser
```

#### Run Tests
```bash
# Run all tests
python -m pytest test.py

# Run tests with verbose output
python -m pytest test.py -v

# Run a specific test
python -m pytest test.py -k "test_name"
```

To set up the environment:
* ensure python is installed (Click the big yellow "Download Python 3.#.#" button on https://www.python.org/downloads/ and during installatation make sure python is in the path)
* ensure python is in the path by opening up a terminal and typing python --version, if not, view this site for more info https://realpython.com/add-python-to-path/
* install requirements.txt ( in a terminal, run `python -m pip install -r requirements.txt`)
* Note: This project uses spotdl version 4.2.10. If you have a different version installed, you may need to uninstall it first:
  ```bash
  pip uninstall spotdl
  pip install -r requirements.txt
  ```

For development only:
* set up your IDE
  * if using Pycharm
    * Open settings, search for Python Integrated Tools
      * set default test runner to pytest
      * set docstring format to Google
  * if using Visual Studio
    * Open settings, search enable pytest and enable it
    * I suggest installing autoDocstring from the extension marketplace (Ctrl+Shift+X, type autoDocstring)
* run tests via command `python -m pytest test.py`)

To run the program manually:
* run the setup script for your system (Mac -> setup_unix.sh, Windows -> setup_windows.bat)
* run the command `vibe -h` (type `vibe -h`` and press enter)

To get spotify credentials:
* Visit [Spotify's getting started page](https://developer.spotify.com/documentation/web-api/tutorials/getting-started#create-an-app) and follow the steps for 'Create an app' and 'Request an access token'
* Put the spotify credentials in the .env file in the following format
  ```
  CLIENT_ID='your spotify api id'
  CLIENT_SECRET='your spotify api key'
  ```
* Note: The Spotify integration uses spotdl 4.2.10 for downloading tracks. This version is pinned in requirements.txt to ensure compatibility.

To get started with documentation:
Open docs/index.html
