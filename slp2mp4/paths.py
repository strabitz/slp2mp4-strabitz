import sys
import os
import shutil
import pathlib

class Paths:
    def __init__(self, dolphin_dir='', user_dir=''):
        self._this_dir = os.path.split(os.path.abspath(__file__))[0]
        self._windows = sys.platform == 'win32'
        if self._windows:
            self.config_json = os.path.join(self._this_dir, 'config_windows.json')
        else:
            self.config_json = os.path.join(self._this_dir, 'config.json')
        self.dolphin_dir = dolphin_dir
        self.user_dir = user_dir

    @property
    def dolphin_dir(self):
        return self._dolphin_dir

    @dolphin_dir.setter
    def dolphin_dir(self, d):
        self._dolphin_dir = d
        if self._windows:
            self.dolphin_bin = os.path.join(self._dolphin_dir, 'Slippi Dolphin.exe')
            self.gale01r2_ini = os.path.join(self._dolphin_dir, 'Sys', 'GameSettings', 'GALE01r2.ini')
        else:
            self.dolphin_bin = os.path.join(self._dolphin_dir, 'Slippi Launcher', 'playback', 'Slippi_Playback-x86_64.AppImage')
            self.gale01r2_ini = os.path.join(self._dolphin_dir, 'Slippi Launcher', 'playback', 'Sys', 'GameSettings', 'GALE01r2.ini')

    @property
    def user_dir(self):
        return self._user_dir

    @user_dir.setter
    def user_dir(self, d):
        self._user_dir = d
        self.user_gale01_ini = os.path.join(self._user_dir, 'GameSettings', 'GALE01.ini')
        self.user_gfx_ini = os.path.join(self._user_dir, 'Config', 'GFX.ini')
        self.user_dolphin_ini = os.path.join(self._user_dir, 'Config', 'Dolphin.ini')
        # TODO: Different in windows?
        self.user_dump_dir = os.path.join(self._user_dir, 'Dump')

    def copy_inis(self):
        if self._windows:
            shutil.copytree(os.path.join(self._dolphin_dir, 'User', self.user_dir))
        else:
            paths = [pathlib.Path(p).parent for p in [
                self.user_gale01_ini,
                self.user_gfx_ini,
                self.user_dolphin_ini,
            ]]
            for p in paths:
                p.mkdir(parents=True, exist_ok=True)

            # Copies config files to correct location
            sys_gale01_ini = os.path.join(self._dolphin_dir, 'SlippiOnline', 'GameSettings', 'GALE01.ini')
            sys_gfx_ini = os.path.join(self._dolphin_dir, 'SlippiPlayback', 'Config', 'GFX.ini')
            sys_dolphin_ini = os.path.join(self._dolphin_dir, 'SlippiPlayback', 'Config', 'Dolphin.ini')

            ini_paths = [
                (sys_gale01_ini, self.user_gale01_ini),
                (sys_gfx_ini, self.user_gfx_ini),
                (sys_dolphin_ini, self.user_dolphin_ini),
            ]

            for sys, user in ini_paths:
                shutil.copy(sys, user)
