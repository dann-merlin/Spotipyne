# spotifyGuiBuilder.py
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

import os
import threading
import time

from functools import reduce

import gi
from gi.repository import Gtk, GdkPixbuf, GLib, GObject, Pango

from .coverArtLoader import CoverArtLoader, PixbufCache, Dimensions, get_desired_image_for_size
from .spotify import Spotify as sp

class TrackListRow(Gtk.ListBoxRow):

	def __init__(self, trackID, uri, albumUri, **kwargs):
		super().__init__(**kwargs)
		self.trackID = trackID
		self.uri = uri
		self.albumUri = albumUri

	def getUri(self):
		return self.uri

	def getAlbumUri(self):
		return self.albumUri

class PlaylistsListRow(Gtk.ListBoxRow):

	def __init__(self, playlistID, uri, **kwargs):
		super().__init__(**kwargs)
		self.playlistID = playlistID
		self.uri = uri

	def getUri(self):
		return self.uri

	def getPlaylistID(self):
		return self.playlistID

class SpotifyGuiBuilder:

	def __init__(self, coverArtLoader):
		self.coverArtLoader = coverArtLoader
		self.currentPlaylistID = ''

	def buildTrackEntry(self, trackResponse):
		track = trackResponse['track']
		albumUri = track['album']['uri']
		row = TrackListRow(track['id'], track['uri'], albumUri = albumUri)
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
		imageResponses = track['album']['images']

		desired_size = 60
		imageUrl = get_desired_image_for_size(desired_size, imageResponses)

		coverArt = self.coverArtLoader.getLoadingImage()
		hbox.pack_start(coverArt, False, True, 5)
		self.coverArtLoader.asyncUpdateCover(coverArt, url=imageUrl, uri=albumUri, dimensions=Dimensions(desired_size, desired_size, True))
		trackNameString = track['name']
		artistString = reduce(lambda a, b: {'name': a['name'] + ", " + b['name']},
					track['artists'][1:],
					track['artists'][0]
					)['name']
		trackLabelString = '<b>' + GLib.markup_escape_text(trackNameString) + '</b>' + '\n' + GLib.markup_escape_text(artistString)
		trackLabel = Gtk.Label(xalign=0)
		trackLabel.set_max_width_chars(32)
		trackLabel.set_line_wrap(True)
		trackLabel.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
		trackLabel.set_markup(trackLabelString)
		hbox.pack_end(trackLabel, True, True, 0)
		row.add(hbox)
		return row

	def asyncLoadPlaylistTracks(self, tracksList, playlistID, resumeEvent, stopEvent):
		if self.currentPlaylistID == playlistID:
			resumeEvent.set()
			return
		self.currentPlaylistID = playlistID

		sem = threading.Semaphore(0)

		def removeOldPlaylist():
			for child in tracksList.get_children():
				tracksList.remove(child)
				self.coverArtLoader.forget_image(child.getAlbumUri())
			sem.release()
		GLib.idle_add(removeOldPlaylist)

		# TODO use insert
		def addTrackEntries(tracks):
			for track in tracks:
				trackEntry = self.buildTrackEntry(track)
				tracksList.add(trackEntry)
			tracksList.show_all()

		def loadPlaylistTracks():
			allTracks = []
			offset = 0
			pageSize = 100
			keepGoing = True
			while keepGoing:
				tracksResponse = sp.get().playlist_tracks(
					playlist_id=playlistID,
					fields='items(track(uri,id,name,artists(name),album(id,uri,images))),next',
					limit=pageSize,
					offset=offset)
				keepGoing = tracksResponse['next'] != None
				offset += pageSize
				allTracks += tracksResponse['items']

			def addAllTrackEntries():
				def chunks(l, n):
					for i in range(0, len(l), n):
						yield l[i:i+n]
				sem.acquire()
				try:
					for hugeChunk in chunks(allTracks, 100):
						for trackChunk in chunks(hugeChunk, 10):
							if stopEvent.is_set():
								break
							GLib.idle_add(addTrackEntries, trackChunk)
						time.sleep(1)
				finally:
					resumeEvent.set()

			addAllTrackEntries()

		thread = threading.Thread(target=loadPlaylistTracks)
		thread.start()

	def asyncLoadPlaylists(self, playlistsList):
		# TODO use insert
		def addPlaylistEntry(playlist):
			row = PlaylistsListRow(playlist['id'], playlist['uri'])
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			imageResponses = playlist['images']

			desired_size = 60
			imageUrl = get_desired_image_for_size(desired_size, imageResponses)

			coverArt = self.coverArtLoader.getLoadingImage()
			hbox.pack_start(coverArt, False, True, 5)
			self.coverArtLoader.asyncUpdateCover(coverArt, url=imageUrl, uri=playlist['uri'], dimensions=Dimensions(desired_size, desired_size, True))
			nameLabel = Gtk.Label(playlist['name'], xalign=0)
			nameLabel.set_max_width_chars(32)
			nameLabel.set_line_wrap(True)
			nameLabel.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
			hbox.pack_end(nameLabel, True, True, 0)
			row.add(hbox)
			playlistsList.add(row)
			playlistsList.show_all()

		def loadPlaylists():
			allPlaylists = []
			offset = 0
			pageSize = 50
			keepGoing = True
			while keepGoing:
				playlistsResponse = sp.get().current_user_playlists(limit=pageSize, offset=offset)
				keepGoing = playlistsResponse['next'] != None
				offset += pageSize
				allPlaylists += playlistsResponse['items']

			def addAllPlaylistEntries():
				for playlist in allPlaylists:
					GLib.idle_add(addPlaylistEntry, playlist)

			addAllPlaylistEntries()

		thread = threading.Thread(target=loadPlaylists)
		thread.start()
