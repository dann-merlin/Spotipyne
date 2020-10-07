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
from gi.repository import Gtk, Handy

from .spotifyGuiBuilder import SpotifyGuiBuilder
from .backButton import BackButton

def static_vars(**kwargs):
	def decorate(func):
		for k in kwargs:
			setattr(func, k, kwargs[k])
		return func
	return decorate

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
	Revealer = Gtk.Template.Child()
	RevealButton = Gtk.Template.Child()

	def onPlaylistOverviewBackButtonClicked(self, button):
		self.PlaylistsOverview.set_visible_child_name("0")

	def onPlaylistTracksListRowActivated(self, PlaylistTracksList, TrackRow):
		# TODO
		index = 0
		try:
			index = PlaylistTracksList.index(TrackRow)
		except ValueError as e:
			print(e)
			return
		# playlistUri = PlaylistTbV


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

	def initializePlaylistsOverview(self):
		def initBackButton():
			self.backButtonPlaylistsOverview.set_property("active", False)
			self.BackButtonBox.remove(self.BackButtonBox.get_children()[0])
			self.backButtonPlaylistsOverview.visible_child_add_activation_widget(self.PlaylistTracks)
			self.backButtonPlaylistsOverview.visible_child_add_deactivation_widget(self.Playlists)
			self.backButtonPlaylistsOverview.addRequirement(self.playlist_tracks_focused)
			self.BackButtonBox.add(self.backButtonPlaylistsOverview)
			self.PlaylistsOverview.bind_property("folded", self.backButtonPlaylistsOverview, "active")
			self.PlaylistsOverview.bind_property("visible-child", self.backButtonPlaylistsOverview, "visible_child_fake")
			self.PlaylistsOverview.bind_property("folded", self.backButtonPlaylistsOverview, "visible")
			self.backButtonPlaylistsOverview.connect("clicked", self.onPlaylistOverviewBackButtonClicked)
			self.BackButtonBox.show_all()

		def initLists():
			self.TracksListStopEvent = threading.Event()
			self.TracksListResumeEvent = threading.Event()
			self.TracksListResumeEvent.set()
			self.PlaylistsList.connect("row-activated", self.onPlaylistsListRowActivated)
			self.spGUI = SpotifyGuiBuilder()
			self.spGUI.asyncLoadPlaylists(self.PlaylistsList)

		initBackButton()
		initLists()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.initializePlaylistsOverview()

		self.RevealButton.connect("clicked", self.toggleReveal)
