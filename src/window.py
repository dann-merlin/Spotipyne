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
from gi.repository import Gtk, Handy, GObject, GLib

from .coverArtLoader import CoverArtLoader
from .spotifyGuiBuilder import SpotifyGuiBuilder
from .spotify import Spotify as sp
from .spotifyPlayback import SpotifyPlayback
from .simpleControls import SimpleControls
from .libraryOverview import LibraryOverview
from .searchOverview import SearchOverview
from .login import Login

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/window.ui')
class SpotipyneWindow(Handy.ApplicationWindow):
	__gtype_name__ = 'SpotipyneWindow'

	Handy.init()
	HeaderbarSwitcher = Gtk.Template.Child()
	BottomSwitcher = Gtk.Template.Child()
	PlayerDeck = Gtk.Template.Child()
	MainStack = Gtk.Template.Child()
	BackButtonStack = Gtk.Template.Child()
	BackButtonPlaylists = Gtk.Template.Child()
	BackButtonSearch = Gtk.Template.Child()
	SimpleControlsParent = Gtk.Template.Child()
	Revealer = Gtk.Template.Child()
	RevealButton = Gtk.Template.Child()

	def toggleReveal(self, button):
		self.Revealer.set_reveal_child( not self.Revealer.get_reveal_child())

	def initCoverArtLoader(self):
		self.coverArtLoader = CoverArtLoader()

	def initSpotifyPlayback(self):
		self.spotifyPlayback = SpotifyPlayback(self.coverArtLoader)

	def initSimpleControls(self):
		self.simpleControls = SimpleControls(self.spotifyPlayback)
		self.SimpleControlsParent.pack_start(self.simpleControls, False, True, 0)
		self.simpleControls.set_reveal_child(False)

	def initLibraryOverview(self):
		self.libraryOverview = LibraryOverview(self.spGUI, self.BackButtonPlaylists)
		self.MainStack.add_titled(self.libraryOverview, 'Library', 'Library')
		self.MainStack.child_set_property(self.libraryOverview, 'icon-name', 'applications-multimedia-symbolic')

	def initSearchOverview(self):
		self.searchOverview = SearchOverview(self.spGUI, self.BackButtonSearch)
		self.MainStack.add_titled(self.searchOverview, 'Search', 'Search')
		self.MainStack.child_set_property(self.searchOverview, 'icon-name', 'edit-find-symbolic')

	def initBackButtons(self):
		self.BackButtonStack.child_set_property
		self.MainStack.bind_property("visible-child-name", self.BackButtonStack, "visible-child-name")

	def initLogin(self):
		self.LoginPage = Login(self.onLoggedIn)
		self.PlayerDeck.add(self.LoginPage)
		self.PlayerDeck.set_visible_child(self.LoginPage)
		self.PlayerDeck.show_all()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.initLogin()

	def onLoggedIn(self):
		self.PlayerDeck.remove(self.LoginPage)
		self.PlayerDeck.set_visible_child(self.PlayerDeck.get_children()[0])

		self.initCoverArtLoader()

		self.spGUI = SpotifyGuiBuilder(self.coverArtLoader)

		self.initLibraryOverview()

		self.initSearchOverview()

		self.initSpotifyPlayback()

		self.initSimpleControls()

		self.initBackButtons()

		self.HeaderbarSwitcher.bind_property("title-visible", self.BottomSwitcher, "reveal", GObject.BindingFlags.SYNC_CREATE)

		self.RevealButton.connect("clicked", self.toggleReveal)
