# simple_controls.py
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
from spotipy import SpotifyException

from gi.repository import Gtk, GLib, Gio

from .spotify import Spotify as sp
from .coverArtLoader import Dimensions


@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/simple_controls.ui')
class SimpleControls(Gtk.Revealer):
    __gtype_name__ = 'SimpleControls'

    class PlaybackButton(Gtk.Button):

        def __init__(self, spotify_playback, **kwargs):
            super().__init__(**kwargs)
            spotify_playback.connect("is_playing_changed", self.update_label)
            self.connect("clicked", self.on_clicked)
            self.show()
            self.__is_playing = False
            self.playing_image = Gtk.Image.new_from_icon_name(
                "media-playback-pause", Gtk.IconSize.LARGE_TOOLBAR)
            self.paused_image = Gtk.Image.new_from_icon_name(
                "media-playback-start", Gtk.IconSize.LARGE_TOOLBAR)
            self.set_image(self.paused_image)

        def update_label(self, spotify_playback, is_playing):
            self.__is_playing = is_playing

            def to_main_thread():
                if is_playing:
                    self.set_image(self.playing_image)
                else:
                    self.set_image(self.paused_image)
            GLib.idle_add(to_main_thread)

        def on_clicked(self, _):
            def to_bg():
                if self.__is_playing:
                    sp.pause_playback()
                else:
                    sp.start_playback()

            thread = threading.Thread(daemon=True, target=to_bg)
            thread.start()

    class SaveTrackButton(Gtk.Button):

        def __init__(self, spotify_playback, **kwargs):
            super().__init__(**kwargs)
            self.show()
            self.__is_saved_track = False
            self.remove_saved_icon_image = Gtk.Image.new_from_icon_name(
                "list-remove-symbolic.symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            self.add_saved_icon_image = Gtk.Image.new_from_icon_name(
                "list-add-symbolic.symbolic", Gtk.IconSize.LARGE_TOOLBAR)
            self.set_image(self.add_saved_icon_image)
            spotify_playback.connect(
                "is_saved_track_changed", self.update_icon)
            self.connect("clicked", self.on_clicked, spotify_playback)

        def update_icon(self, spotify_playback, is_saved_track):
            self.__is_saved_track = is_saved_track

            def to_main_thread():
                if is_saved_track:
                    self.set_image(self.remove_saved_icon_image)
                else:
                    self.set_image(self.add_saved_icon_image)
            GLib.idle_add(to_main_thread)

        def on_clicked(self, _, spotify_playback):
            def to_bg():
                try:
                    current_track_uri = spotify_playback.track_uri
                    saved = self.__is_saved_track
                    if saved:
                        sp.get().current_user_saved_tracks_delete(
                            [current_track_uri])
                    else:
                        sp.get().current_user_saved_tracks_add(
                            [current_track_uri])
                    spotify_playback.emit("is_saved_track_changed", not saved)
                except SpotifyException as e:
                    print(str(e))
            thread = threading.Thread(daemon=True, target=to_bg)
            thread.start()

    class SimpleProgressBar(Gtk.ProgressBar):

        def __init__(self, spotify_playback, **kwargs):
            super().__init__(**kwargs)
            self.__smooth_time_ms = 150
            self.__smoothing_speed = 0.0
            self.pb = spotify_playback
            self.pb.connect("track_changed", self.update_smoothing_speed)
            self.pb.connect("is_playing_changed", self.update_smoother)
            self.__smooth_updater = None

        def update_smoother(self, spotify_playback, is_playing):
            if is_playing:
                self.__smooth_updater = GLib.timeout_add(
                    interval=self.__smooth_time_ms,
                    function=self.update_fraction_smoothly)
            elif self.__smooth_updater is not None:
                GLib.source_remove(self.__smooth_updater)

        def update_smoothing_speed(self, spotify_playback, track_uri):
            self.__smoothing_speed = self.__smooth_time_ms / spotify_playback.duration_ms

        def update_fraction_smoothly(self):
            self.set_fraction(self.get_fraction() + self.__smoothing_speed)
            return True

    progressbar_box = Gtk.Template.Child()
    mainbox = Gtk.Template.Child()

    def __init__(self, spotify_playback, **kwargs):
        super().__init__(**kwargs)
        self.progressbar = self.SimpleProgressBar(spotify_playback)
        self.progressbar_box.pack_start(self.progressbar, False, True, 0)
        self.progressbar_box.reorder_child(self.progressbar, 0)

        self.cover_art = Gtk.Image()
        self.mainbox.pack_start(self.cover_art, False, True, 0)

        self.song_label = Gtk.Label()
        self.song_label.set_line_wrap(False)
        self.mainbox.pack_start(self.song_label, False, True, 0)

        spotify_playback.connect("track_changed", self.on_track_changed)

        def reveal_child(_, reveal):
            self.set_reveal_child(reveal)
        spotify_playback.connect("has_playback", reveal_child)

        self.devices_menu = Gio.Menu()
        self.devices_list_menu = Gio.Menu()
        self.devices_list_menu.append("Device1", None)
        self.devices_list_menu.append("Device2", None)
        spotify_playback.connect("devices_changed", self.update_devices_list)
        self.update_devices_list(spotify_playback)
        self.devices_menu.append_section("Devices", self.devices_list_menu)

        devices_button = Gtk.MenuButton()
        self.devices_popover = Gtk.Popover.new_from_model(
            devices_button, self.devices_menu)
        self.devices_popover.set_relative_to(devices_button)
        devices_button.set_popover(self.devices_popover)
        devices_button.set_direction(Gtk.ArrowType.UP)
        devices_button.set_image(
            Gtk.Image.new_from_icon_name(
                "multimedia-player-symbolic.symbolic",
                Gtk.IconSize.LARGE_TOOLBAR))
        heart_button = self.SaveTrackButton(spotify_playback)
        play_button = self.PlaybackButton(spotify_playback)
        self.buttons = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)

        devices_button.set_relief(Gtk.ReliefStyle.NONE)
        heart_button.set_relief(Gtk.ReliefStyle.NONE)
        play_button.set_relief(Gtk.ReliefStyle.NONE)

        self.buttons.pack_start(devices_button, False, True, 0)
        self.buttons.pack_start(heart_button, False, True, 0)
        self.buttons.pack_start(play_button, False, True, 0)
        self.buttons.set_homogeneous(True)
        self.buttons.set_halign(Gtk.Align.CENTER)
        self.buttons.set_valign(Gtk.Align.CENTER)
        self.buttons.set_layout(Gtk.ButtonBoxStyle.EXPAND)
        self.mainbox.pack_end(self.buttons, False, True, 10)

        spotify_playback.bind_property(
            "progress_fraction", self.progressbar, "fraction")
        self.show_all()

    def update_devices_list(self, spotify_playback):
        def activate_device(action, value, device_id):
            sp.get().transfer_playback(device_id, force_play=True)
        self.devices_list_menu.remove_all()
        devs = spotify_playback.get_devices()
        self.set_reveal_child(len(devs) != 0)
        self.action_group = Gio.SimpleActionGroup.new()
        for dev in devs:
            dev_name = dev['name']
            device_action = Gio.SimpleAction(name=dev_name)
            Gio.Application.get_default().add_action(device_action)
            device_action.connect("activate", activate_device, dev['id'])
            detailed_action = "app." + dev_name
            self.devices_list_menu.append(dev_name, detailed_action)

    def updateSongLabel(self, spotify_playback):
        label_string = '<b>' + GLib.markup_escape_text(
            spotify_playback.get_track_name()) + '</b>'
        label_string += '\n'
        label_string += GLib.markup_escape_text(
            spotify_playback.get_artist_names())
        self.song_label.set_markup(label_string)

    def on_track_changed(self, spotify_playback, track_uri):
        spotify_playback.set_current_cover_art(
            self.cover_art, Dimensions(60, 60, True))
        self.updateSongLabel(spotify_playback)
