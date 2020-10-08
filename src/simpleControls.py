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

from gi.repository import GObject, Gtk

@Gtk.Template(resource_path='/xyz/merlinx/Spotipyne/simpleControls.ui')
class SimpleControls(Gtk.Revealer):
	__gtype_name__ = 'SimpleControls'

	def __init__(self, parent, **kwargs):
		super().__init__(**kwargs)
		parent.pack_start(self, False, True, 0)
		self.__progressbar_box = Gtk.Template.Child()
		self.__progressbar = Gtk.Template.Child()
		self.__mainbox = Gtk.Template.Child()
		self.set_reveal_child(True)
