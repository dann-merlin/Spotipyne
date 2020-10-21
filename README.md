# Spotipyne
Gtk Spotify client written in python made to be compatible with mobile formfactors like a pinephone.

Note: You need to have a spotify device running in order to play songs. This could for example be the official player or spotifyd.

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
