import pathlib 
import os 
import fnmatch 
import re

def build_subpaths(source_folder, accept=['*.*'], check_exists=True):
    """ For a given source_folder return full Posix paths for all 
    subfolders/files given the regex pattern in accept. Defaults to all files.
    """
    subpaths = []
    for p in os.walk(source_folder):
        for f in p[-1]:
            for pattern in accept:
                if re.match(fnmatch.translate(pattern), f, re.IGNORECASE):
                    subpaths.append(pathlib.Path(p[0])/f)
    if check_exists:
        for s in subpaths:
            assert s.exists(), f'{s} does not exist'
    
    return subpaths


def posix_path_from_string(path_str, check_exists=True):
    """ Build a path, optionally assert that it exists. If true will 
    raise an AssertionError 
    """
    p = pathlib.Path(path_str)
    if check_exists:
        assert p.exists(), f'{p} does not exist'
    return p 


def path_splitter(path_str, after=''):
    """ split a path_str after a certain value and return a string of the 
    result. 
    """
    l = path_str.split('/')
    idx = l.index(after)
    before = '/'.join(l[:idx+ 1])
    after = '/'.join(l[idx+1:])
    return before, after 



def touch_filepath(path):
    """ Given a posix path will make a filepath if it doesn't exist. If it does then it does nothing 
    """ 
    dir_ = '/'.join(str(path).split('/')[:-1])  # split the file off so we can call mkdirs 
    pathlib.Path(dir_).mkdir(parents=True, exist_ok=True)


