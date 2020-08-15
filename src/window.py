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
class SpotipyneWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'SpotipyneWindow'

	Handy.init()
	squeezer = Gtk.Template.Child()
	headerbar_switcher = Gtk.Template.Child()
	bottom_switcher = Gtk.Template.Child()
	MainStack = Gtk.Template.Child()
	PlaylistsList = Gtk.Template.Child()

	def on_headerbar_squeezer_notify(self, squeezer, event):
		child = squeezer.get_visible_child()
		self.bottom_switcher.set_reveal(child != self.headerbar_switcher)

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.squeezer.connect("notify::visible-child", self.on_headerbar_squeezer_notify)
		self.spGUI = SpotifyGuiBuilder()
		self.spGUI.setPlaylistEntries(self.PlaylistsList)
		self.PlaylistsList.show_all()


