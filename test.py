import os
import sys
import pytest
import importlib


def import_lib(lib, explode=False):
    """
    Tries to import a library.
    If that doesn't work, it will return the exception as a string
    Args:
        lib: (string) the library name to import
        explode: (bool) whether or not to raise an exception

    Returns:
        the module, or an exception message
    """
    try:
        return importlib.import_module(lib.strip())
    except Exception as import_exception:
        if explode:
            raise import_exception
        else:
            return f"{import_exception}"


def import_libs(libs):
    """
    Imports a list of libraries to ensure they can be loaded
    Args:
        libs: (list) containing strings corresponding to modules to import
    """
    error_libs = []
    for lib in libs:
        imported = import_lib(lib)
        if isinstance(imported, str):  # failed to load, this is an exception string
            error_libs.append(imported)
    if len(error_libs):
        raise ImportError(f"Unable to import the following libraries: {','.join(error_libs)}. " +
                          "Please run 'pip install -r requirements.txt'")


def import_libs_with_paths(lib_list):
    """
    Imports a list of libraries to ensure they can be loaded
    Mentions the file path the import came from if the import fails
    Args:
        lib_list: (list of tuples containing two strings)
    """
    error_libs = []
    for lib, path in lib_list.items():
        imported = import_lib(lib)
        if isinstance(imported, str):  # failed to load, this is an exception string
            error_libs.append((lib, path, imported))
    if len(error_libs):
        errs = [f"Cannot import '{lib}' in {path} because: {err}" for lib, path, err in error_libs]
        err_str = '\n'.join(errs)
        import_str = ','.join([lib for lib, _, _ in error_libs])
        raise ImportError(f"Unable to import the following libraries: {err_str}. Please run 'pip install {import_str}'")


def get_required_libs():
    """
    Gets the list of required libs from requirements.txt
    Returns:
        (list) list of strings
    """
    with open("requirements.txt", 'r') as reqs:
        libs = reqs.readlines()
    return libs


def test_anything_works():
    """
    Asserts that tests are working
    """
    assert 2 == 2, "2 does not equal 2!?"
    with pytest.raises(Exception):
        assert 2 == 3, "2 equals 3!?"


def test_libs():
    """
    Imports the libraries included in the requirements file to ensure they can all be used
    """
    libs = get_required_libs()
    try:
        import_libs(libs)
    except ImportError as import_error:
        try:
            import subprocess
            subprocess.check_call("pip install -r requirements.txt".split(' '))
        except Exception:
            raise Exception(f"Unable to import libraries, and unable to run pip install automatically: {import_error}")


def test_missing_libs():
    """
    Checks for libraries used that are missing from requirements.txt, also tries to import them to ensure they exist
    """
    libs = dict()
    for root, dirs, files in os.walk("."):  # recursively traverses the current directory
        for file in files:  # the list of files for each respective directory
            if file.endswith(".py"):
                path_name = os.path.join(root, file)  # create the full path to use and print
                with open(path_name, 'r') as py_file:
                    txt = py_file.readlines()  # read all lines into a list
                    for line in txt:
                        if line.startswith("import "):
                            lib_to_import = line[line.find("import ")+7:].strip("\n \t")  # grab the library that's imported
                            libs[lib_to_import] = path_name
    import_libs_with_paths(libs)


if __name__ == "__main__":  # main entry point
    args = sys.argv[1:]
    if len(args):  # if there are any command line args
        for arg in args:  # check all command line parameters after the file name
            if arg in locals():  # checks if the parameter is a function in the current file
                locals()[arg]()  # runs the function
    else:
        # get all functions that start with 'test_' i.e. is a pytest function
        test_funcs = [local for local in locals().copy() if local.startswith("test_")]
        total = len(test_funcs)
        passed = 0
        failed = []
        for test in test_funcs:  # for every local attribute of this file that seems to be a test function
            try:
                locals()[test]()  # run the function
                print(f"Test '{test}' passed")
                passed += 1
            except Exception as test_error:
                fail_msg = f"Test '{test}' failed due to error: {test_error}"
                print(fail_msg)
                failed.append(test)
        print(f"{passed} of {total} ({(passed/total)*100:.2f}%) tests passed")
        if len(failed):  # any failed tests exist
            print(f"Failing tests: {failed}")
