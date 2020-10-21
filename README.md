# Spotipyne
Gtk Spotify client written in python made to be compatible with mobile formfactors like a pinephone.

![Screenshot Desktop](https://gitlab.com/dann-merlin/spotipyne/-/raw/master/assets/desktop_library.png)
![Screenshot Mobile Playlist](https://gitlab.com/dann-merlin/spotipyne/-/raw/master/assets/mobile_playlists.png)
![Screenshot Mobile Tracks](https://gitlab.com/dann-merlin/spotipyne/-/raw/master/assets/mobile_tracks.png)

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

# How can I use it?

For installation see below.

You need to set your spotify username as an environment variable.

``export SPOTIPYNE_USERNAME="my_username"``

I have not implemented a way to set it inside the application yet.

# Build dependencies

- meson
- ninja

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
