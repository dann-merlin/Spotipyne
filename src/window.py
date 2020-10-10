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
from .backButton import BackButton
from .simpleControls import SimpleControls

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
	BackButtonBox = Gtk.Template.Child()
	backButtonPlaylistsOverview = BackButton()
	SimpleControlsParent = Gtk.Template.Child()
	Revealer = Gtk.Template.Child()
	RevealButton = Gtk.Template.Child()

	def onPlaylistOverviewBackButtonClicked(self, button):
		self.PlaylistsOverview.set_visible_child_name("0")

	def onPlaylistTracksListRowActivated(self, PlaylistTracksList, TrackRow):
		uri = self.PlaylistsList.get_selected_row().getUri()
		try:
			sp.get().start_playback(context_uri=uri, offset={ "uri": TrackRow.getUri() })
		except Exception as e:
			print(e)

	def onPlaylistsListRowActivated(self, PlaylistsList, PlaylistRow):
		self.TracksListStopEvent.set()
		self.TracksListResumeEvent.wait()
		self.TracksListResumeEvent.clear()
		self.TracksListStopEvent.clear()
		self.spGUI.asyncLoadPlaylistTracks(self.PlaylistTracksList, PlaylistRow.getPlaylistID(), self.TracksListResumeEvent, self.TracksListStopEvent)
		self.PlaylistsOverview.set_visible_child_name("1")

	def toggleReveal(self, button):
		self.Revealer.set_reveal_child( not self.Revealer.get_reveal_child())

	def playlist_tracks_focused(self):
		return self.PlaylistsOverview.get_visible_child() == self.PlaylistTracks

	def initCoverArtLoader(self):
		self.coverArtLoader = CoverArtLoader()

	def initPlaylistsOverview(self):
		def initBackButton():
			self.BackButtonBox.remove(self.BackButtonBox.get_children()[0])
			self.backButtonPlaylistsOverview.visible_child_add_activation_widget(self.PlaylistTracks)
			self.backButtonPlaylistsOverview.visible_child_add_deactivation_widget(self.Playlists)
			self.backButtonPlaylistsOverview.addRequirement(self.playlist_tracks_focused)
			self.BackButtonBox.add(self.backButtonPlaylistsOverview)
			self.PlaylistsOverview.bind_property("visible-child", self.backButtonPlaylistsOverview, "visible_child_fake", GObject.BindingFlags.SYNC_CREATE)
			self.PlaylistsOverview.bind_property("folded", self.backButtonPlaylistsOverview, "visible", GObject.BindingFlags.SYNC_CREATE)
			self.backButtonPlaylistsOverview.connect("clicked", self.onPlaylistOverviewBackButtonClicked)
			self.PlaylistTracksList.connect("row-activated", self.onPlaylistTracksListRowActivated)
			self.backButtonPlaylistsOverview.set_property("active", self.PlaylistsOverview.get_folded())

		def initLists():
			self.TracksListStopEvent = threading.Event()
			self.TracksListResumeEvent = threading.Event()
			self.TracksListResumeEvent.set()
			self.PlaylistsList.connect("row-activated", self.onPlaylistsListRowActivated)
			self.spGUI = SpotifyGuiBuilder(self.coverArtLoader)
			self.spGUI.asyncLoadPlaylists(self.PlaylistsList)

		initLists()
		initBackButton()

	def initSpotifyPlayback(self):
		self.spotifyPlayback = SpotifyPlayback(self.coverArtLoader)

	def initSimpleControls(self):
		self.simpleControls = SimpleControls(self.spotifyPlayback)
		self.SimpleControlsParent.pack_start(self.simpleControls, False, True, 0)
		self.simpleControls.set_reveal_child(False)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.initCoverArtLoader()

		self.initPlaylistsOverview()

		self.initSpotifyPlayback()

		self.initSimpleControls()

		self.HeaderbarSwitcher.bind_property("title-visible", self.BottomSwitcher, "reveal", GObject.BindingFlags.SYNC_CREATE)

		self.RevealButton.connect("clicked", self.toggleReveal)
