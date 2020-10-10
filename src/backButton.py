# backButton.py
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

from gi.repository import Gtk, GObject

class BackButton(Gtk.Button):

	requirementChecks = []
	callbacks = []
	deactivation_widgets = []
	activation_widgets = []

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self.__active = False
		self.set_image(Gtk.Image.new_from_icon_name("go-previous-symbolic.symbolic", Gtk.IconSize.BUTTON))


	def addRequirement(self, requirement):
		self.requirementChecks.append(requirement)

	def addCallback(self, callback):
		self.callbacks.append(callback)

	def visible_child_add_deactivation_widget(self, widget):
		self.deactivation_widgets.append(widget)

	def visible_child_add_activation_widget(self, widget):
		self.activation_widgets.append(widget)

	@GObject.Property(type=bool,default=False)
	def active(self):
		return self.__active

	@active.setter
	def active(self, new_value):
		for requirement in self.requirementChecks:
			if not requirement():
				new_value = False
		self.set_sensitive(new_value)
		self.__active = new_value
		for callback in self.callbacks:
			callback()

	@GObject.Property(type=Gtk.Widget)
	def visible_child_fake(self):
		return None

	@visible_child_fake.setter
	def visible_child_fake(self, widget):
		if widget in self.deactivation_widgets:
			self.active = False
		elif widget in self.activation_widgets:
			self.active = True

