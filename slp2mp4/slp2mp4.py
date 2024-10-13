#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, uuid, multiprocessing, glob
import argparse
import tempfile
from pathlib import Path
from collections import namedtuple
import zipfile

from slippi import Game
import psutil
import natsort
from youtube_uploader_selenium import YouTubeUploader

from config import Config
from dolphinrunner import DolphinRunner
from ffmpegrunner import FfmpegRunner

FPS = 60
MIN_GAME_LENGTH = 30 * FPS
DURATION_BUFFER = 70              # Record for 70 additional frames

###############################################################################
# Misc utils
###############################################################################
def is_game_too_short(num_frames, remove_short):
    return num_frames < MIN_GAME_LENGTH and remove_short

def get_num_processes(conf):
    if conf.parallel_games == "recommended":
        return psutil.cpu_count(logical=False)
    else:
        return int(conf.parallel_games)

def safe_remove_file(f):
    try:
        os.remove(f)
    except FileNotFoundError:
        pass

SlpMp4Obj = namedtuple('SlpMp4Obj', ['slp_file', 'outfile', 'conf'])
ToCombineObj = namedtuple('ToCombineObj', ['vids', 'outname'])

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    return extract_to

def is_zip(file_path):
    return file_path.lower().endswith('.zip')

def format_title(title_template, context):
    tournament = context['startgg']['tournament']['name']
    bracket = context['startgg']['event']['name']
    players = " vs ".join([slot['displayNames'][0] for slot in context['scores'][0]['slots']])
    return title_template.format(tournament=tournament, bracket=bracket, players=players)

###############################################################################
# YouTube upload
###############################################################################
def upload_to_youtube(video_path, metadata_path):
    uploader = YouTubeUploader(video_path, metadata_path)
    was_video_uploaded, video_id = uploader.upload()
    if was_video_uploaded:
        print(f"Video uploaded successfully. Video ID: {video_id}")
    else:
        print("Failed to upload video.")
    return was_video_uploaded, video_id

###############################################################################
# Run logic
###############################################################################
def record_file_slp(slp_file, outfile, conf):
    # Parse file with py-slippi to determine number of frames
    slippi_game = Game(slp_file)
    num_frames = slippi_game.metadata.duration + DURATION_BUFFER

    if is_game_too_short(slippi_game.metadata.duration, conf.remove_short):
        print("Warning: Game is less than 30 seconds and won't be recorded. Override in config.")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        with DolphinRunner(conf, conf.paths, tmpdir, uuid.uuid4()) as dolphin_runner:
            video_file, audio_file = dolphin_runner.run(slp_file, num_frames)

            # Encode
            ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
            ffmpeg_runner.run(video_file, audio_file, outfile)

            if conf.remove_slps:
                safe_remove_file(slp_file)

            print('Created {}'.format(outfile))

    # YouTube upload
    if conf.youtube_upload:
        context_file = os.path.join(os.path.dirname(slp_file), 'context.json')
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context = json.load(f)
            title = format_title(conf.youtube_title_template, context)
        else:
            title = os.path.basename(outfile)

        metadata = {
            "title": title,
            "description": conf.youtube_description,
            "tags": conf.youtube_tags,
            "privacyStatus": conf.youtube_privacy
        }
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
            json.dump(metadata, tmp)
            metadata_path = tmp.name

        upload_to_youtube(outfile, metadata_path)
        os.unlink(metadata_path)

def combine(mp4s, out, conf):
    # Creates concat file
    tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    for mp4 in mp4s:
        mp4 = os.path.abspath(mp4)
        print(mp4)
        tmp.write(f"file '{mp4}'\n")
    tmp.close()
    out = os.path.abspath(out)

    ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
    ffmpeg_runner.combine(tmp.name, out)

    os.unlink(tmp.name)

def is_slp(slp):
    return slp.endswith('.slp')

def get_mp4_name(slp):
    return '.'.join(os.path.splitext(slp)[:-1]) + '.mp4'

