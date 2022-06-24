#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, uuid, multiprocessing, psutil, glob
from pathlib import Path
from slippi import Game
from config import Config
from dolphinrunner import DolphinRunner
from ffmpegrunner import FfmpegRunner

VERSION = '1.0.0'
USAGE = """\
slp-to-mp4 {}
Convert slippi files to mp4 videos

USAGE: slp-to-mp4.py REPLAY_FILE [OUT_FILE]

Notes:
OUT_FILE can be a directory or a file name ending in .mp4, or omitted.
e.g.
This will create my_replay.mp4 in the current directory:
 $ slp-to-mp4.py my_replay.slp

This will create my_video.mp4 in the current directory:
 $ slp-to-mp4.py my_replay.slp my_video.mp4

This will create videos/my_replay.mp4, creating the videos directory if it doesn't exist
 $ slp-to-mp4.py my_replay.slp videos

See README.md for details
""".format(VERSION)

FPS = 60
MIN_GAME_LENGTH = 30 * FPS
DURATION_BUFFER = 70              # Record for 70 additional frames

# Paths to files in (this) script's directory
SCRIPT_DIR, _ = os.path.split(os.path.abspath(__file__))
if sys.platform == "win32":
    THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config_windows.json')
else:
    THIS_CONFIG = os.path.join(SCRIPT_DIR, 'config.json')
OUT_DIR = os.path.join(SCRIPT_DIR, 'out')


def is_game_too_short(num_frames, remove_short):
    return num_frames < MIN_GAME_LENGTH and remove_short


def get_num_processes(conf):
    if conf.parallel_games == "recommended":
        return psutil.cpu_count(logical=False)
    else:
        return int(conf.parallel_games)


def clean():
    for folder in glob.glob("User-*"):
        shutil.rmtree(folder)
    for file in glob.glob("slippi-comm-*"):
        os.remove(file)

# Evaluate whether file should be run. The open in dolphin and combine video and audio with ffmpeg.
def record_file_slp(slp_file, outfile):
    conf = Config()

    # Parse file with py-slippi to determine number of frames
    slippi_game = Game(slp_file)
    num_frames = slippi_game.metadata.duration + DURATION_BUFFER

    if is_game_too_short(slippi_game.metadata.duration, conf.remove_short):
        print("Warning: Game is less than 30 seconds and won't be recorded. Override in config.")
        return

    with DolphinRunner(conf, conf.paths, SCRIPT_DIR, uuid.uuid4()) as dolphin_runner:
        video_file, audio_file = dolphin_runner.run(slp_file, num_frames)

        # Encode
        ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
        ffmpeg_runner.run(video_file, audio_file, outfile)

        print('Created {}'.format(outfile))


# Given a list of mp4s, does the basic prep and cleanup work for ffmpeg runner
def combine(mp4s, conf):
    # TODO: Worry about escaping filenames?
    # Creates concat file
    outdir = os.path.dirname(mp4s[0])
    basedir = os.path.basename(outdir)
    concat_file = os.path.join(outdir, 'concat_file.txt')
    final_mp4_file = os.path.join(OUT_DIR, basedir + '.mp4')
    with open(concat_file, 'w') as file:
        for mp4 in mp4s:
            file.write(f"file '{mp4}'\n")

    # Combines files
    ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
    ffmpeg_runner.combine(concat_file, final_mp4_file)

    # Cleanup
    shutil.rmtree(outdir)


# Get a list of the input files and their subdirectories to prepare the output files. Feed this to record_file_slp.
# If combine is true, combine the files in the out folder every time there is a new subdirectory.
def record_folder_slp(slp_folder, conf):
    slps_to_record = []
    mp4s_to_combine = {}

    # Get a list of the input files and their subdirectories. The output file will use the basename of the subdirectory
    # and the name of the file without the extension
    for subdir, dirs, files in os.walk(slp_folder):
        for file in files:
            if file.endswith('.slp'):
                slp_name = os.path.join(subdir, file)
                out_dir = os.path.join(OUT_DIR, os.path.basename(subdir))
                mp4_name = os.path.join(
                    out_dir,
                    '.'.join(file.split('.')[:-1]) + '.mp4'
                )

                # Skips mp4s that already exist
                # TODO: Should this be part of record_file_slip instead?
                if os.path.exists(mp4_name):
                    print(f'mp4 for {file} already exists - skipping')
                    continue

                slps_to_record.append((slp_name, mp4_name))

                # Makes the needed directory in the output if needed
                if not os.path.isdir(out_dir):
                    os.makedirs(out_dir)

                if conf.combine:
                    if subdir not in mp4s_to_combine:
                        mp4s_to_combine[subdir] = []
                    mp4s_to_combine[subdir].append(mp4_name)

    if len(slps_to_record) == 0:
        RuntimeError('No slp files in folder!')

    # Start recording
    num_processes = get_num_processes(conf)
    pool = multiprocessing.Pool(processes=num_processes)
    pool.starmap(record_file_slp, slps_to_record)
    pool.close()

    # Combines mp4s
    for mp4s in mp4s_to_combine.values():
        mp4s.sort()
        combine(mp4s, conf)

def main():

    # Parse arguments

    if len(sys.argv) == 1 or '-h' in sys.argv:
        print(USAGE)
        sys.exit()

    slp_file = os.path.abspath(sys.argv[1])
    clean()
    os.makedirs(OUT_DIR, exist_ok=True)

    # Handle all the outfile argument possibilities
    outfile = ''
    if len(sys.argv) > 2:
        outfile_name = ''
        outdir = ''
        if sys.argv[2].endswith('.mp4'):
            outdir, outfile_name = os.path.split(sys.argv[2])
        else:
            outdir = sys.argv[2]
            outfile_name, _ = os.path.splitext(os.path.basename(slp_file))
            outfile_name += '.mp4'

        # We need to remove '..' etc from the path before making directories
        outdir = os.path.abspath(outdir)
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, outfile_name)
    else:
        outfile, _ = os.path.splitext(os.path.basename(slp_file))
        outfile += '.mp4'
        outfile = os.path.join(OUT_DIR, outfile)

    if os.path.isdir(slp_file):
        conf = Config()
        record_folder_slp(slp_file, conf)
    else:
        record_file_slp(slp_file, outfile)


if __name__ == '__main__':
    main()
