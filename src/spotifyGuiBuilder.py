import os

from functools import reduce

from xdg import XDG_CACHE_HOME

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import gi
from gi.repository import Gtk, GdkPixbuf, GLib, GObject

from .config import Config
from .coverArtLoader import CoverArtLoader

scope = "playlist-read-private,playlist-read-collaborative"

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
		username = os.getenv("SPOTIPYNE_USERNAME", "der_echte_merlin") #TODO read in via dialog and save
		clientID = os.getenv("SPOTIPY_CLIENT_ID",  "72d3a0443ae547db8e6471841f0ac6d7")
		clientSecret = os.getenv("SPOTIPY_CLIENT_SECRET", "ac0ed069a1f4470c9068690a19b5960e")

		cache_path_dir = XDG_CACHE_HOME / Config.applicationID
		cache_path_dir.mkdir(parents=True, exist_ok=True)
		sp_oauth = SpotifyOAuth(
				username = username,
				client_id = clientID,
				client_secret = clientSecret,
			scope = scope,
			cache_path =  cache_path_dir / 'auth_token',
			redirect_uri = "http://127.0.0.1:8080"
			)

		self.sp = spotipy.Spotify(auth_manager=sp_oauth)

		self.coverArtLoader = CoverArtLoader()
		self.currentPlaylistID = ''

	def buildTrackEntry(self, trackResponse):
		track = trackResponse['track']
		row = TrackListRow(track['id'])
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		imageUrl = track['album']['images'][0]['url']
		coverArt = self.coverArtLoader.loadAlbumCover(url=imageUrl, ID=track['id'])
		if coverArt:
			hbox.pack_start(coverArt, False, True, 0)

		trackNameString = track['name']
		artistString = reduce(lambda a, b: {'name': a['name'] + ", " + b['name']},
					track['artists'][1:],
					track['artists'][0]
					)['name']
		trackLabelString = '<b>' + GLib.markup_escape_text(trackNameString) + '</b>' + '\n' + GLib.markup_escape_text(artistString)
		trackLabel = Gtk.Label(xalign=0)
		trackLabel.set_markup(trackLabelString)
		hbox.pack_end(trackLabel, True, True, 0)
		row.add(hbox)
		return row

	def loadPlaylistTracksList(self, playlist):
		tracksList = self.window.PlaylistTracksList
		if playlist == None:
			removeMe = tracksList.get_children()
			for elem in removeMe:
				tracksList.remove(elem)

			row = Gtk.ListBoxRow()
			label = Gtk.Label(label="Select a playlist")
			row.add(label)
			tracksList.add(row)
		else:
			playlistID = playlist.getPlaylistID()
			if self.currentPlaylistID == playlistID:
				return
			self.currentPlaylistID = playlistID
			allTracks=[]
			offset = 0
			limit = 100
			total = offset + 2
			while offset + 1 < total:
				tracksResponse = self.sp.playlist_tracks(
					playlist_id=playlistID,
					fields='items(track(id,name,artists(name),album(images))),offset,total',
					offset=offset,
					limit=limit,
					)
				allTracks.append(tracksResponse['items'])
				total = tracksResponse['total']
				offset = tracksResponse['offset'] + limit

			removeMe = tracksList.get_children()
			for elem in removeMe:
				tracksList.remove(elem)

			if len(allTracks) == 0:
				row = Gtk.ListBoxRow()
				label = Gtk.Label(label="No playlists found.")
				row.add(label)
				tracksList.add(row)

			for item in allTracks[0]:
				print("item:")
				print(item)
				trackEntry = self.buildTrackEntry(item)
				tracksList.add(trackEntry)

		tracksList.show_all()

	def activatePlaylist(self, playlistsList, playlist):
		def activatePlaylistHidden(self):
			self.loadPlaylistTracksList(playlist)
			self.window.PlaylistsOverview.set_visible_child(self.window.PlaylistTracks)
		Thread(target=activatePlaylistHidden


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
			coverArt = self.coverArtLoader.loadPlaylistCover(url=imageUrl, ID=item['id'])
			if coverArt:
				hbox.pack_start(coverArt, False, True, 0)

			label = Gtk.Label(item['name'], xalign=0)
			hbox.pack_end(label, True, True, 0)
			row.add(hbox)
			PlaylistsList.add(row)