def record_files(infiles, outdir, conf):
    file_mappings = [] # [SlpMp4Obj, ...]
    to_combine = []    # [ToCombineObj, ...]
    individual_mp4s = []
    created_dirs = []

    # Determines groupings and output names
    for infile in infiles:
        # Handle zip files
        if is_zip(infile):
            zip_name = os.path.splitext(os.path.basename(infile))[0]
            extract_dir = os.path.join(os.path.dirname(infile), zip_name)
            extracted_path = extract_zip(infile, extract_dir)
            infile = extracted_path
            created_dirs.append(extract_dir)

        # Individual files just become mp4s and, if combined, are named `out.mp4`
        if os.path.isfile(infile):
            if not is_slp(infile):
                continue
            outfile = get_mp4_name(os.path.join(outdir, Path(infile).parts[-1]))
            file_mappings.append(SlpMp4Obj(infile, outfile, conf))
            individual_mp4s.append(outfile)

        # Directories get grouped/combined by level
        elif os.path.isdir(infile):
            parent = Path(os.path.abspath(infile)).parts[-1]
            for subdir, _, fs in os.walk(infile):
                cur_outdir = os.path.join(
                    outdir,
                    parent,
                    os.path.relpath(subdir, infile)
                )
                cur_combine = []
                for f in fs:
                    if not is_slp(f):
                        continue
                    mp4_name = os.path.join(cur_outdir, get_mp4_name(f))
                    file_mappings.append(SlpMp4Obj(os.path.join(subdir, f), mp4_name, conf))
                    cur_combine.append(mp4_name)

                # Skips empty directories
                if len(cur_combine) == 0:
                    continue

                if not Path(cur_outdir).is_dir():
                    created_dirs.append(cur_outdir)
                    os.makedirs(cur_outdir)
                cur_combine = natsort.natsorted(cur_combine)

                # Always give file some kind of meaningful name, at least
                idx = 1
                if len(Path(cur_outdir).parts):
                    idx = 0

                final_mp4_name = Path(subdir).name + '.mp4'
                to_combine.append(ToCombineObj(cur_combine, os.path.join(outdir, final_mp4_name)))

    if len(individual_mp4s) > 0:
        to_combine.append(ToCombineObj(individual_mp4s, os.path.join(outdir, 'out.mp4')))

    # Records mp4s
    num_processes = get_num_processes(conf)
    pool = multiprocessing.Pool(processes=num_processes)
    pool.starmap(record_file_slp, file_mappings)
    pool.close()

    # Combines mp4s
    if conf.combine:
        for files in to_combine:
            combine(files.vids, files.outname, conf)

        # Removes created directories
        for d in created_dirs:
            shutil.rmtree(d, ignore_errors=True)

        # Removes created files (if need be)
        for _, mp4, _ in file_mappings:
            safe_remove_file(mp4)

###############################################################################
# Argument parsing
###############################################################################
def config_script(_=None):
    print('Entering configuration script...')
    conf = Config(False)
    with open(conf.paths.config_json, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        for k, v in data.items():
            print(f"{k} (blank = '{v}'): ", end='')
            val = input()
            if val != '':
                data[k] = attempt_data_conversion(val)
        
        # YouTube options
        print("\nYouTube Upload Options:")
        data['youtube_upload'] = input("Enable YouTube upload? (true/false): ").lower() == 'true'
        if data['youtube_upload']:
            data['youtube_title_template'] = input("Enter title template (e.g. '{tournament} | {bracket} | {players}'): ")
            data['youtube_description'] = input("Enter video description: ")
            data['youtube_tags'] = input("Enter tags (comma-separated): ").split(',')
            data['youtube_privacy'] = input("Enter privacy status (public, unlisted, private): ")

        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

def run(args):
    os.makedirs(args.output_directory, exist_ok=True)
    while True:
        try:
            conf = Config()
            break
        except RuntimeError as e:
            print(e, file=sys.stderr)
            config_script()
    record_files(args.path, args.output_directory, conf)

# Parser configuration
def attempt_data_conversion(val):
    if val.lower() == 'false':
        return False
    elif val.lower() == 'true':
        return True
    else:
        try:
            return int(val)
        except ValueError:
            return val

def parser_is_file_or_dir(path):
    if os.path.isfile(path) or os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid file or directory")

parser = argparse.ArgumentParser(
    prog='slp2mp4',
    description='Convert slippi replay files for Super Smash Bros Melee to videos and optionally upload to YouTube',
)
subparser = parser.add_subparsers(
    title='mode',
    help='Choose which action to execute',
    required=True
)

config_parser = subparser.add_parser('config', help='Run configuration helper')
config_parser.set_defaults(func=config_script)

run_parser = subparser.add_parser('run', help='Convert slps to mp4s and optionally upload to YouTube')
run_parser.set_defaults(func=run)
run_parser.add_argument(
    '-o', '--output_directory',
    metavar='dir',
    help='Directory to put created mp4s',
    type=str,
    default='.',
)
run_parser.add_argument(
    'path',
    help='Slippi files/directories containing slippi files to convert',
    default='.',
    nargs='+',
    type=parser_is_file_or_dir,
)

def main():
    # Parse arguments
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()