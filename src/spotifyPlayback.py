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

class SpotifyPlayback(GObject.Object):
	__gtype_name__ = "SpotifyPlayback"

	SLEEP_TIME = 1

	def __init__(self, coverArtLoader, **kwargs):
		super().__init__(**kwargs)
		self.__shuffle = False
		self.duration_ms = 1.0
		self.coverArtLoader = coverArtLoader
		self.has_playback = False

		playbackUpdateThread = threading.Thread(target=self.keepUpdating, daemon=True)
		playbackUpdateThread.start()

	def keepUpdating(self):
		self.track_uri = ""
		self.track_name = ""
		self.artists = ""
		self.coverUrl = ""
		is_playing = None
		while True:
			try:
				pb = sp.get().current_playback()

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
							{ 'name': a['name'] + ", " + b['name'] },
							pb['item']['artists'][1:],
							pb['item']['artists'][0]
							)['name']
					self.track_uri = pb['item']['uri']
					self.duration_ms = pb['item']['duration_ms']
					self.coverUrl = pb['item']['album']['images'][0]['url']
					self.emit("track_changed", self.track_uri)
				self.progress_fraction = self.progress_ms / self.duration_ms
			except Exception as e:
				print(e)
			time.sleep(self.SLEEP_TIME)

	# @GObject.Property(type=int, default=0)
	# def progress_ms(self):
	# 	return self.__progress_ms

	# @progress_ms.setter
	# def progress_ms(self, new_progress_ms):
	# 	try:
	# 		print("Seeking: " + str(new_progress_ms))
	# 		sp.get().seek_track(new_progress_ms)
	# 	except SpotifyException as e:
	# 		print(e)
	# 	self.__progress_ms = new_progress_ms

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
	def has_playback(self, has_playback):
		pass

	def set_current_cover_art(self, image):
		self.coverArtLoader.asyncUpdateCover(image, self.track_uri, self.coverUrl)

	def get_track_name(self):
		return self.track_name

	def get_artist_names(self):
		return self.artists
