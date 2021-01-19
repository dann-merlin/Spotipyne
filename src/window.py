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

from gi.repository import Gtk, Handy, GObject

from .cover_art_loader import CoverArtLoader
from .spotify_gui_builder import SpotifyGuiBuilder
from .spotify_playback import SpotifyPlayback
from .simple_controls import SimpleControls
from .search_overview import SearchOverview
from .login import Login


@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/window.ui')
class SpotipyneWindow(Handy.ApplicationWindow):
    __gtype_name__ = 'SpotipyneWindow'

    Handy.init()
    headerbar_switcher = Gtk.Template.Child()
    bottom_switcher = Gtk.Template.Child()
    player_deck = Gtk.Template.Child()
    main_stack = Gtk.Template.Child()
    library_overview = Gtk.Template.Child()
    primary_box = Gtk.Template.Child()
    playlists_list = Gtk.Template.Child()
    secondary_box = Gtk.Template.Child()
    playlist_tracks_list = Gtk.Template.Child()
    back_button_stack = Gtk.Template.Child()
    back_button_playlists = Gtk.Template.Child()
    back_button_search = Gtk.Template.Child()
    simple_controls_parent = Gtk.Template.Child()
    revealer = Gtk.Template.Child()
    reveal_button = Gtk.Template.Child()
    secondary_viewport = Gtk.Template.Child()

    def on_playlists_list_row_activated(self, _playlists_list, playlist_row):
        def load_playlist_tracks():
            built_page = self.sp_gui.build_playlist_page(
                playlist_row.get_uri()
            )
            # TODO has the next line to be commented in?
            self.secondary_viewport.remove(self.secondary_viewport.get_child())
            self.secondary_viewport.add(built_page)
            self.secondary_viewport.show_all()

        load_playlist_tracks()
        self.library_overview.set_visible_child(self.secondary_box)

    def toggle_reveal(self, _button):
        self.revealer.set_reveal_child(not self.revealer.get_reveal_child())

    def playlist_tracks_focused(self):
        return self.library_overview.get_visible_child() == self.secondary_box

    def init_cover_art_loader(self):
        self.cover_art_loader = CoverArtLoader()

    def init_library_overview(self):

        def init_lists():
            self.playlists_list.connect(
                "row-activated", self.on_playlists_list_row_activated)
            self.sp_gui.async_load_playlists(self.playlists_list)

        init_lists()

        def on_folded_change(playlists_overview, _):
            # For some reason the folded variable can not be trusted
            if playlists_overview.get_folded():
                if playlists_overview.get_visible_child() == self.primary_box:
                    self.back_button_playlists.hide()
                else:
                    self.back_button_playlists.show()
            else:
                self.back_button_playlists.hide()

        def on_child_switched(playlists_overview, _):
            if playlists_overview.get_visible_child() == self.primary_box:
                self.back_button_playlists.hide()
            else:
                if playlists_overview.get_folded():
                    self.back_button_playlists.show()
                else:
                    self.back_button_playlists.hide()

        def on_clicked_back_button(_back_button):
            self.library_overview.set_visible_child(self.primary_box)

        self.library_overview.connect("notify::folded", on_folded_change)
        self.library_overview.connect(
            "notify::visible-child", on_child_switched)
        self.back_button_playlists.connect("clicked", on_clicked_back_button)

    def init_spotify_playback(self):
        self.spotify_playback = SpotifyPlayback(self.cover_art_loader)

    def init_simple_controls(self):
        self.simple_controls = SimpleControls(self.spotify_playback)
        self.simple_controls_parent.pack_start(
            self.simple_controls, False, True, 0)
        self.simple_controls.set_reveal_child(False)

    def init_search_overview(self):
        self.search_overview = SearchOverview(
            self.sp_gui, self.back_button_search)
        self.main_stack.add_titled(self.search_overview, 'Search', 'Search')
        self.main_stack.child_set_property(
            self.search_overview, "icon-name", "edit-find-symbolic")

    def init_back_buttons(self):
        # TODO what the hell did i think?
        # self.BackButtonStack.child_set_property
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

        self.headerbar_switcher.bind_property("title-visible",
                                              self.bottom_switcher, "reveal",
                                              GObject.BindingFlags.SYNC_CREATE)

        self.reveal_button.connect("clicked", self.toggle_reveal)
