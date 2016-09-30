"""
Common test functions used across test files.
"""
import os


def make_fixture_path(folder, filename='lambda.py'):
    """
    Make path to fixture using  given args.

    folder (str): Folder name that contains fixture(s)
    filename (str): Filename to pass, if ``None`` will return folder
    """
    path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), 'fixtures', folder
        )
    )
    if filename:
        path = os.path.join(path, filename)
    return path
