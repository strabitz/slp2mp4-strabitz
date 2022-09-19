# slp to mp4

`slp2mp4` converts [Project Slippi][slippi] replay files for [Super Smash Bros.
Melee][ssbm] to mp4 videos.

The goal is to make it easy to batch-convert replays to HD video without screen
recording software.

## Dependencies

- [Python][python] >= 3.7

- [ffmpeg][ffmpeg] for combining the raw the video and audio streams

- A 'playback build' of Dolphin. This is a special Dolphin used for playing
  back Slippi replays.

	- If your replays are from the latest rollback Slippi (e.g. 2.2.3) you
	  can get the playback dolphin by installing the [Slippi Desktop
	  App][slippi-download]

	- For older replays, you can use [Faster Melee][faster-melee]

- A Super Smash Bros. Melee v1.02 NTSC ISO.

## Setup

First, install [python]. Make sure you have at least Python 3.7 installed.
While installing, be sure to check that `pip` should be installed as well, and
that Python should be added to your environment variables.

Now, in a command window, run the following command:

```
pip install git+https://github.com/davisdude/slp2mp4
```

The same command can be used to update to the latest version at any time. Note
that this will reset all settings.

## Usage

```
usage: slp2mp4 run [-h] [-o dir] path [path ...]

positional arguments:
  path                  Slippi files/directories containing slippi files to convert

options:
  -h, --help            show this help message and exit
  -o dir, --output_directory dir
                        Directory to put created mp4s
```

This launches Dolphin, which plays the replay and dumps frames and audio. Then
ffmpeg is invoked to combine audio and video.

```
Event/
      a.slp
      b.slp
      c.slp
      Game_1/
             d.slp
             e.slp
             f.slp
      Game_2/
             g.slp
             h.slp
             i.slp
```

gives

```
./OUTDIR/Event.mp4
./OUTDIR/Event-Game_1.mp4
./OUTDIR/Event-Game_2.mp4
```

Where `./` is the directory in which the command was run and `OUTDIR` is the
(optional) prefix given if you want all videos to show up in a specific spot.
Additionally, `Event.mp4` is made up of `a.slp`, `b.slp`, and `c.slp`,
`Event-Game_1.mp4` is made up of `d.slp`, `e.slp`, and `f.slp`, and so on.

---

## Configuration

To enter configuration mode, run

```
slp2mp4 config
```

**NOTE**: Unfortunately, you will need to redo the configuration each time you
update.

From here, you will see several fields (described below), which you can
configure by entering text and hitting `enter`.

There are several configuration options that you can control:

- `'melee_iso'` is the path to your Super Smash Bros. Melee 1.02 ISO.

- `'dolphin_dir'` and `'ffmpeg'` in linux need to be set to the playback path
  in the installed version of dolphin, and the default installed path of
  ffmpeg. In windows, these dependencies are downloaded and installed in the
  local directory so there is no need to change the paths; 'ffmpeg' can also be
  the command name if it's in your PATH

- `'resolution'` can be set to the following. The output resolution is the
  minimum resolution dolphin can run above the resolution in this
  configuration.

	- 480p
	- 720p
	- 1080p
	- 1440p
	- 2160p

- `'video_backend'` is the graphics backend you want to use. Currently, this
  can either be `"OGL"` for OpenGL, or `"D3D"` for Direct3D (Windows only).
  OpenGL is the default, as Direct3D can give strange cropping results when
  dumping in non-widescreen mode. Plus, it tends to be faster and gives fewer
  visual artifacts.

- `'widescreen'` can be `true` or `false`. Enabling will set the resolution to
  16:9

- `'bitrateKbps'` must be a number. It selects the bitrate in Kilobits per
  second that dolphin records at.

- `'parallel_games'` must be a number greater than 0, or `"recommended"`. This
  is the maximum number of games that will run at the same time.
  `"recommended"` will select the number of physical cores in the CPU.

- `'remove_short'` can be `true` or `false`. Enabling will not record games
  less than 30 seconds. Most games less than 30 seconds are handwarmers, so it
  can save time not to record them.

- `'combine'`: can be `true` or `false`, and matters only when recording a
  folder of `.slp` files. If `false`, the `.mp4` files will be left in their
  subfolders in the output folder. If `true`, each subfolder of `.mp4` files
  will be combined into `.mp4` files in the output folder.

- `remove_slps`: can be `true` or `false`; if `true`, remove slp files after
  they've been converted into mp4s.

## Performance

Resolution, widescreen, bitrate, and the number of parallel games will all
affect performance. Dolphin will not record well (skips additional frames) when
running less than or greater than 60 FPS. It becomes noticeable below 58 FPS.
YouTube requires a resolution of at least 720p to upload a 60 FPS video, so it
should be a goal to run at that resolution or higher. A higher bitrate will
come with better video quality but larger file size and worse performance
because dolphin has more to encode. The number of parallel games will have the
largest effect on performance. The 'recommended' value is the number of
physical cpu cores, but greater or fewer parallel games may be optimal.

## Future work

- Make installation/setup easier

	- There was previously an auto-installer for ffmpeg + playback dolphin
	  on windows, but it relied on a direct download of the playback
	  dolphin, which isn't available for the latest slippi

	- Would be nice to remove dependencies on py-slippi and psutil somehow.

	- Package everything in a release

- Multiprocessing

	- Allow combining after all required files are done recording while
	  multiprocessing

	- Better progress reporting

	- Warning on completion if average runtime frame rate is below 58 fps

- Run Dolphin at higher emulation speed if possible

- Improve config script experience

	- Open file explorer / at least enable tab completion

	- Change default playback dir for Linux to `~/.config/Slippi Launcher/playback`

	- Don't overwrite config on update

- GUI

	- At least simple batch script people can drop files/folders onto

[faster-melee]: https://www.smashladder.com/download/dolphin/18/Project+Slippi+%28r18%29
[ffmpeg]: https://ffmpeg.org/download.html
[python]: https://www.python.org/downloads/
[slippi-download]: https://slippi.gg/downloads
[slippi]: https://github.com/project-slippi/project-slippi
[ssbm]: https://en.wikipedia.org/wiki/Super_Smash_Bros._Melee
