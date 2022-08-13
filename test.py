import sys
import pytest
import importlib
from inspect import getmembers, isfunction


def import_libs(libs):
    """
    Imports a list of libraries to ensure they can be loaded
    Args:
        libs:

    Returns:

    """
    error_libs = []
    for lib in libs:
        try:
            importlib.import_module(lib.strip())
        except Exception as import_exception:
            error_libs.append(f"{import_exception}")
    if len(error_libs):
        raise ImportError(f"Unable to import the following libraries: {','.join(error_libs)}. " +
                          "Please run pip install -r requirements.txt")


def test_libs():
    """
    Imports the libraries included in the requirements file to ensure they can all be used
    """
    with open("requirements.txt") as reqs:
        libs = reqs.readlines()
        import_libs(libs)


def test_missing_libs():
    import os
    for root, dirs, files in os.walk("/mydir"):
        for file in files:
            if file.endswith(".txt"):
                print(os.path.join(root, file))


def test_dummy():
    assert 2 == 2, "2 does not equal 2!?"
    with pytest.raises(Exception):
        assert 2 == 3, "2 equals 3!?"


if __name__ == "__main__":  # main entry point
    args = sys.argv[1:]
    if len(args):
        for arg in args:  # check all command line parameters after the file name
            if arg in locals():  # checks if the parameter is a function in the current file
                locals()[arg]()  # runs the function
    else:
        # get all functions that start with 'test_' i.e. is a pytest function
        test_funcs = [local for local in locals().copy() if local.startswith("test_")]
        total = len(test_funcs)
        passed = 0
        failed = []
        for test in test_funcs:  # for every local attribute to this file
            try:
                locals()[test]()  # run the function
                print(f"Test '{test}' passed")
                passed += 1
            except Exception as test_error:
                fail_msg = f"Test '{test}' failed due to error: {test_error}"
                print(fail_msg)
                failed.append(test)
        print(f"{passed} of {total} ({(passed/total)*100}%) tests passed")
        if len(failed):
            print(f"Failing tests: {failed}")
