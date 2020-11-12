# window.py
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

import threading

import gi
gi.require_version('Handy', '1')
from gi.repository import Gtk, Handy, GObject

from .coverArtLoader import CoverArtLoader
from .spotifyGuiBuilder import SpotifyGuiBuilder
from .spotify import Spotify as sp
from .spotifyPlayback import SpotifyPlayback
from .simpleControls import SimpleControls
from .searchOverview import SearchOverview

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/window.ui')
class SpotipyneWindow(Handy.ApplicationWindow):
	__gtype_name__ = 'SpotipyneWindow'

	Handy.init()
	HeaderbarSwitcher = Gtk.Template.Child()
	BottomSwitcher = Gtk.Template.Child()
	MainStack = Gtk.Template.Child()
	PlaylistsOverview = Gtk.Template.Child()
	Playlists = Gtk.Template.Child()
	PlaylistsList = Gtk.Template.Child()
	PlaylistTracks = Gtk.Template.Child()
	PlaylistTracksList = Gtk.Template.Child()
	BackButtonStack = Gtk.Template.Child()
	BackButtonPlaylists = Gtk.Template.Child()
	BackButtonSearch = Gtk.Template.Child()
	SimpleControlsParent = Gtk.Template.Child()
	Revealer = Gtk.Template.Child()
	RevealButton = Gtk.Template.Child()

	def onPlaylistsListRowActivated(self, PlaylistsList, PlaylistRow):
		self.TracksListStopEvent.set()
		self.TracksListResumeEvent.wait()
		self.TracksListResumeEvent.clear()
		self.TracksListStopEvent.clear()
		self.spGUI.asyncLoadPlaylistTracks(self.PlaylistTracksList, PlaylistRow.getUri().split(":")[-1], self.TracksListResumeEvent, self.TracksListStopEvent)
		self.PlaylistsOverview.set_visible_child(self.PlaylistTracks)

	def toggleReveal(self, button):
		self.Revealer.set_reveal_child( not self.Revealer.get_reveal_child())

	def playlist_tracks_focused(self):
		return self.PlaylistsOverview.get_visible_child() == self.PlaylistTracks

	def initCoverArtLoader(self):
		self.coverArtLoader = CoverArtLoader()

	def initPlaylistsOverview(self):

		def initLists():
			self.TracksListStopEvent = threading.Event()
			self.TracksListResumeEvent = threading.Event()
			self.TracksListResumeEvent.set()
			self.PlaylistsList.connect("row-activated", self.onPlaylistsListRowActivated)
			self.spGUI.asyncLoadPlaylists(self.PlaylistsList)

		initLists()

		def onFoldedChange(playlistsOverview, _):
			# For some reason the folded variable can not be trusted
			if playlistsOverview.get_folded():
				if playlistsOverview.get_visible_child() == self.Playlists:
					self.BackButtonPlaylists.hide()
				else:
					self.BackButtonPlaylists.show()
			else:
				self.BackButtonPlaylists.hide()

		def onChildSwitched(playlistsOverview, _):
			if playlistsOverview.get_visible_child() == self.Playlists:
				self.BackButtonPlaylists.hide()
			else:
				if playlistsOverview.get_folded():
					self.BackButtonPlaylists.show()
				else:
					self.BackButtonPlaylists.hide()

		def onClickedBackButton(backButton):
			self.PlaylistsOverview.set_visible_child(self.Playlists)

		self.PlaylistsOverview.connect("notify::folded", onFoldedChange)
		self.PlaylistsOverview.connect("notify::visible-child", onChildSwitched)
		self.BackButtonPlaylists.connect("clicked", onClickedBackButton)


	def initSpotifyPlayback(self):
		self.spotifyPlayback = SpotifyPlayback(self.coverArtLoader)

	def initSimpleControls(self):
		self.simpleControls = SimpleControls(self.spotifyPlayback)
		self.SimpleControlsParent.pack_start(self.simpleControls, False, True, 0)
		self.simpleControls.set_reveal_child(False)

	def initSearchOverview(self):
		self.searchOverview = SearchOverview(self.spGUI, self.BackButtonSearch)
		self.MainStack.add_titled(self.searchOverview, 'Search', 'Search')
		self.MainStack.child_set_property(self.searchOverview, "icon-name", "edit-find-symbolic")

	def initBackButtons(self):
		self.BackButtonStack.child_set_property
		self.MainStack.bind_property("visible-child-name", self.BackButtonStack, "visible-child-name")

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.initCoverArtLoader()

		self.spGUI = SpotifyGuiBuilder(self.coverArtLoader)

		self.initPlaylistsOverview()

		self.initSearchOverview()

		self.initSpotifyPlayback()

		self.initSimpleControls()

		self.initBackButtons()

		self.HeaderbarSwitcher.bind_property("title-visible", self.BottomSwitcher, "reveal", GObject.BindingFlags.SYNC_CREATE)

		self.RevealButton.connect("clicked", self.toggleReveal)
