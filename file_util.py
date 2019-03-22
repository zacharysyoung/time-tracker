"""
Simple file-system operations.
"""

def append_file_with_data(fpath, data, mode='a+b'):
    """Open a file and append to it."""
    with open(fpath, mode) as f:
        f.write(data)

def del_path(p, ignore_error=None):
    """Remove a file, not a directory."""
    import os

    try:
        os.remove(p)
    except OSError as e:
        if e.errno != ignore_error:
            raise
