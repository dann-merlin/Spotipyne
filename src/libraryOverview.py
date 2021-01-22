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

from gi.repository import Handy, Gtk
from .contentDeck import ContentDeck


@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/libraryOverview.ui')
class LibraryOverview(Handy.Leaflet):
    __gtype_name__ = 'LibraryOverview'

    primary_box = Gtk.Template.Child()
    primary_viewport = Gtk.Template.Child()
    secondary_box = Gtk.Template.Child()

    def __init__(self, gui_builder, back_button, **kwargs):
        super().__init__(**kwargs)

        self.gui_builder = gui_builder
        self.back_button = back_button

        self.connect("notify::folded", self.__on_folded_change)
        self.connect("notify::visible-child", self.__on_child_switched)
        self.back_button.connect("clicked", self.__on_back_button_clicked)

        self.content_deck = ContentDeck(
            Gtk.Label("Select one of the options in the library."))

        # TODO Build the list of playlists (also add the saved songs and maybe somehow the spotify created playlists
        # TODO add callback for those playlists to load the PlaylistPage
        def set_widget_function(widget):
            self.secondary_box.remove(self.content_deck)
            self.contentDeck = ContentDeck(
                Gtk.Label("Select one of the options in the library."))
            self.secondary_box.pack_start(self.content_deck, True, True, 0)
            self.content_deck.push(widget)
            self.set_visible_child(self.secondary_box)

        def push_widget_function(widget):
            self.content_deck.push(widget)
            self.set_visible_child(self.secondary_box)
        self.library = Gtk.ListBox()
        self.gui_builder.load_library(
            self.library,
            set_widget_function,
            push_widget_function)
        self.primary_viewport.add(self.library)
        self.secondary_box.pack_start(self.content_deck, True, True, 0)
        self.show_all()

    def __on_folded_change(self, _overview, _folded):
        print("FOLD!")
        if self.get_folded():
            if self.get_visible_child() == self.primary_box:
                self.back_button.hide()
            else:
                self.back_button.show()
        else:
            self.back_button.hide()

    def __on_child_switched(self, _overview, _child):
        if self.get_visible_child() == self.primary_box:
            self.back_button.hide()
        else:
            if self.get_folded():
                self.back_button.show()
            else:
                self.back_button.hide()

    def __on_back_button_clicked(self, _):
        self.content_deck.pop()
        if self.content_deck.isEmpty():
            self.set_visible_child(self.primary_box)
