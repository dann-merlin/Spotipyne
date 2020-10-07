# spotify.py
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

from .config import Config
import os
import sys
import threading
from xdg import XDG_CACHE_HOME

import spotipy
from spotipy.oauth2 import SpotifyOAuth

class Spotify:

	__sp = None
	__lock = threading.Lock()

	def __init__(self):
		if self.__sp:
			print("There is an error in the code. The constructor of the spotify object should not be called more than once!.", file=sys.stderr)
			sys.exit(1)
		username = os.getenv("SPOTIPYNE_USERNAME", "der_echte_merlin") #TODO read in via dialog and save
		clientID = os.getenv("SPOTIPY_CLIENT_ID",  "72d3a0443ae547db8e6471841f0ac6d7")
		clientSecret = os.getenv("SPOTIPY_CLIENT_SECRET", "ac0ed069a1f4470c9068690a19b5960e")

		cache_path_dir = XDG_CACHE_HOME / Config.applicationID
		cache_path_dir.mkdir(parents=True, exist_ok=True)

		scope = "playlist-read-private,playlist-read-collaborative"

		sp_oauth = SpotifyOAuth(
				username = username,
				client_id = clientID,
				client_secret = clientSecret,
			scope = scope,
			cache_path =  cache_path_dir / 'auth_token',
			redirect_uri = "http://127.0.0.1:8080"
			)

		self.sp = spotipy.Spotify(auth_manager=sp_oauth)

	@classmethod
	def get(cls):
		with cls.__lock:
			if not cls.__sp:
				cls.__sp = Spotify()
			return cls.__sp.sp
