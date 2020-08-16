import os

from functools import reduce

from xdg import XDG_CACHE_HOME

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import gi
from gi.repository import Gtk, GdkPixbuf

from .config import Config
from .coverArtLoader import CoverArtLoader

scope = "playlist-read-private,playlist-read-collaborative"
username = 'der_echte_merlin'

os.environ["SPOTIPY_CLIENT_ID"] = "72d3a0443ae547db8e6471841f0ac6d7"
os.environ["SPOTIPY_CLIENT_SECRET"] = "ac0ed069a1f4470c9068690a19b5960e"

class TrackListRow(Gtk.ListBoxRow):

	def __init__(self, trackID, **kwargs):
		super().__init__(**kwargs)

class PlaylistsListRow(Gtk.ListBoxRow):

	def __init__(self, playlistID, **kwargs):
		super().__init__(**kwargs)
		self.playlistID = playlistID

	def getPlaylistID(self):
		return self.playlistID

class SpotifyGuiBuilder:

	def __init__(self, window):
		self.window = window
		sp_oauth = SpotifyOAuth(
			username = username,
			scope = scope,
			cache_path = XDG_CACHE_HOME / Config.applicationID / 'auth_token',
			redirect_uri = "http://127.0.0.1:8080"
			)

		self.sp = spotipy.Spotify(auth_manager=sp_oauth)

		self.coverArtLoader = CoverArtLoader()
		self.currentPlaylistID = ''

	def loadPlaylistTracksList(self, playlist):
		playlistID = playlist.getPlaylistID()
		if self.currentPlaylistID == playlistID:
			return
		self.currentPlaylistID = playlistID
		allTracks=[]
		offset = 0
		limit = 100
		total = offset + 2
		while offset + 1 < total:
			print('Downloading...')
			tracksResponse = self.sp.playlist_tracks(
				playlist_id=playlistID,
				fields='items(track(id,name,artists(name))),offset,total',
				offset=offset,
				limit=limit,
				)
			allTracks.append(tracksResponse['items'])
			total = tracksResponse['total']
			offset = tracksResponse['offset'] + limit
		tracksList = self.window.PlaylistTracksList
		removeMe = tracksList.get_children()
		for elem in removeMe:
			tracksList.remove(elem)

		if len(allTracks) == 0:
			row = Gtk.ListBoxRow()
			label = Gtk.Label(label="No playlists found.")
			row.add(label)
			tracksList.add(row)

		for item in allTracks[0]:
			track = item['track']
			row = TrackListRow(track['id'])
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			# imageUrl = item['images'][0]['url']
			# coverArt = self.coverArtLoader.loadPlaylistCover(url=imageUrl, playlistID=item['id'])
			# if coverArt:
			# 	hbox.pack_start(coverArt, False, True, 0)
			nameLabel = Gtk.Label(track['name'], xalign=0)
			hbox.pack_end(nameLabel, True, True, 0)
			artistsLabel = Gtk.Label(
					reduce(lambda a, b: {'name': a['name'] + ", " + b['name']},
						track['artists'][1:],
						track['artists'][0]
						)['name'],
					xalign=0)
			hbox.pack_end(artistsLabel, True, True, 0)
			row.add(hbox)
			tracksList.add(row)
		tracksList.show_all()

	def activatePlaylist(self, playlistsList, playlist):
		self.loadPlaylistTracksList(playlist)
		self.window.PlaylistsOverview.set_visible_child(self.window.PlaylistTracks)


	def setPlaylistEntries(self):
		PlaylistsList = self.window.PlaylistsList
		results = self.sp.current_user_playlists(limit=50)

		if len(results['items']) == 0:
			row = Gtk.ListBoxRow()
			label = Gtk.Label(label="No playlists found.")
			row.add(label)
			PlaylistsList.add(row)
			return

		for item in results['items']:
			row = PlaylistsListRow(item['id'])
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			imageUrl = item['images'][0]['url']
			coverArt = self.coverArtLoader.loadPlaylistCover(url=imageUrl, playlistID=item['id'])
			if coverArt:
				hbox.pack_start(coverArt, False, True, 0)

			label = Gtk.Label(item['name'], xalign=0)
			hbox.pack_end(label, True, True, 0)
			row.add(hbox)
			PlaylistsList.add(row)
