"""
This file is the main entry point for users attempting to use this library from the command line or some other program
Usage would be something like python -m VibeMatch [arguments]
"""
try:
    import frontend
except Exception as local_import_error:
    print("Not running locally:", local_import_error)
    import VibeMatch.frontend as frontend


if __name__ == "__main__":
    frontend.main()
