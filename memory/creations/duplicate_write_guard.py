#!/usr/bin/env python3
import os, tempfile, shutil

def atomic_write(path, content):
    dir_name = os.path.dirname(path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    fd, temp_path = tempfile.mkstemp(dir=dir_name)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        shutil.move(temp_path, path)
    except:
        os.remove(temp_path)
        raise
