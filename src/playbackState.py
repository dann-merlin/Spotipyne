# playbackState.py
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

import threading
import spotipy
from .spotify import Spotify as sp
from gi.repository import GObject
from enum import IntEnum

class playback_status_enum(IntEnum):
	PLAYING = 1
	NOT_PLAYING = 2
	UNINITIALIZED = 3

	def to_string(self):
		if self is PLAYING:
			return "PLAYING"
		elif self is NOT_PLAYING:
			return "NOT_PLAYING"
		else:
			return "UNINITIALIZED"

class PlaybackState(GObject.Object):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.playback_status_value = playback_status_enum.UNINITIALIZED
		self.active_device_str = None

	@GObject.Property(type=bool, default=False)
	def is_shuffle(self):
		return self.shuffle_val

	@GObject.Property(type=

	@GObject.Property(type=str, default=None)
	def active_device(self):
		return self.active_device_str

	@GObject.Property(type=playback_status_enum, default=playback_status_enum.UNINITIALIZED)
	def playback_status(self):
		return self.playback_status_value

	def start(self):
		def stateUpdateLoop():
			while True:
				try:
					sp.get().current_playback()
				except spotipy.SpotifyException as e:
					print(e)
				# TODO update loop ( update itself has to be in GLib.idle_add )
		thread = threading.Thread(target=stateUpdateLoop, daemon=True)
		thread.start()
