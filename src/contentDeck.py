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

from gi.repository import Gtk, Handy


class ContentDeck(Handy.Deck):

    transition_duration = 200

    def __init__(self, default_widget, **kwargs):
        super().__init__(**kwargs)

        self.set_can_swipe_back(True)
        self.set_can_swipe_forward(False)
        self.set_homogeneous(Gtk.Orientation.HORIZONTAL, True)
        self.set_homogeneous(Gtk.Orientation.VERTICAL, True)
        self.set_transition_duration(self.transition_duration)
        self.set_transition_type(Handy.DeckTransitionType.OVER)
        self.default_widget = Gtk.ScrolledWindow()
        self.default_widget.add(default_widget)
        self.add(self.default_widget)
        self.show_all()

        self.stack = []

        def on_deck_transition_running(deck, _):
            if len(deck.stack) == 0:
                return
            if not deck.get_transition_running():
                visible_child = deck.get_visible_child()
                while visible_child != self.stack[-1]:
                    deck.remove(deck.stack.pop())
                    if len(deck.stack) == 0:
                        return
        self.connect("notify::transition-running", on_deck_transition_running)

    def set_default_widget(self, new_default):
        self.default_widget.remove(self.default_widget.get_child())
        self.default_widget.add(new_default)
        self.show_all()

    def pop(self):
        if len(self.stack) == 0:
            self.set_visible_child(self.default_widget)
            return None
        else:
            last = self.stack[-1]
            if hasattr(last, "page_stop_event"):
                print("stop this page")
                last.page_stop_event.set()
            self.stack = self.stack[:-1]
            if len(self.stack) == 0:
                self.set_visible_child(self.default_widget)
            else:
                self.set_visible_child(self.stack[-1])
            return last

    def push(self, new_top):
        scrollable_container = Gtk.ScrolledWindow()
        scrollable_container.add(new_top)
        self.stack.append(scrollable_container)
        self.add(scrollable_container)
        self.show_all()
        self.set_visible_child(scrollable_container)

    def clear(self):
        self.set_visible_child(self.default_widget)
        if len(self) > 1:
            for child in self.get_children()[1:]:
                self.remove(child)
        self.stack = []

    def reset_push(self, widget):
        self.set_transition_duration(0)
        self.push(widget)
        for child in self.stack[:-1]:
            self.remove(child)
        self.stack = [self.stack[-1]]
        self.set_transition_duration(self.transition_duration)

    def isEmpty(self):
        return len(self.stack) <= 0
