import os

import requests

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import gi
from gi.repository import Gtk, GdkPixbuf

from .coverArtLoader import CoverArtLoader

scope = "playlist-read-private,playlist-read-collaborative"
username = 'der_echte_merlin'

os.environ["SPOTIPY_CLIENT_ID"] = "72d3a0443ae547db8e6471841f0ac6d7"
os.environ["SPOTIPY_CLIENT_SECRET"] = "ac0ed069a1f4470c9068690a19b5960e"

class SpotifyGuiBuilder:

	def __init__(self):
		sp_oauth = SpotifyOAuth(
			username=username,
			scope=scope,
			redirect_uri="http://127.0.0.1:8080"
			)

		self.sp = spotipy.Spotify(auth_manager=sp_oauth)

	def setPlaylistEntries(self, PlaylistsList):
		results = self.sp.current_user_playlists(limit=50)
		if len(results['items']) == 0:
			row = Gtk.ListBoxRow()
			label = Gtk.Label(label="No playlists found.")
			row.add(label)
			PlaylistsList.add(row)
			return
		print("Results: ")
		print(results)
		for item in results['items']:
			row = Gtk.ListBoxRow()
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			imageUrl = None
			coverArt = CoverArtLoader.load_playlist_cover(item['id'])
			if coverArt:
				hbox.pack_start(coverArt, True, True, 0)

			label = Gtk.Label(item['name'], xalign=0)
			hbox.pack_end(label, True, True, 0)
			row.add(box)
			PlaylistsList.add(row)
