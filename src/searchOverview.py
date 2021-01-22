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

from gi.repository import Gtk, GLib

from .spotify import Spotify as sp
from .contentDeck import ContentDeck


@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/searchOverview.ui')
class SearchOverview(Gtk.Box):
    __gtype_name__ = 'SearchOverview'

    search_bar_entry = Gtk.Template.Child()

    def __init__(self, gui_builder, back_button, **kwargs):
        super().__init__(**kwargs)
        self.gui_builder = gui_builder
        self.back_button = back_button
        self.search_bar_entry.connect("activate", self.search)
        self.search_bar_entry.set_placeholder_text("Search")
        self.scrolled_window = Gtk.ScrolledWindow()
        self.search_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        start_search_label = Gtk.Label(
            "Input a search request and press enter...", xalign=0)
        self.search_results_box.pack_start(start_search_label, False, True, 0)
        self.search_deck = ContentDeck(default_widget=self.search_results_box)
        self.pack_start(self.search_deck, True, True, 0)

        def on_back_button_clicked(button):
            self.search_deck.pop()

        def on_decks_visible_child_changed(deck, _):
            if deck.isEmpty():
                self.back_button.hide()
            else:
                self.back_button.show()

        self.back_button.connect("clicked", on_back_button_clicked)
        self.search_deck.connect(
            "notify::visible-child",
            on_decks_visible_child_changed)

        self.show_all()

    def set_search_results(self, widget):
        self.search_deck.clear()
        self.search_deck.set_default_widget(widget)

    def set_new_search(self, text):
        search_response = sp.get().search(
            text, limit=4, offset=0,
            type='track,playlist,show,episode,album,artist')

        def _set_new_search():
            new_search_results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.gui_builder.build_search_results(
                new_search_results_box, search_response, self.search_deck.push)
            self.remove(self.search_results_box)
            self.set_search_results(new_search_results_box)
        GLib.idle_add(_set_new_search)

    def search(self, entry):
        text = entry.get_buffer().get_text()
        thread = threading.Thread(
            target=self.set_new_search,
            daemon=True,
            args=(
                text,
                ))
        thread.start()
