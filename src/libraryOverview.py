# libraryOverview.py
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

from gi.repository import GObject, Handy, Gtk, GLib, Gio
from .contentDeck import ContentDeck

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/libraryOverview.ui')
class LibraryOverview(Handy.Leaflet):
	__gtype_name__ = 'LibraryOverview'

	PrimaryViewport = Gtk.Template.Child()
	SecondaryBox = Gtk.Template.Child()

	def __init__(self, guiBuilder, backButton, **kwargs):
		super().__init__(**kwargs)

		self.GuiBuilder = guiBuilder
		self.BackButton = backButton

		self.connect("notify::folded", self.__onFoldedChange)
		self.connect("notify::visible-child", self.__onChildSwitched)
		self.BackButton.connect("clicked", self.__onBackButtonClicked)

		self.ContentDeck = ContentDeck(Gtk.Label("Select one of the options in the library."))

		# TODO Build the list of playlists (also add the saved songs and maybe somehow the spotify created playlists
		# TODO add callback for those playlists to load the PlaylistPage
		self.Library = Gtk.ListBox()
		self.GuiBuilder.loadLibrary(self.Library)
		self.PrimaryViewport.add(self.Library)
		self.SecondaryBox.pack_start(self.ContentDeck, True, True, 0)
		self.show_all()

	def __onFoldedChange(self, _):
		if self.get_folded():
			if self.get_visible_child() == self.PrimaryBox:
				self.BackButton.hide()
			else:
				self.BackButton.show()
		else:
			self.BackButton.hide()

	def __onChildSwitched(self, _):
		if self.get_visible_child() == self.PrimaryBox:
			self.BackButton.hide()
		else:
			if self.get_folded():
				self.BackButton.show()
			else:
				self.BackButton.hide()

	def __onBackButtonClicked(self, _):
		if self.ContentDeck.isEmpty():
			self.set_visible_child(self.PrimaryBox)
		else:
			self.ContentDeck.pop()
