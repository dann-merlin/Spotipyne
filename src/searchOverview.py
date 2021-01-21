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
from .contentDeck import ContentDeck


@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/searchOverview.ui')
class SearchOverview(Gtk.Box):
    __gtype_name__ = 'SearchOverview'

    SearchBarEntry = Gtk.Template.Child()

    def __init__(self, GuiBuilder, backButton, **kwargs):
        super().__init__(**kwargs)
        self.GuiBuilder = GuiBuilder
        self.BackButton = backButton
        self.SearchBarEntry.connect("activate", self.search)
        self.SearchBarEntry.set_placeholder_text("Search")
        self.ScrolledWindow = Gtk.ScrolledWindow()
        self.SearchResultsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        startSearchLabel = Gtk.Label(
            "Input a search request and press enter...", xalign=0)
        self.SearchResultsBox.pack_start(startSearchLabel, False, True, 0)
        self.SearchDeck = ContentDeck(defaultWidget=self.SearchResultsBox)
        self.pack_start(self.SearchDeck, True, True, 0)

        def onBackButtonClicked(button):
            self.SearchDeck.pop()

        def onDecksVisibleChildChanged(deck, _):
            if deck.isEmpty():
                self.BackButton.hide()
            else:
                self.BackButton.show()

        self.BackButton.connect("clicked", onBackButtonClicked)
        self.SearchDeck.connect(
            "notify::visible-child",
            onDecksVisibleChildChanged)

        self.show_all()

    def setSearchResults(self, widget):
        self.SearchDeck.clear()
        self.SearchDeck.setDefaultWidget(widget)

    def setNewSearch(self, text):
        searchResponse = sp.get().search(
            text, limit=4, offset=0,
            type='track,playlist,show,episode,album,artist')

        def _setNewSearch():
            newSearchResultsBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.GuiBuilder.buildSearchResults(
                newSearchResultsBox, searchResponse, self.SearchDeck.push)
            self.remove(self.SearchResultsBox)
            self.setSearchResults(newSearchResultsBox)
        GLib.idle_add(_setNewSearch)

    def search(self, entry):
        text = entry.get_buffer().get_text()
        thread = threading.Thread(
            target=self.setNewSearch,
            daemon=True,
            args=(
                text,
                ))
        thread.start()
