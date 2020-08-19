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

import gi
gi.require_version('Handy', '1')
from gi.repository import Gtk, Handy

from .spotifyGuiBuilder import SpotifyGuiBuilder


@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/window.ui')
class SpotipyneWindow(Handy.ApplicationWindow):
	__gtype_name__ = 'SpotipyneWindow'

	Handy.init()
	# squeezer = Gtk.Template.Child()
	HeaderbarSwitcher = Gtk.Template.Child()
	BottomSwitcher = Gtk.Template.Child()
	MainStack = Gtk.Template.Child()
	PlaylistsOverview = Gtk.Template.Child()
	PlaylistsList = Gtk.Template.Child()
	PlaylistTracks = Gtk.Template.Child()
	PlaylistTracksList = Gtk.Template.Child()
	BackButton = Gtk.Template.Child()

	# def on_headerbar_squeezer_notify(self, squeezer, event):
	# 	child = squeezer.get_visible_child()
	# 	self.bottom_switcher.set_reveal(child != self.headerbar_switcher)

	def getCurrentOverview(self):
		return self.MainStack.get_visible_child()

	def showBackButtonIfApplicable(self, leaflet, childNumber, switchTime):
		if childNumber == 1:
			self.BackButton.show()

	def actionBackButton(self, button):
		button.hide()
		self.getCurrentOverview().set_visible_child_name("0")
		self.spGUI.loadPlaylistTracksList(None)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.BackButton.connect("clicked", self.actionBackButton)
		self.BackButton.hide()
		self.spGUI = SpotifyGuiBuilder(window=self)
		self.spGUI.setPlaylistEntries()
		self.spGUI.loadPlaylistTracksList(None)
		self.PlaylistsList.connect("row-activated", self.spGUI.activatePlaylist)
		self.PlaylistsOverview.connect("child-switched", self.showBackButtonIfApplicable)
		self.PlaylistsList.show_all()
