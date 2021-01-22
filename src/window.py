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

from .login import Login
from .searchOverview import SearchOverview
from .libraryOverview import LibraryOverview
from .simpleControls import SimpleControls
from .spotifyPlayback import SpotifyPlayback
from .spotifyGuiBuilder import SpotifyGuiBuilder
from .coverArtLoader import CoverArtLoader
from gi.repository import Gtk, Handy, GObject

import gi
gi.require_version('Handy', '1')


@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/window.ui')
class SpotipyneWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'SpotipyneWindow'

    Handy.init()
    headerbar_switcher = Gtk.Template.Child()
    bottom_switcher = Gtk.Template.Child()
    player_deck = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    back_button_stack = Gtk.Template.Child()
    back_button_playlists = Gtk.Template.Child()
    back_button_search = Gtk.Template.Child()
    simple_controls_parent = Gtk.Template.Child()

    def init_cover_art_loader(self):
        self.cover_art_loader = CoverArtLoader()

    def init_spotify_playback(self):
        self.spotify_playback = SpotifyPlayback(self.cover_art_loader)

    def init_simple_controls(self):
        self.simple_controls = SimpleControls(self.spotify_playback)
        self.simple_controls_parent.pack_start(
            self.simple_controls, False, True, 0)
        self.simple_controls.set_reveal_child(False)

    def init_library_overview(self):
        self.library_overview = LibraryOverview(
            self.sp_gui, self.back_button_playlists)
        self.main_stack.add_titled(self.library_overview, 'Library', 'Library')
        self.main_stack.child_set_property(
            self.library_overview, 'icon-name',
            'applications-multimedia-symbolic')

    def init_search_overview(self):
        self.search_overview = SearchOverview(self.sp_gui, self.back_button_search)
        self.main_stack.add_titled(self.search_overview, 'Search', 'Search')
        self.main_stack.child_set_property(
            self.search_overview, 'icon-name', 'edit-find-symbolic')

    def init_back_buttons(self):
        self.back_button_stack.child_set_property
        self.main_stack.bind_property(
            "visible-child-name",
            self.back_button_stack,
            "visible-child-name")

    def init_login(self):
        self.login_page = Login(self.on_logged_in)
        self.player_deck.add(self.login_page)
        self.player_deck.set_visible_child(self.login_page)
        self.player_deck.show_all()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.init_login()

    def on_logged_in(self):
        self.player_deck.remove(self.login_page)
        self.player_deck.set_visible_child(self.player_deck.get_children()[0])

        self.init_cover_art_loader()

        self.sp_gui = SpotifyGuiBuilder(self.cover_art_loader)

        self.init_library_overview()

        self.init_search_overview()

        self.init_spotify_playback()

        self.init_simple_controls()

        self.init_back_buttons()

        self.headerbar_switcher.bind_property(
            "title-visible",
            self.bottom_switcher,
            "reveal",
            GObject.BindingFlags.SYNC_CREATE)
