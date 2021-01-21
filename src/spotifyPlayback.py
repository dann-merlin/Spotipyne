# spotifyPlayback.py
#
# Copyright 2020 Merlin Danner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
import threading

from functools import reduce

from gi.repository import GObject

from .spotify import Spotify as sp

from .coverArtLoader import CoverArtLoader, Dimensions, get_desired_image_for_size


class SpotifyPlayback(GObject.Object):
    __gtype_name__ = "SpotifyPlayback"

    SLEEP_TIME = 2

    def __init__(self, coverArtLoader, **kwargs):
        super().__init__(**kwargs)
        self.__shuffle = False
        self.duration_ms = 1.0
        self.desired_size = 60
        self.coverArtLoader = coverArtLoader
        self.has_playback = False
        self.devices = []
        self.devices_ids = []
        self.lock = threading.Lock()
        self.track_uri = ""
        self.track_name = ""
        self.artists = ""
        self.coverUrl = ""
        self.is_saved_track = False

        playbackUpdateThread = threading.Thread(
            target=self.keepUpdating, daemon=True)
        playbackUpdateThread.start()

    def keepUpdating(self):
        is_playing = None
        while True:
            try:
                pb = sp.get().current_playback()
                devices = sp.get().devices()['devices']
                new_devices_ids = [dev['id'] for dev in devices]
                self.devices = devices
                if new_devices_ids != self.devices_ids:
                    self.devices_ids = new_devices_ids
                    self.emit("devices_changed")

                if not pb:
                    if self.has_playback:
                        self.emit("has_playback", not self.has_playback)
                    time.sleep(5)
                    self.has_playback = False
                    continue
                else:
                    if not self.has_playback:
                        self.emit("has_playback", not self.has_playback)
                    self.has_playback = True

                if is_playing != pb['is_playing']:
                    is_playing = pb['is_playing']
                    self.emit("is_playing_changed", is_playing)

                self.repeat = pb['repeat_state']

                self.shuffle = pb['shuffle_state']

                self.progress_ms = pb['progress_ms']

                if self.track_uri != pb['item']['uri']:
                    self.track_name = pb['item']['name']
                    self.artists = reduce(
                                    lambda a, b:
                                    {'name': a['name'] + ", " + b['name']},
                                    pb['item']['artists'][1:],
                                    pb['item']['artists'][0]
                                    )['name']
                    self.track_uri = pb['item']['uri']
                    self.duration_ms = pb['item']['duration_ms']
                    self.coverUrl = pb['item']['album']['images']
                    self.emit("track_changed", self.track_uri)
                    if sp.get().current_user_saved_tracks_contains(
                            [self.track_uri])[0]:
                        self.emit(
                            "is_saved_track_changed",
                            self.is_saved_track)
                self.progress_fraction = self.progress_ms / self.duration_ms
            except Exception as e:
                print(e)
            time.sleep(self.SLEEP_TIME)

    @GObject.Property(type=float, default=0.0)
    def progress_fraction(self):
        return self.__progress_fraction

    @progress_fraction.setter
    def progress_fraction(self, new_progress_fraction):
        self.__progress_fraction = new_progress_fraction

    @GObject.Signal(arg_types=(bool,))
    def is_playing_changed(self, is_playing):
        pass

    @GObject.Signal(arg_types=(str,))
    def track_changed(self, track_uri):
        pass

    @GObject.Signal(arg_types=(bool,))
    def is_saved_track_changed(self, is_saved_track):
        self.is_saved_track = is_saved_track

    @GObject.Signal(arg_types=(bool,))
    def has_playback(self, has_playback):
        pass

    @GObject.Signal
    def devices_changed(self):
        pass

    def set_current_cover_art(self, image, dim=None):
        if dim is None:
            dim = Dimensions(self.desired_size, self.desired_size, True)
        self.coverArtLoader.asyncUpdateCover(
            image, self.track_uri, self.coverUrl, dim)

    def get_track_name(self):
        return self.track_name

    def get_artist_names(self):
        return self.artists

    def get_devices(self):
        return self.devices
