# login.py
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

from gi.repository import Gtk, GLib

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/login.ui')
class Login(Gtk.Bin):
	__gtype_name__ = 'Login'

	LoginListBox = Gtk.Template.Child()

	def __init__(self, onLoggedIn, **kwargs):
		super().__init__(**kwargs)
		self.buttonCallback = onLoggedIn
		self.SubmitButton = Gtk.Button("Submit")
		username_label = Gtk.Label('Username: ')
		username_input = Gtk.Entry()
		username_input.set_placeholder_text('Input username here')
		box_username = Gtk.FlowBox()
		box_username.set_homogeneous(True)
		box_username.add(username_label)
		box_username.add(username_input)
		password_label = Gtk.Label('Password: ')
		password_input = Gtk.Entry()
		password_input.set_placeholder_text('Input password here')
		password_input.set_visibility(False)
		password_input.set_invisible_char('*')
		box_password = Gtk.FlowBox()
		box_password.set_homogeneous(True)
		box_password.add(password_label)
		box_password.add(password_input)
		self.LoginListBox.add(Gtk.Label("Login to Spotify"))
		self.LoginListBox.add(box_username)
		self.LoginListBox.add(box_password)
		self.LoginListBox.add(self.SubmitButton)
		self.show_all()
		def onButtonPressed(button):
			GLib.idle_add(self.buttonCallback)
		self.SubmitButton.connect("clicked", onButtonPressed)

