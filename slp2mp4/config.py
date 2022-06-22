import os, json, sys
import shutil
from paths import Paths

class Config:
    def __init__(self):
        self.paths = Paths()
        with open(self.paths.config_json, 'r') as f:
            j = json.loads(f.read())
            self.melee_iso = os.path.expanduser(j['melee_iso'])
            self.check_path(self.melee_iso)
            self.dolphin_dir = os.path.expanduser(j['dolphin_dir'])
            self.paths.dolphin_dir = self.dolphin_dir
            self.check_path(self.dolphin_dir)
            self.ffmpeg = os.path.expanduser(shutil.which(j['ffmpeg']))
            self.check_path(self.ffmpeg)
            self.resolution = j['resolution']
            self.video_backend = j['video_backend']
            self.widescreen = j['widescreen']
            self.bitrateKbps = j['bitrateKbps']
            self.parallel_games = j['parallel_games']
            self.remove_short = j['remove_short']
            self.combine = j['combine']

        self.dolphin_bin = self.paths.dolphin_bin
        self.check_path(self.dolphin_bin)

    def check_path(self, path):
        if not os.path.exists(path):
            raise RuntimeError("{} does not exist".format(path))
