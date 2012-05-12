import os


def filetype(filename):
    base, ext = os.path.splitext(filename)
    return ext[1:].lower()
