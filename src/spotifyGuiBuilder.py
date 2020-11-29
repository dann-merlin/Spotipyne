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

# TODO maybe just remove the non genericRows
class GenericSpotifyRow(Gtk.ListBoxRow):

	def __init__(self, uri, **kwargs):
		super().__init__(**kwargs)
		self.uri = uri

	def getUri(self):
		return self.uri

class AlbumRow(GenericSpotifyRow):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

class TrackRow(GenericSpotifyRow):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

class ArtistRow(GenericSpotifyRow):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

class EpisodeRow(GenericSpotifyRow):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

class ShowRow(GenericSpotifyRow):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

class PlaylistRow(GenericSpotifyRow):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

class SpotifyGuiBuilder:

	def __init__(self, coverArtLoader):
		self.coverArtLoader = coverArtLoader
		self.currentPlaylistID = ''

	def getPlaylistTracks(self, playlist_id):
		allTracks = []
		offset = 0
		pageSize = 100
		keepGoing = True
		while keepGoing:
			tracksResponse = sp.get().playlist_tracks(
				playlist_id=playlist_id,
				fields='items(track(uri,id,name,artists(name),album(id,uri,images))),next',
				limit=pageSize,
				offset=offset)
			keepGoing = tracksResponse['next'] != None
			offset += pageSize
			allTracks += tracksResponse['items']
		return [trackResponse['track'] for trackResponse in allTracks]

	def loadGenericList(self, generic_list, raw_data, buildEntryFunction):
		def loadChunk(chunk):
			for raw_data_for_entry in chunk:
				entry = buildEntryFunction(raw_data_for_entry)
				generic_list.insert(entry, -1)
			generic_list.show_all()

		def chunks(l, n):
			for i in range(0, len(l), n):
				yield l[i:i+n]

		def setListboxAttributes(listbox):
			listbox.set_selection_mode(Gtk.SelectionMode.NONE)
		GLib.idle_add(setListboxAttributes, generic_list)

		for chunk in chunks(raw_data, 10):
			GLib.idle_add(loadChunk, chunk, priority=GLib.PRIORITY_LOW)
			time.sleep(1)

	def loadPlaylistTracksList(self, playlist_tracks_list, playlist_id):
		playlist_tracks = self.getPlaylistTracks(playlist_id)
		self.loadGenericList(playlist_tracks_list, playlist_tracks, self.buildTrackEntry)

	def buildArtistPage(self, artist_uri):
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.pack_start(Gtk.Label("Artist " + artist_uri), False, True, 0)
		vbox.show_all()
		return vbox

	def buildAlbumPage(self, album_uri):
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.pack_start(Gtk.Label("Album " + album_uri), False, True, 0)
		vbox.show_all()
		return vbox

	def buildPlaylistPage(self, playlist_uri):
		playlist_id=playlist_uri.split(':')[-1]
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		playlist_image = self.coverArtLoader.getLoadingImage()
		label = Gtk.Label(xalign=0)
		playlist_tracks_list = Gtk.ListBox()
		vbox.pack_start(playlist_image, False, True, 0)
		vbox.pack_start(label, False, True, 0)
		vbox.pack_start(playlist_tracks_list, False, True, 0)
		def onPlaylistTracksListRowActivated(listbox, row):
			def helper():
				sp.start_playback(context_uri=playlist_uri, offset={"uri": row.getUri()})
			sp_thread = threading.Thread(daemon=True, target=helper)
			sp_thread.start()

		playlist_tracks_list.connect('row-activated', onPlaylistTracksListRowActivated)

		def loadPlaylistPage():
			def loadLabelAndImage():
				playlist_info_response = sp.get().playlist(
					playlist_id,
					fields='name,images,followers(total),owner(display_name)'
				)
				playlist_cover_size_big = 128
				images = playlist_info_response['images']
				self.coverArtLoader.asyncUpdateCover(playlist_image, playlist_uri, images, dimensions=Dimensions(playlist_cover_size_big, playlist_cover_size_big, True))

				def buildPlaylistLabel():
					markup_string = '<b>' + GLib.markup_escape_text(playlist_info_response['name']) + '</b>'
					markup_string += '\n'
					markup_string += 'by ' + GLib.markup_escape_text(playlist_info_response['owner']['display_name'])
					followers_total = playlist_info_response['followers']['total']
					if followers_total > 1:
						markup_string += ' - ' + str(followers_total) + ' followers'
					label.set_markup(markup_string)
					label.show_all()

				GLib.idle_add(buildPlaylistLabel, priority=GLib.PRIORITY_LOW)

			thread_label = threading.Thread(daemon=True, target=loadLabelAndImage)
			thread_label.start()
			thread_tracks = threading.Thread(daemon=True, target=self.loadPlaylistTracksList, args=(playlist_tracks_list, playlist_id))
			thread_tracks.start()
		loadPlaylistPage()
		vbox.show_all()
		return vbox

	def buildShowPage(self, show_uri):
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		vbox.pack_start(Gtk.Label("Show " + show_uri), False, True, 0)
		vbox.show_all()
		return vbox

	def __buildGenericEntry(self, entry, imageResponses, uri, labelText, desiredCoverSize = 60):
		hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

		coverArt = self.coverArtLoader.getLoadingImage()
		hbox.pack_start(coverArt, False, True, 5)
		self.coverArtLoader.asyncUpdateCover(coverArt, urls=imageResponses, uri=uri, dimensions=Dimensions(desiredCoverSize, desiredCoverSize, True))
		label = Gtk.Label(xalign=0)
		label.set_max_width_chars(32)
		label.set_line_wrap(True)
		label.set_lines(2)
		label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);
		label.set_markup(labelText)
		hbox.pack_end(label, True, True, 0)
		entry.add(hbox)
		return entry

	def buildTrackEntry(self, track):
		albumUri = track['album']['uri']
		row = TrackRow(uri=track['uri'])
		imageResponses = track['album']['images']

		trackNameString = track['name']
		artistString = reduce(lambda a, b: {'name': a['name'] + ", " + b['name']},
					track['artists'][1:],
					track['artists'][0]
					)['name']
		trackLabelString = '<b>' + GLib.markup_escape_text(trackNameString) + '</b>' + '\n' + GLib.markup_escape_text(artistString)
		return self.__buildGenericEntry(row, imageResponses, albumUri, trackLabelString)

	def buildArtistEntry(self, artistResponse):
		artistUri = artistResponse['uri']
		row = ArtistRow(uri=artistUri)
		imageResponses = artistResponse['images']
		labelMarkup = '<b>' + GLib.markup_escape_text(artistResponse['name']) + '</b>' + '\n' + GLib.markup_escape_text(str(artistResponse['followers']['total']) + ' followers')
		return self.__buildGenericEntry(row, imageResponses, artistUri, labelMarkup)

	def buildEpisodeEntry(self, episodeResponse):
		if episodeResponse is None:
			return self.__buildGenericEntry(EpisodeRow(uri='episode::Response is None'), None, "No Uri. Episode is None", "No Uri. Episode is None")
		episodeUri = episodeResponse['uri']
		row = EpisodeRow(uri=episodeUri)
		imageResponses = episodeResponse['images']
		labelMarkup = '<b>' + GLib.markup_escape_text(episodeResponse['name']) + '</b>' + '\n' + GLib.markup_escape_text(episodeResponse['description'])
		return self.__buildGenericEntry(row, imageResponses, episodeUri, labelMarkup)

	def buildShowEntry(self, showResponse):
		showUri = showResponse['uri']
		row = ShowRow(uri=showUri)
		imageResponses = showResponse['images']
		labelMarkup = '<b>' + GLib.markup_escape_text(showResponse['name']) + '</b>' + '\n' + GLib.markup_escape_text(showResponse['publisher'])
		return self.__buildGenericEntry(row, imageResponses, showUri, labelMarkup)

	def buildAlbumEntry(self, albumResponse):
		albumUri = albumResponse['uri']
		row = AlbumRow(uri=albumUri)
		imageResponses = albumResponse['images']
		artistString = reduce(lambda a, b: {'name': a['name'] + ", " + b['name']},
					albumResponse['artists'][1:],
					albumResponse['artists'][0]
					)['name']
		labelMarkup = '<b>' + GLib.markup_escape_text(albumResponse['name']) + '</b>' + '\n' + GLib.markup_escape_text(artistString)
		return self.__buildGenericEntry(row, imageResponses, albumUri, labelMarkup)

	def buildPlaylistEntry(self, playlistResponse):
		playlistUri = playlistResponse['uri']
		row = PlaylistRow(uri=playlistUri)
		imageResponses = playlistResponse['images']
		return self.__buildGenericEntry(row, imageResponses, playlistUri, GLib.markup_escape_text(playlistResponse['name']))

	def buildSearchResults(self, searchResultBox, searchResponse, setSearchOverlayFunction):
		def _searchResultHelper(searchType, name, buildEntryFunction, activationHandler):
			response = searchResponse[searchType]
			resultBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
			resultTitle = Gtk.Label(xalign=0)
			resultTitle.set_markup('<b>' + name + '</b>')
			resultBox.pack_start(resultTitle, False, True, 0)
			if len(response['items']) != 0:
				resultsList = Gtk.ListBox()
				resultsList.connect("row-activated", activationHandler)
				list_loader_thread = threading.Thread(daemon=True, target=self.loadGenericList, args=(resultsList, response['items'], buildEntryFunction))
				list_loader_thread.start()
				resultBox.pack_start(resultsList, False, True, 0)
				searchResultBox.pack_start(resultBox, False, True, 0)
			else:
				notFoundLabel = Gtk.Label(xalign=0)
				notFoundLabel.set_markup('Could not find any ' + searchType + ' matching your search query...')
				resultBox.pack_start(notFoundLabel, False, True, 0)
				searchResultBox.pack_end(resultBox, False, True, 0)

		searchQueries = [
			{
				'type': 'tracks',
				'name': 'Tracks',
				'buildEntryFunction': self.buildTrackEntry,
				'activationHandler': lambda _, entry: sp.start_playback(uris=[entry.getUri()])
			},
			{
				'type': 'artists',
				'name': 'Artists',
				'buildEntryFunction': self.buildArtistEntry,
				'activationHandler': lambda _, entry: setSearchOverlayFunction(self.buildArtistPage(entry.getUri()))
			},
			{
				'type': 'albums',
				'name': 'Albums',
				'buildEntryFunction': self.buildAlbumEntry,
				'activationHandler': lambda _, entry: setSearchOverlayFunction(self.buildAlbumPage(entry.getUri()))
			},
			{
				'type': 'playlists',
				'name': 'Playlists',
				'buildEntryFunction': self.buildPlaylistEntry,
				'activationHandler': lambda _, entry: setSearchOverlayFunction(self.buildPlaylistPage(entry.getUri()))
			},
			{
				'type': 'shows',
				'name': 'Shows',
				'buildEntryFunction': self.buildShowEntry,
				'activationHandler': lambda _, entry: setSearchOverlayFunction(self.buildShowPage(entry.getUri()))
			},
			{
				'type': 'episodes',
				'name': 'Episodes',
				'buildEntryFunction': self.buildEpisodeEntry,
				'activationHandler': lambda _, entry: sp.start_playback(uris=[entry.getUri()])
			}
		]
		for searchQuery in searchQueries:
			_searchResultHelper(searchQuery['type'], searchQuery['name'], searchQuery['buildEntryFunction'], searchQuery['activationHandler'])
		searchResultBox.show_all()

	def buildLibrary(self):
		return Gtk.Box()

	def asyncLoadPlaylists(self, playlistsList):
		# TODO use insert
		def addPlaylistEntry(playlist):
			playlistUri = playlist['uri']
			row = PlaylistRow(uri=playlistUri)
			hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
			imageResponses = playlist['images']

			desired_size = 60

			coverArt = self.coverArtLoader.getLoadingImage()
			hbox.pack_start(coverArt, False, True, 5)
			self.coverArtLoader.asyncUpdateCover(coverArt, urls=imageResponses, uri=playlistUri, dimensions=Dimensions(desired_size, desired_size, True))
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
					GLib.idle_add(addPlaylistEntry, playlist, priority=GLib.PRIORITY_LOW)

			addAllPlaylistEntries()

		thread = threading.Thread(target=loadPlaylists)
		thread.start()
