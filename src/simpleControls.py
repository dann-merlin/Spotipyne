# simpleControls.py
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

from .spotifyPlayback import SpotifyPlayback
from .spotify import Spotify as sp
from .coverArtLoader import Dimensions

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/simpleControls.ui')
class SimpleControls(Gtk.Revealer):
	__gtype_name__ = 'SimpleControls'

	class PlaybackButton(Gtk.Button):

		def __init__(self, spotifyPlayback, **kwargs):
			super().__init__(**kwargs)
			self.pb = spotifyPlayback
			self.pb.connect("is_playing_changed", self.updateLabel)
			self.connect("clicked", self.on_clicked)
			self.show()
			self.playing_image = Gtk.Image.new_from_icon_name("media-playback-pause", Gtk.IconSize.LARGE_TOOLBAR)
			self.paused_image = Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.LARGE_TOOLBAR)

		def updateLabel(self, spotifyPlayback, is_playing):
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

			thread = threading.Thread(target=to_bg)
			thread.start()

	class SimpleProgressBar(Gtk.ProgressBar):

		def __init__(self, spotifyPlayback, **kwargs):
			super().__init__(**kwargs)
			self.__smooth_time_ms = 150
			self.__smoothing_speed = 0.0
			self.pb = spotifyPlayback
			self.pb.connect("track_changed", self.updateSmoothingSpeed)
			self.pb.connect("is_playing_changed", self.updateSmoother)
			self.__smooth_updater = None

		def updateSmoother(self, spotifyPlayback, is_playing):
			if is_playing:
				self.__smooth_updater = GLib.timeout_add(interval=self.__smooth_time_ms, function=self.updateFractionSmoothly)
			elif self.__smooth_updater is not None:
				GLib.source_remove(self.__smooth_updater)

		def updateSmoothingSpeed(self, spotifyPlayback, track_uri):
			self.__smoothing_speed = self.__smooth_time_ms / spotifyPlayback.duration_ms
			print("new smoothing speed is: " + str(self.__smoothing_speed))

		def updateFractionSmoothly(self):
			self.set_fraction(self.get_fraction() + self.__smoothing_speed)
			return True

	progressbar_box = Gtk.Template.Child()
	mainbox = Gtk.Template.Child()

	def __init__(self, spotifyPlayback, **kwargs):
		super().__init__(**kwargs)
		self.progressbar = self.SimpleProgressBar(spotifyPlayback)
		self.progressbar_box.pack_start(self.progressbar, False, True, 0)
		self.progressbar_box.reorder_child(self.progressbar, 0)

		self.coverArt = Gtk.Image()
		self.mainbox.pack_start(self.coverArt, False, True, 0)

		self.songLabel = Gtk.Label()
		self.songLabel.set_line_wrap(False)
		self.mainbox.pack_start(self.songLabel, False, True, 0)

		spotifyPlayback.connect("track_changed", self.on_track_changed)
		def reveal_child(_, reveal):
			print("Reveal: " + str(reveal))
			self.set_reveal_child(reveal)
		spotifyPlayback.connect("has_playback", reveal_child)

		self.devices_menu = Gio.Menu()
		self.devices_list_menu = Gio.Menu()
		self.devices_list_menu.append("Device1", None)
		self.devices_list_menu.append("Device2", None)
		spotifyPlayback.connect("devices_changed", self.updateDevicesList)
		self.updateDevicesList(spotifyPlayback)
		self.devices_menu.append_section("Devices", self.devices_list_menu)

		devices_button = Gtk.MenuButton()
		self.devices_popover = Gtk.Popover.new_from_model(devices_button, self.devices_menu)
		self.devices_popover.set_relative_to(devices_button)
		devices_button.set_popover(self.devices_popover)
		devices_button.set_direction(Gtk.ArrowType.UP)
		devices_button.set_image(Gtk.Image.new_from_icon_name("multimedia-player-symbolic.symbolic", Gtk.IconSize.LARGE_TOOLBAR))
		heart_button = Gtk.Button.new_from_icon_name("emblem-favorite-symbolic.symbolic", Gtk.IconSize.LARGE_TOOLBAR)
		play_button = self.PlaybackButton(spotifyPlayback)
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

		spotifyPlayback.bind_property("progress_fraction", self.progressbar, "fraction")
		self.show_all()

	def updateDevicesList(self, spotifyPlayback):
		def testCallback(action, value, device_name):
			print("Callback from action: " + str(action))
			print("with value: " + str(value))
			print("Device name: " + str(device_name))
		self.devices_list_menu.remove_all()
		devs = spotifyPlayback.get_devices()
		self.set_reveal_child(len(devs) != 0)
		new_device_names = [ dev['name'] for dev in devs ]
		self.action_group = Gio.SimpleActionGroup.new()
		for dev_name in new_device_names:
			action_name = dev_name
			device_action = Gio.SimpleAction(name=dev_name)
			Gio.Application.get_default().add_action(device_action)
			device_action.connect("activate", testCallback, dev_name)
			detailed_action = "app." + dev_name
			self.devices_list_menu.append(dev_name, detailed_action)

	def updateSongLabel(self, spotifyPlayback):
		label_string = '<b>' + GLib.markup_escape_text(spotifyPlayback.get_track_name()) + '</b>'
		label_string += '\n'
		label_string += GLib.markup_escape_text(spotifyPlayback.get_artist_names())
		self.songLabel.set_markup(label_string)

	def on_track_changed(self, spotifyPlayback, track_uri):
		spotifyPlayback.set_current_cover_art(self.coverArt, Dimensions(60,60,True))
		self.updateSongLabel(spotifyPlayback)
