# searchOverview.py
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

from gi.repository import GObject, Gtk, GLib, Gio

from .spotify import Spotify as sp
from .coverArtLoader import Dimensions

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/searchOverview.ui')
class SearchOverview(Gtk.Box):
	__gtype_name__ = 'SearchOverview'

	SearchBarEntry = Gtk.Template.Child()
	SearchDeck = Gtk.Template.Child()

	def __init__(self, GuiBuilder, backButton, **kwargs):
		super().__init__(**kwargs)
		self.GuiBuilder = GuiBuilder
		self.BackButton = backButton
		self.SearchBarEntry.connect("activate", self.search)
		self.SearchBarEntry.set_placeholder_text("Search")
		self.ScrolledWindow = Gtk.ScrolledWindow()
		self.SearchResultsBoxes = [Gtk.Box(orientation=Gtk.Orientation.VERTICAL)]
		startSearchLabel = Gtk.Label("Input a search request and press enter...", xalign=0)
		self.SearchResultsBoxes[0].pack_start(startSearchLabel, False, True, 0)
		self.ScrolledWindow.add(self.SearchResultsBox)
		self.SearchDeck.add(self.ScrolledWindow)
		self.SearchOverlay = None

		def onDecksVisibleChildChanged(deck, _):
			if self.SearchDeck.get_visible_child() == self.ScrolledWindow:
				self.BackButton.hide()
			else:
				self.BackButton.show()

		self.SearchDeck.connect("notify::visible-child", onDecksVisibleChildChanged)

		def onBackButtonClicked(button):
			self.popFromSearchDeck()

		self.BackButton.connect("clicked", onBackButtonClicked)

		self.show_all()

	# TODO use a stack like layout using the Deck instead
	def __setNewResultsBox(self, newBox):
		self.ScrolledWindow.remove(self.SearchResultsBox)
		self.SearchResultsBox = newBox
		self.ScrolledWindow.add(self.SearchResultsBox)
		self.show_all()

	def setSearchOverlay(self, widget):
		if self.SearchOverlay is not None:
			self.SearchDeck.remove(self.SearchOverlay)
		self.SearchDeck.add(widget)
		self.SearchDeck.set_visible_child(widget)
		self.SearchOverlay = widget

	def setNewSearch(self, text):
		searchResponse = sp.get().search(text, limit=4, offset=0, type='track,playlist,show,episode,album,artist')
		def _setNewSearch():
			newSearchResultsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
			self.GuiBuilder.buildSearchResults(newSearchResultsBox, searchResponse, self.setSearchOverlay)
			self.remove(self.SearchResultsBox)
			self.__setNewResultsBox(newSearchResultsBox)
		GLib.idle_add(_setNewSearch)

	def search(self, entry):
		text = entry.get_buffer().get_text()
		thread = threading.Thread(target=self.setNewSearch, daemon=True, args=(text,))
		thread.start()
