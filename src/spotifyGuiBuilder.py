import os
import threading

from functools import reduce

from xdg import XDG_CACHE_HOME

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import gi
from gi.repository import Gtk, GdkPixbuf, GLib, GObject, Pango

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

		self.asyncLoadPlaylists()

	def buildTrackEntry(self, trackResponse):
		track = trackResponse['track']
		row = TrackListRow(track['id'])
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		try:
			imageUrl = track['album']['images'][0]['url']
			coverArt = self.coverArtLoader.getLoadingImage()
			hbox.pack_start(coverArt, False, True, 5)
			self.coverArtLoader.asyncUpdateAlbumCover(hbox, coverArt, url=imageUrl, ID=track['album']['id'])
		except IndexError:
			coverArt = self.coverArtLoader.getErrorImage()
			hbox.pack_start(coverArt, False, True, 5)
			print("Failed retrieveing the imageUrl for the track: " + str(track))
		trackNameString = track['name']
		artistString = reduce(lambda a, b: {'name': a['name'] + ", " + b['name']},
					track['artists'][1:],
					track['artists'][0]
					)['name']
		trackLabelString = '<b>' + GLib.markup_escape_text(trackNameString) + '</b>' + '\n' + GLib.markup_escape_text(artistString)
		trackLabel = Gtk.Label(xalign=0)
		trackLabel.set_max_width_chars(64)
		trackLabel.set_line_wrap(True)
		trackLabel.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
		trackLabel.set_markup(trackLabelString)
		hbox.pack_end(trackLabel, True, True, 0)
		row.add(hbox)
		return row

	def clearList(self, listToClear):
		for child in listToClear.get_children():
			listToClear.remove(child)


	def asyncLoadPlaylistTracks(self, tracksList, playlistID):
		if self.currentPlaylistID == playlistID:
			self.window.TracksListResumeEvent.set()
			return
		self.currentPlaylistID = playlistID

		self.clearList(tracksList)

		def addTrackEntry(track):
			trackEntry = self.buildTrackEntry(track)
			tracksList.add(trackEntry)

		def loadPlaylistTracks():
			allTracks = []
			offset = 0
			pageSize = 100
			keepGoing = True
			while keepGoing:
				tracksResponse = self.sp.playlist_tracks(
					playlist_id=playlistID,
					fields='items(track(id,name,artists(name),album(id,images))),next',
					limit=pageSize,
					offset=offset)
				keepGoing = tracksResponse['next'] != None
				offset += pageSize
				allTracks += tracksResponse['items']

			def addAllTrackEntries():
				try:
					counter = 0
					for track in allTracks:
						if self.window.TracksListStopEvent.is_set():
							break
						GLib.idle_add(addTrackEntry, track)
						counter += 1
						if counter == 10:
							GLib.idle_add(tracksList.show_all)
						counter %= 10
						GLib.idle_add(tracksList.show_all)
				finally:
					self.window.TracksListResumeEvent.set()

			addAllTrackEntries()

		thread = threading.Thread(target=loadPlaylistTracks)
		thread.start()

	def asyncLoadPlaylists(self):
		def addPlaylistEntry(playlist):
			row = PlaylistsListRow(playlist['id'])
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			imageUrl = playlist['images'][0]['url']
			coverArt = self.coverArtLoader.getLoadingImage()
			hbox.pack_start(coverArt, False, True, 5)
			self.coverArtLoader.asyncUpdatePlaylistCover(hbox, coverArt, url=imageUrl, ID=playlist['id'])
			nameLabel = Gtk.Label(playlist['name'], xalign=0)
			nameLabel.set_max_width_chars(32)
			nameLabel.set_line_wrap(True)
			nameLabel.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
			hbox.pack_end(nameLabel, True, True, 0)
			row.add(hbox)
			self.window.PlaylistsList.add(row)
			self.window.PlaylistsList.show_all()

		def loadPlaylists():
			allPlaylists = []
			offset = 0
			pageSize = 50
			keepGoing = True
			while keepGoing:
				playlistsResponse = self.sp.current_user_playlists(limit=pageSize, offset=offset)
				keepGoing = playlistsResponse['next'] != None
				offset += pageSize
				allPlaylists += playlistsResponse['items']

			def addAllPlaylistEntries():
				for playlist in allPlaylists:
					addPlaylistEntry(playlist)

			GLib.idle_add(addAllPlaylistEntries)

		thread = threading.Thread(target=loadPlaylists)
		thread.start()



	# def setPlaylistEntries(self):
	# 	PlaylistsList = self.window.PlaylistsList
	# 	results = self.sp.current_user_playlists(limit=50)

	# 	if len(results['items']) == 0:
	# 		row = Gtk.ListBoxRow()
	# 		label = Gtk.Label(label="No playlists found.")
	# 		row.add(label)
	# 		PlaylistsList.add(row)
	# 		return

	# 	for item in results['items']:
	# 		row = PlaylistsListRow(item['id'])
	# 		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
	# 		imageUrl = item['images'][0]['url']
	# 		coverArt = self.coverArtLoader.loadPlaylistCover(url=imageUrl, ID=item['id'])
	# 		if coverArt:
	# 			hbox.pack_start(coverArt, False, True, 0)

	# 		label = Gtk.Label(item['name'], xalign=0)
	# 		hbox.pack_end(label, True, True, 0)
	# 		row.add(hbox)
	# 		PlaylistsList.add(row)
