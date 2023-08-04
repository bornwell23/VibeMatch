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


To set up the environment:
* ensure python is installed (Click the big yellow "Download Python 3.#.#" button on https://www.python.org/downloads/ and during installatation make sure python is in the path)
* ensure python is in the path by opening up a terminal and typing python --version, if not, view this site for more info https://realpython.com/add-python-to-path/
* install requirements.txt ( in a terminal, run `python -m pip install -r requirements.txt``)

For development only:
* set up your IDE
  * if using Pycharm
    * Open settings, search for Python Integrated Tools
      * set default test runner to pytest
      * set docstring format to Google
  * if using Visual Studio
    * Open settings, search enable pytest and enable it
    * I suggest installing autoDocstring from the extension marketplace (Ctrl+Shift+X, type autoDocstring)
* run tests via command `python -m pytest test.py`)`

To run the program manually:
* run the setup script for your system (Mac -> setup_unix.sh, Windows -> setup_windows.bat)
* run the command `vibe -h` (type `vibe -h`` and press enter)

To get started with documentation:
Open docs/index.html
