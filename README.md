# Spotipyne
Gtk Spotify client written in python made to be compatible with mobile formfactors like a pinephone.

<img src="https://gitlab.com/dann-merlin/spotipyne/-/raw/master/assets/desktop_library.png" alt="Screenshot Desktop" title="Screenshot Desktop" height=600/>
<br/>
<img src="https://gitlab.com/dann-merlin/spotipyne/-/raw/master/assets/mobile_playlists.png" alt="Screenshot Mobile Playlist" title="Screenshot Mobile Playlist" height=600/>
<img src="https://gitlab.com/dann-merlin/spotipyne/-/raw/master/assets/mobile_tracks.png" alt="Screenshot Mobile Tracks" title="Screenshot Mobile Tracks" height=600/>
<br/>

These images use the Adwaita dark theme. One way enable it, is to set the environment variable GTK_THEME

``export GTK_THEME=Adwaita:dark``

Note: You need to have a spotify device running in order to play songs. This could for example be the official player or spotifyd.

# What works?

Not a lot yet. But here's a short list:

- play/pause
- list devices/select device
- list playlists
- list tracks inside a playlist
- start playing a track inside a playlist
- show playlist covers
- show album covers
- show progress bar
- search (playlists and tracks only really work yet)

# How can I use it?

For installation see below.

You need to set your spotify username as an environment variable.

``export SPOTIPYNE_USERNAME="my_username"``

I have not implemented a way to set it inside the application yet.

# Build dependencies

- meson
- ninja
- pip (optional - alternatively you might be able to install the python packages with your package manager)

# Dependencies

- gettext
- libhandy-1
- python3
- PyGObject >= 3.36
- pyxdg
- spotipy

# Building

The following instructions require that you already have all dependencies installed. However you can also just run:

``./build.sh``

This will check for the dependencies and tell you what needs to be installed.

It also automatically uses pip to install python dependencies.

To build Spotipyne run:

``
meson build
``

``
ninja -C build
``

I don't actually know how to run this application without installing it, so:

# Install

First build then do this:

To install run (with sudo):

``
ninja -C build install
``
