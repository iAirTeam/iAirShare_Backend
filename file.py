import os
import time
from PIL import Image
import ffmpeg


class File:
    def __init__(self):
        self.image_ext = [
            '.png', '.jpg', '.jpeg', '.apng', '.avif', '.bmp', '.gif', '.ico', '.cur', '.jfif',
            '.pjpeg', '.pjp', '.svg', '.tif', '.tiff', '.webp'
        ]
        self.video_ext = [
            '.mp4', '.webm', '.avi', '.ogg', '.mpeg', '.mkv'
        ]
        # self.audio_ext = [
        #     '.mp3',
        # ]

    @staticmethod
    def format_size(size: float, floor: int = 2):
        if size == 0:
            return "0B"
        if size / 1024 / 1024 / 1024 >= 1:
            return "{}Gib".format(round(size / 1024 / 1024 / 1024, floor))
        elif size / 1024 / 1024 >= 1:
            return "{}Mib".format(round(size / 1024 / 1024, floor))
        elif size / 1024 >= 1:
            return "{}Kib".format(round(size / 1024, floor))
        else:
            return "{}B".format(round(size, floor))

    def get_filetype(self, filename: str):
        ext = os.path.splitext(filename)[-1].lower()
        if ext in self.image_ext:
            return 'image'
        elif ext in self.video_ext:
            return 'video'
        # elif ext in self.audio_ext:
        #     return 'audio'
        else:
            return 'other'

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
            except Image.UnidentfiedImageError as e:
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
            except ffmpeg.Error as e:
                response["extra"] = {}
                response["file_type"] = 'other'
        else:
            response["extra"] = {}
            response["file_type"] = 'other'

        return response

    def get_filelist(self, path: str, ffprobe='ffprobe.exe', use_format: bool = False):
        response = {
            "count": 0,
            "fileinfo": []
        }

        for file in os.listdir(path):
            filename = os.path.join(os.path.abspath(path), file)
            if os.path.isfile(filename):
                try:
                    fileinfo = self.get_fileinfo(filename, ffprobe)
                    response["fileinfo"].append(fileinfo)
                    response["count"] += 1
                except Exception as e:
                    print(filename, e)
            else:
                pass


        return response
