# contentDeck.py
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

from gi.repository import GObject, Gtk, Handy

class ContentDeck(Handy.Deck):

	def __init__(self, defaultWidget, **kwargs):
		super().__init__(**kwargs)
		self.set_can_swipe_back(True)
		self.set_can_swipe_forward(False)
		self.set_homogeneous(Gtk.Orientation.HORIZONTAL, True)
		self.set_homogeneous(Gtk.Orientation.VERTICAL, True)
		self.set_transition_duration(200)
		self.set_transition_type(Handy.DeckTransitionType.OVER)
		self.DefaultWidget = Gtk.ScrolledWindow()
		self.DefaultWidget.add(defaultWidget)
		self.add(self.DefaultWidget)
		self.show_all()

		self.Stack = []

		def onDeckTransitionRunning(deck, _):
			if len(deck.Stack) == 0:
				return
			if not deck.get_transition_running():
				visible_child = deck.get_visible_child()
				while visible_child != self.Stack[-1]:
					deck.remove(deck.Stack.pop())
					if len(deck.Stack) == 0:
						return
		self.connect("notify::transition-running", onDeckTransitionRunning)

		# TODO use a Signal or sth instead to indicate, that one might want to change the backbutton
		# def onDecksVisibleChildChanged(deck, _):
		# 	if deck.get_visible_child() == self.DefaultWidget:
		# 		self.BackButton.hide()
		# 	else:
		# 		self.BackButton.show()

		# self.SearchDeck.connect("notify::visible-child", onDecksVisibleChildChanged)

	def setDefaultWidget(self, newDefault):
		self.DefaultWidget.remove(self.DefaultWidget.get_child())
		self.DefaultWidget.add(newDefault)
		self.show_all()

	def pop(self):
		if len(self.Stack) == 0:
			self.set_visible_child(self.DefaultWidget)
			return False
		else:
			self.Stack = self.Stack[:-1]
			if len(self.Stack) == 0:
				self.set_visible_child(self.DefaultWidget)
			else:
				self.set_visible_child(self.Stack[-1])
			return True

	def push(self, newTop):
		scrollableContainer = Gtk.ScrolledWindow()
		scrollableContainer.add(newTop)
		self.Stack.append(scrollableContainer)
		self.add(scrollableContainer)
		self.show_all()
		self.set_visible_child(scrollableContainer)

	def clear(self):
		self.set_visible_child(self.DefaultWidget)
		if len(self) > 1:
			for child in self.get_children()[1:]:
				self.remove(child)
		self.Stack = [self.DefaultWidget]

	def isEmpty(self):
		return self.get_visible_child() == self.DefaultWidget
