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
from xdg import BaseDirectory

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Spotify:

    __sp = None
    __lock = threading.Lock()
    username_backup = None

    @classmethod
    def set_username_backup(cls, username):
        cls.username_backup = username

    @classmethod
    def get_username_cache_path(cls):
        return BaseDirectory.save_cache_path(
            Config.applicationID) + '/' + 'username'

    @classmethod
    def save_username_to_cache(cls, username):
        cache_path = cls.get_username_cache_path()
        with open(cache_path, "w") as cache_file:
            cache_file.write(username)

    @classmethod
    def get_username_from_cache(cls):
        cache_path = cls.get_username_cache_path()
        try:
            with open(cache_path, "r") as cache_file:
                return cache_file.readline()
        except FileNotFoundError:
            return None

    @classmethod
    def get_cached_token_path(cls):
        cache_path = BaseDirectory.save_cache_path(Config.applicationID)
        cache_path += '/' + 'auth_token'
        return cache_path

    @classmethod
    def delete_cached_token(cls):
        try:
            os.remove(cls.get_cached_token_path())
        except FileNotFoundError:
            pass

    @classmethod
    def build_auth_manager(cls):

        clientID = os.getenv(
            "SPOTIPY_CLIENT_ID",
            "72d3a0443ae547db8e6471841f0ac6d7")
        # This is obviously a "secret", but honestly nobody wants to go make a
        # spotify developer account
        clientSecret = os.getenv(
            "SPOTIPY_CLIENT_SECRET",
            "ac0ed069a1f4470c9068690a19b5960e")

        cache_path = cls.get_cached_token_path()

        scope = "user-read-playback-position,user-read-private,user-library-modify,user-library-read,user-top-read,playlist-modify-public,playlist-modify-private,user-read-playback-state,user-read-currently-playing,user-read-recently-played,user-modify-playback-state,playlist-read-private,playlist-read-collaborative"

        user = cls.get_username_from_cache()
        if user is None and cls.username_backup is None:
            raise Exception("Username was not set yet!")

        sp_oauth = SpotifyOAuth(
                        username=cls.username_backup if user is None else user,
                        client_id=clientID,
                        client_secret=clientSecret,
                        scope=scope,
                        cache_path=cache_path,
                        redirect_uri="http://127.0.0.1:8080"
                )
        return sp_oauth

    def __init__(self, auth_manager):
        if self.__sp:
            print(
                "There is an error in the code. The constructor of the spotify object should not be called more than once!",
                file=sys.stderr)
            sys.exit(1)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    @classmethod
    def get(cls):
        with cls.__lock:
            if not cls.__sp:
                cls.__sp = Spotify(cls.build_auth_manager())
            return cls.__sp.sp

    @classmethod
    def start_playback(
            cls, context_uri=None, offset=None, device_id=None, uris=None,
            recursion_protection=False):
        try:
            cls.get().start_playback(
                context_uri=context_uri,
                offset=offset,
                uris=uris,
                device_id=device_id)
        except spotipy.SpotifyException as e:
            if "No active device found" in str(e):
                if recursion_protection:
                    return
                try:
                    cls.start_playback(
                            context_uri=context_uri,
                            uris=uris,
                            offset=offset,
                            device_id=cls.get().devices()['devices'][0]['id'],
                            recursion_protection=True
                            )
                except spotipy.SpotifyException as dev_e:
                    print(str(dev_e))
                except IndexError:
                    print("Cannot start playback. No active devices...")
            else:
                print(str(e))

    @classmethod
    def pause_playback(cls):
        try:
            cls.get().pause_playback()
        except spotipy.SpotifyException as e:
            print(str(e))
