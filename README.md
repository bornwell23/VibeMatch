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


To set environment:
* install requirements.txt (pip install -r requirements.txt)
* if using Pycharm
  * Open settings, search for Python Integrated Tools
    * set default test runner to pytest
    * set docstring format to Google
* run tests (python -m pytest test.py)

To get started:
Open docs/index.html
