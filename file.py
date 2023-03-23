import os

import ffmpeg
from PIL import Image


# noinspection PyUnresolvedReferences
class File:
    def get_fileinfo(self, filename: str, ffprobe='ffprobe.exe'):
        response = {
            "file_name": os.path.split(filename)[-1],
            "file_size": os.path.getsize(filename),
            "last_modify_date": os.path.getctime(filename),
            "file_type": None,
            "extra": {}
            # "tag": None,
        }
        filetype = self.get_filetype(filename)
        if filetype == 'image':
            try:
                image = Image.open(filename)
                response["extra"]["width"] = image.width
                response["extra"]["height"] = image.height
                response["file_type"] = filetype
            except Image.UnidentfiedImageError:
                response["extra"] = {}
                response["file_type"] = 'other'
        elif filetype == 'video':
            try:
                video = ffmpeg.probe(filename, ffprobe)
                # print(video)
                fps = round(int(video['streams'][0]['r_frame_rate'].split('/')[0]) / int(
                    video['streams'][0]['r_frame_rate'].split('/')[1]), 2)
                duration = round(float(video['format']['duration']), 2)
                response["extra"]["time"] = duration
                response["extra"]["size"] = {
                    "width": video['streams'][0].get("width", -1),
                    "height": video['streams'][0].get("height", -1)
                }
                response["extra"]["fps"] = fps
                response["file_type"] = filetype
            except ffmpeg.Error:
                response["extra"] = {}
                response["file_type"] = 'other'
        else:
            response["extra"] = {}
            response["file_type"] = 'other'

        return response
