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
- list tracks inside a playlist / liked tracks 
- start playing a track inside a playlist (liked tracks can't yet be played, because there is no great native way to do so)
- show playlist covers
- show album covers
- show progress bar
- search (playlists and tracks only really work yet)
- like/unlike the current track

# How can I use it?

For installation see below.

For the normal login, just input your username and press submit (no password required). This should start your browser, if you haven't authorized the application to access your Spotify account yet in which you will have to log into spotify. If it does not start a browser, try setting the environment variable `BROWSER` before starting spotipyne.
You could also try the browser-automation login, which uses selenium to automate the login process inside the browser (so it's a hands-free experience). However this didn't work on the pinephone for me. Also you have to install some sort of webdriver supported by selenium like the geckodriver for firefox.

**Note: IF YOU ARE USING THE BROWSER AUTOMATION, IT WILL AUTOMATICALLY AGREE TO AUTHORIZE THIS APP TO HAVE ACCESS TO YOUR LIBRARY AND PLAYBACK! PLEASE BE AWARE OF THAT.**

# Build dependencies

- meson
- ninja
- pip (optional - alternatively you might be able to install the python packages with your package manager)

# Dependencies

- gettext
- libhandy >= 1.0
- python3
- PyGObject >= 3.36
- pyxdg
- spotipy

# Optional Dependencies:

- selenium and a webdriver like geckodriver (for browser automation on login)

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

# Contact

If you wan't to contact me, you can do so at spotipyne@posteo.net
