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
		self.SearchResultsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		startSearchLabel = Gtk.Label("Input a search request and press enter...", xalign=0)
		self.SearchResultsBox.pack_start(startSearchLabel, False, True, 0)
		self.SearchDeckStack = []
		self.ScrolledWindow.add(self.SearchResultsBox)
		self.SearchDeck.add(self.ScrolledWindow)

		def onDecksVisibleChildChanged(deck, _):
			if self.SearchDeck.get_visible_child() == self.ScrolledWindow:
				self.BackButton.hide()
			else:
				self.BackButton.show()

		self.SearchDeck.connect("notify::visible-child", onDecksVisibleChildChanged)

		def onBackButtonClicked(button):
			self.popOverlay()

		self.BackButton.connect("clicked", onBackButtonClicked)

		self.show_all()

	# TODO use a stack like layout using the Deck instead
	def __setNewOverlayBox(self, newBox):
		self.ScrolledWindow.remove(self.SearchResultsBox)
		self.SearchResultsBox = newBox
		self.ScrolledWindow.add(self.SearchResultsBox)
		self.show_all()

	def popOverlay(self):
		if len(self.SearchDeckStack) == 1:
			self.SearchDeck.set_visible_child(self.ScrolledWindow)
		else:
			self.SearchDeck.set_visible_child(self.SearchDeckStack[-2])
		connectionID = 0
		def onTransitionRunning(deck, _):
			if not deck.get_transition_running():
				deck.remove(self.SearchDeckStack.pop())
				deck.disconnect(connectionID)

		connectionID = self.SearchDeck.connect("notify::transition-running", onTransitionRunning)

	def pushOverlay(self, newBox):
		self.SearchDeckStack.append(newBox)
		self.SearchDeck.add(newBox)
		self.SearchDeck.set_visible_child(newBox)

	def setSearchResults(self, widget):
		for child in self.SearchDeck.get_children()[1:]:
			self.SearchDeck.remove(child)
		self.ScrolledWindow.remove(self.ScrolledWindow.get_child())
		self.ScrolledWindow.add(widget)
		self.SearchDeck.set_visible_child(self.ScrolledWindow)

	def setNewSearch(self, text):
		searchResponse = sp.get().search(text, limit=4, offset=0, type='track,playlist,show,episode,album,artist')
		def _setNewSearch():
			newSearchResultsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
			self.GuiBuilder.buildSearchResults(newSearchResultsBox, searchResponse, self.pushOverlay)
			self.remove(self.SearchResultsBox)
			self.setSearchResults(newSearchResultsBox)
		GLib.idle_add(_setNewSearch)

	def search(self, entry):
		text = entry.get_buffer().get_text()
		thread = threading.Thread(target=self.setNewSearch, daemon=True, args=(text,))
		thread.start()
