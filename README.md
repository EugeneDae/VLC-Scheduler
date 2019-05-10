# VLC Scheduler

**[DOWNLOAD](https://github.com/EugeneDae/VLC-Scheduler/releases/latest/) / Windows & macOS / current version: 0.3.2.**

Do you have a TV screen that plays media content non-stop? Do you want some of the content to play in the morning, and the rest during the rest of the day? Do you want to add new content to VLC as easily as dragging the file into a folder? VLC Scheduler, which is a tiny companion to the world’s best open source media player VLC, was made exactly for such purposes.

![VLC Scheduler](/docs/screenshot.png)

VLC Scheduler works with directories rather than individual media files. It scans the directories specified in its configuration file for media content, composes its own playlist and “feeds” it to VLC file-by-file.

You can share a directory with TV screen content over the local network (for example, via SMB or FTP) with your coworkers or family members. When they add or remove media files, VLC Scheduler would track those changes and update its playlist accordingly.

### Features
- **Directory watching.**
- **Equal intermixing.** No matter how big or small the directories with media content are, VLC Scheduler will ensure that their media files appear equally often in the playlist. For example, if you have two directories — one with several files (`A1, A2, A3, A4`) and one with just a single file (`B1`) — the resulting playlist would be: `A1, B1, A2, B1, A3, B1, A4, B1`. This behavior can be changed using the `source_mixing_function` parameter.
- **Basic scheduling.** Set playing hours for specific directories using the `playing_hours` parameter. Also — if the filename of a media file contains a date in the format that VLC Scheduler can recognize (e.g. `23-02-2019_birthday.mp4`), the file will only be played during that day.
- **Directories for special occasions.** If a directory that is marked “special” (`special: true`) contains one or more files, VLC Scheduler will only play those files — and nothing else — until they’re removed from the “special” directory. You will find this feature useful on the occasions when you need to air something of immediate importance, while putting aside all “regular” content.
- **Plays long videos in short pieces.** For example, if you want to use your TV screen as a digital photo frame that alternates between different views, and each view is an hours long video file, use the `item_play_duration` parameter. Set it to `600` (seconds) and VLC Scheduler will change the view every 10 minutes. VLC will play the video from where it was left off if you configure VLC to [always continue playback](https://www.vlchelp.com/restart-continue-playback-ask/). 
- **Supports images (JPEG, PNG...)** Use `image_play_duration` or `item_play_duration` to control for how long they should be shown.
- **Supports live streams.** Turn your TV screen into a “digital window” that shows the live picture from various places around the world. Show a live stream, then in five minutes switch to a video on the hard drive, then show another live stream and so on — VLC Scheduler can arrange that. (See [docs/dam-square.xspf](/docs/dam-square.xspf)).
- **Show content every X minutes** — useful for ads, commercials, safety instructions etc, that you don’t want to show too often.
- Written in Python, VLC Scheduler can be used on Windows, macOS and Linux. The binaries for Windows and macOS are provided for download. Linux users should see **Running & building the script**.

### Caveats
- VLC Scheduler is not an add-on to VLC. It’s a separate application that runs alongside VLC and controls it. Do not try to control VLC yourself while VLC Scheduler is running.
- VLC Scheduler isn’t meant to replace digital signage software such as [Xibo](https://xibo.org.uk/). It was created for simpler use cases, for which VLC alone is *almost* good enough.
- VLC Scheduler doesn’t expose its internal playlist to VLC and you can’t change it, because VLC Scheduler doesn’t come with a user interface of any kind. You can configure VLC Scheduler only through its configuration file in [YAML format](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html). For changes in the configuration file to take effect, VLC Scheduler needs to be restarted.
- VLC Scheduler only supports per directory configuration. In other words, it doesn’t allow setting air time or duration for individual files. If you want one video file to play in the morning and another one to play in the evening, put them into two separate directories and add those directories to vlcscheduler.yaml with different `playing_time`.
- VLC Scheduler is still a “beta” and may contain terrible bugs.

## Installation & configuration
1. [Download the latest version](https://github.com/EugeneDae/VLC-Scheduler/releases/latest/). **vlcscheduler-win.zip** is for Windows, **vlcscheduler-mac.zip** is for macOS. If you’re on Linux, see **Running & building the script**.
2. Edit vlcscheduler.yaml as per your needs.

### vlcscheduler.yaml

vlcscheduler.yaml must reside at the same level as the program itself. *(Advanced users, who want to move the configuration file to another location, should set the environment variable `VLCSCHEDULER_YAML` to the full path that includes the filename of the configuration file)*.

*macOS High Sierra/Mojave users: if you're getting the following error: `FileNotFoundError: Cannot find <...> vlcscheduler.yaml in any of these places: <...>/T/AppTranslocation/<...>`, [see the solution here](https://github.com/EugeneDae/VLC-Scheduler/issues/11#issuecomment-491338627).*

The configuration must be expressed in YAML — if you don’t know anything about this format, [read up on it a bit](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html).

The only required parameter is `sources`. In VLC Scheduler’s terms, a **source** is a path to the directory with media files, followed by the parameters that define how VLC Scheduler should play those media files.

Minimal configuration example:

```
sources:
    - path: C:\Users\Administrator\Desktop\Videos
```

Now, let’s set `playing_time`:

```
sources:
    - path: C:\Users\Administrator\Desktop\Videos
      playing_time: 09:00-22:00
```

Not hard, right? [See also example.yaml](/docs/example.yaml).

#### Per source configuration

**`path`** — *(required)* absolute path to the directory with media files. `~/` and variables are not supported.

**`playing_time: HH:MM-HH:MM`** — *(optional)* the time interval during which the media files from the directory should be played. Use 24-hour clock. Example: `playing_time: 09:00-22:00` (from 9 AM to 10 PM).

**`shuffle: true/false`** — *(optional)* if set to `true`, shuffles the media files from each directory. If set to `false`, VLC Scheduler will get the files in alphabetic order. Default: `false`.

**`recursive: true/false`** — *(optional)* if set to `true`, recurses into subfolders of each directory. Default is value of global config media_recursive which is itself defaulted to `false`.

**`special: true/false`** — *(optional)* if set to `true`, marks a directory as special. Special directories are meant to stay empty most of the time. When a media file is added to such directory, VLC Scheduler puts aside all non-special content and only plays that file until it’s removed from its directory. Default: `false`.

**`item_play_duration: seconds`**— *(optional)* how much screen time each media file (an image or a video) should be given.

- If `item_play_duration` is not set, each video will play until the end and each image will play for the time defined by `image_play_duration` (which is — by default — 60 seconds). Note that `image_play_duration` is a top-level (general) parameter.
- If a video is shorter than `item_play_duration`, it’ll play over again until `item_play_duration` runs out.
- If a video is longer than `item_play_duration`, it’ll play only until `item_play_duration` runs out. When it comes up again in the playlist, it’ll play from the start — unless VLC is configured to [continue playback without asking](https://www.vlchelp.com/restart-continue-playback-ask/).

Example: `item_play_duration: 120` (120 seconds = 2 minutes).

**`play_every_minutes: minutes`** — *(optional)* the content will be played only after X minutes. Such content is internally referred to as “ads”. If there is no content other than the “ads”, VLC Scheduler won’t play anything. VLC Scheduler doesn’t “pause” the currently playing media file to play “ads” — instead it waits for the media file to complete. The use of this parameter in conjunction with `special: true` is not supported. Example: `play_every_minutes: 30`.

#### General configuration

**`source_mixing_function: "function_name"`** — *(optional)* If you don’t want VLC Scheduler to ensure equal occurrence of the sources in the playlist, change this to `chain`. Default value: `zip_equally`.

**`media_extensions: [...]`** — *(optional)* a list of filename extensions that defines the kinds of **media files** that VLC Scheduler should be looking for when scanning the directories listed in `sources`. Note that each filename extension should be prepended with a dot and written in lowercase. Note that VLC Scheduler does not understand that `.jpeg` and `.jpg` belong to the same file format. Example: `media_extensions: ['.mp4', '.avi', '.jpeg', '.jpg']`. For the default list of extensions see [defaults.py](/src/defaults.py).

**`media_recursive: true/false`** — *(optional)* sets the default value for recursion of all sources. Default: `false`

**`playlist_extensions: [...]`** — *(optional)* a list of filename extensions that defines the kinds of **playlist files** that VLC Scheduler should be looking for when scanning the directories listed in `sources`. Note that each filename extension should be prepended with a dot and written in lowercase. Example: `playlist_extensions: ['.xspf', '.m3u']`. For the default list of extensions see [defaults.py](/src/defaults.py).

**`ignore_playing_time_if_playlist_is_empty: true/false`** — *(optional)* if set to `true`, VLC Scheduler will ignore `playing_time` of the sources if the playlist is empty. Default value: `false`.

**`image_play_duration: seconds`** — *(optional)* how long an image should be displayed on the screen if `item_play_duration` is not set for the source. Default value: `60`.

**`vlc`** — *(optional)* a dictionary of VLC-related parameters.

```
vlc:
    # Path to VLC
    path: '/Applications/VLC.app/Contents/MacOS/VLC'
    
    # VLC HTTP server host — change only if you know what you’re doing
    host: '127.0.0.1'
    
    # VLC HTTP server port — change only if you know what you’re doing
    port: 8080
    
    # VLC HTTP server password — change if you need more security
    password: 'vlcremote'
    
    # Extra interfaces — change only if you know what you’re doing
    extraintf: 'http,luaintf'
```

## Running & building the script

**(Advanced users only).**

### Python

Check your Python version with: `python3 --version`.

If you want to make a binary, make sure to have Python 3.6 (see https://www.python.org/downloads/), because [PyInstaller](https://www.pyinstaller.org/), the tool used to make VLC Scheduler into a binary, does not support Python 3.7 yet (as of writing).

If you just want to run VLC Scheduler as a Python script, you can use either Python 3.6 or 3.7.

### Running
1. Check if you already have **virtualenv**: `virtualenv --version`. If you don’t:

        pip3 install virtualenv

2. [Download and extract the source code](/archive/master.zip) (or do `git clone`) and `cd` into the directory.

3. Create a new virtual environment and activate it.

    macOS or any other *nix:

        virtualenv venv --python=python3
        source venv/bin/activate

    Windows:

        virtualenv venv --python=python3
        call venv\Scripts\activate

4. Install the dependencies:

        pip install -r requirements.pip

5. Create vlcscheduler.yaml and add at least one `path` to `sources`.

6. Run the script:

        python src/vlcscheduler.py

### Building

On Windows:

    Make.bat

On macOS:

    make

In theory `make` should also work on Linux, but it hasn’t been tested.

If everything goes fine, you will find either `vlcscheduler.exe` (on Windows) or `VLC Scheduler.app` (on macOS) in `dist` directory.

## Credits & license

Created by **Eugene / Dae** (dae@dae.me).

VLC folder icon by [scafer31000](http://scafer31000.deviantart.com/).

License: MIT, see [LICENSE](LICENSE).

**Special thanks to:**

- VideoLAN organization and all of its contributors for creating VLC.
- Sergey Karnaukhov for testing.
