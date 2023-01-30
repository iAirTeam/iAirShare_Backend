import os
from typing import Optional

from .vars import *

def get_file_full_path(filename) -> Optional[str]:
    path = os.path.join(os.path.abspath(config.get('files_path', "./files")), filename)  # flag
    return path if os.path.exists(path) else None


def safe_filename(filename: str):
    seps = os.path.sep + os.path.altsep + '/\\$\'\"'
    for sep in seps:
        if sep:
            filename = filename.replace(sep, "_")
    filename.replace('..', '_')

    # on nt a couple of special files are present in each folder.  We
    # have to ensure that the target file is not such a filename.  In
    # this case we prepend an underline
    nt_badnames = ("CON", "AUX", "COM1", "COM2", "COM3", "COM4", "LPT1", "LPT2", "LPT3", "PRN", "NUL")
    if (os.name == "nt"
            and filename
            and filename.split(".")[0].upper() in nt_badnames):
        filename = f"_{filename}"

    return filename


def get_filetype(filename: str):
    ext = os.path.splitext(filename)[-1].lower()
    if ext in image_ext:
        return 'image'
    elif ext in video_ext:
        return 'video'
    else:
        return 'other'


def get_filelist(self, path: str, ffprobe='ffprobe.exe'):
    response = {
        "filelist": []
    }

    for file in os.listdir(path):
        filename = os.path.join(os.path.abspath(path), file)
        if os.path.isfile(filename):
            try:
                fileinfo = self.get_fileinfo(filename, ffprobe)
                response["filelist"].append(fileinfo)
                response["count"] += 1
            except Exception as e:
                print(filename, e)
        else:
            pass

    return response
