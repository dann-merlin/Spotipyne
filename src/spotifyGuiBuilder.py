import os

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

		self.coverArtLoader = CoverArtLoader()

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
			imageUrl = item['images'][0]['url']
			coverArt = self.coverArtLoader.loadPlaylistCover(url=imageUrl, playlistID=item['id'])
			if coverArt:
				hbox.pack_start(coverArt, False, True, 0)

			label = Gtk.Label(item['name'], xalign=0)
			hbox.pack_end(label, True, True, 0)
			row.add(hbox)
			PlaylistsList.add(row)
