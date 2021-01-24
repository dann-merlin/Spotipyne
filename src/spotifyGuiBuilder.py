# spotifyGuiBuilder.py
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
import time
import random

from functools import reduce

from gi.repository import Gtk, GLib, Pango

from .coverArtLoader import Dimensions
from .spotify import Spotify as sp

# TODO maybe just remove the non genericRows


class GenericSpotifyRow(Gtk.ListBoxRow):

    def __init__(self, uri, **kwargs):
        super().__init__(**kwargs)
        self.uri = uri

    def get_uri(self):
        return self.uri


class AlbumRow(GenericSpotifyRow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TrackRow(GenericSpotifyRow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ArtistRow(GenericSpotifyRow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class EpisodeRow(GenericSpotifyRow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ShowRow(GenericSpotifyRow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class PlaylistRow(GenericSpotifyRow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SpotifyGuiBuilder:

    def __init__(self, cover_art_loader):
        self.cover_art_loader = cover_art_loader
        self.current_playlist_iD = ''

    def get_playlists(self):
        all_playlists = []
        offset = 0
        page_size = 50
        keep_going = True
        while keep_going:
            playlists_response = sp.get().current_user_playlists(limit=page_size, offset=offset)
            keep_going = playlists_response['next'] is not None
            offset += page_size
            all_playlists += playlists_response['items']
        return all_playlists

    def get_saved_tracks(self):
        all_tracks = []
        offset = 0
        page_size = 50
        keep_going = True
        while keep_going:
            tracks_response = sp.get().current_user_saved_tracks(
                    limit=page_size,
                    offset=offset
            )
            keep_going = tracks_response['next'] is not None
            offset += page_size
            all_tracks += tracks_response['items']
        return [track_response['track'] for track_response in all_tracks]

    def get_playlist_tracks(self, playlist_id):
        all_tracks = []
        offset = 0
        page_size = 100
        keep_going = True
        while keep_going:
            tracks_response = sp.get().playlist_tracks(
                playlist_id=playlist_id,
                fields='items(track(uri,id,name,artists(name),album(id,uri,images))),next',
                limit=page_size, offset=offset)
            keep_going = tracks_response['next'] is not None
            offset += page_size
            all_tracks += tracks_response['items']
        return [track_response['track'] for track_response in all_tracks]

    def load_generic_list(self,
                          generic_list,
                          raw_data,
                          build_entry_function,
                          stop_event):
        def load_chunk(chunk):
            for raw_data_for_entry in chunk:
                entry = build_entry_function(raw_data_for_entry)
                generic_list.insert(entry, -1)
            generic_list.show_all()

        def chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i+n]

        def set_listbox_attributes(listbox):
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        GLib.idle_add(set_listbox_attributes, generic_list)

        for chunk in chunks(raw_data, 10):
            GLib.idle_add(load_chunk, chunk, priority=GLib.PRIORITY_LOW)
            time.sleep(0.5)
            if stop_event and stop_event.is_set():
                return


    def load_playlist_tracks_list(self,
                                  playlist_tracks_list,
                                  playlist_id,
                                  stop_event):
        playlist_tracks = self.get_playlist_tracks(playlist_id)
        self.load_generic_list(
            playlist_tracks_list,
            playlist_tracks,
            self.build_track_entry,
            stop_event
        )

    def build_artist_page(self, artist_uri):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.page_stop_event = threading.Event()
        vbox.pack_start(Gtk.Label("Artist " + artist_uri), False, True, 0)
        vbox.show_all()
        return vbox

    def build_album_page(self, album_uri):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.page_stop_event = threading.Event()
        vbox.pack_start(Gtk.Label("Album " + album_uri), False, True, 0)
        vbox.show_all()
        return vbox

    def build_saved_tracks_page(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.page_stop_event = threading.Event()
        tracks_list = Gtk.ListBox()
        image = Gtk.Image.new_from_icon_name(
            "emblem-favorite-symbolic.symbolic", Gtk.IconSize.DIALOG)
        label = Gtk.Label("Liked Songs", xalign=0)
        vbox.pack_start(image, False, True, 0)
        vbox.pack_start(label, False, True, 0)
        vbox.pack_start(tracks_list, False, True, 0)

        def on_saved_tracks_list_row_activated(listbox, row):
            pass
            # def helper():
            # 	sp.start_playback(offset={"uri": row.getUri()})
            # sp_thread = threading.Thread(daemon=True, target=helper)
            # sp_thread.start()

        tracks_list.connect('row-activated', on_saved_tracks_list_row_activated)

        def load_saved_tracks_list():
            saved_tracks = self.get_saved_tracks()
            self.load_generic_list(
                tracks_list,
                saved_tracks,
                self.build_track_entry,
                vbox.page_stop_event
            )
            pass

        threading.Thread(daemon=True, target=load_saved_tracks_list).start()

        vbox.show_all()
        return vbox

    def build_playlist_page(self, playlist_uri):
        playlist_id = playlist_uri.split(':')[-1]
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.page_stop_event = threading.Event()
        playlist_image = self.cover_art_loader.get_loading_image()
        label = Gtk.Label(xalign=0.5)
        play_button = Gtk.Button("play random", halign=Gtk.Align.CENTER)
        playlist_tracks_list = Gtk.ListBox()
        vbox.pack_start(playlist_image, False, True, 0)
        vbox.pack_start(label, False, True, 0)
        vbox.pack_start(play_button, False, False, 0)
        vbox.pack_start(playlist_tracks_list, False, True, 0)

        def play_random(_button):
            try:
                random_row = random.choice(playlist_tracks_list.get_children())
            except IndexError:
                return
            uri = random_row.get_uri()
            def helper():
                sp.start_playback(
                    context_uri=playlist_uri, offset={
                        "uri": uri})
            threading.Thread(daemon=True, target=helper).start()

        play_button.connect("clicked", play_random)

        def on_playlist_tracks_list_row_activated(listbox, row):
            uri = row.get_uri()
            def helper():
                sp.start_playback(
                    context_uri=playlist_uri, offset={
                        "uri": uri})
            sp_thread = threading.Thread(daemon=True, target=helper)
            sp_thread.start()

        playlist_tracks_list.connect(
            'row-activated', on_playlist_tracks_list_row_activated)

        def load_playlist_page():
            def load_label_and_image():
                playlist_info_response = sp.get().playlist(
                    playlist_id, fields='name,images,followers(total),owner(display_name)')
                playlist_cover_size_big = 128
                images = playlist_info_response['images']
                self.cover_art_loader.async_update_cover(
                    playlist_image, playlist_uri, images, dimensions=Dimensions(
                        playlist_cover_size_big, playlist_cover_size_big, True))

                def build_playlist_label():
                    markup_string = '<b>' + GLib.markup_escape_text(
                        playlist_info_response['name']) + '</b>'
                    markup_string += '\n'
                    markup_string += 'by ' + GLib.markup_escape_text(
                        playlist_info_response['owner']['display_name'])
                    followers_total = playlist_info_response['followers'][
                        'total']
                    if followers_total > 1:
                        markup_string += ' - ' + str(
                            followers_total) + ' followers'
                    label.set_markup(markup_string)
                    label.show_all()

                GLib.idle_add(build_playlist_label, priority=GLib.PRIORITY_LOW)

            thread_label = threading.Thread(
                daemon=True, target=load_label_and_image)
            thread_label.start()
            thread_tracks = threading.Thread(
                daemon=True, target=self.load_playlist_tracks_list, args=(
                    playlist_tracks_list, playlist_id, vbox.page_stop_event))
            thread_tracks.start()
        load_playlist_page()
        vbox.show_all()
        return vbox

    def build_show_page(self, show_uri):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.page_stop_event = threading.Event()
        vbox.pack_start(Gtk.Label("Show " + show_uri), False, True, 0)
        vbox.show_all()
        return vbox

    def __build_generic_entry(self, entry, image_responses,
                            uri, label_text, desired_cover_size=60):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        cover_art = self.cover_art_loader.get_loading_image()
        hbox.pack_start(cover_art, False, True, 5)
        self.cover_art_loader.async_update_cover(
            cover_art, urls=image_responses, uri=uri, dimensions=Dimensions(
                desired_cover_size, desired_cover_size, True))
        label = Gtk.Label(xalign=0)
        label.set_max_width_chars(32)
        label.set_line_wrap(True)
        label.set_lines(2)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_markup(label_text)
        hbox.pack_end(label, True, True, 0)
        entry.add(hbox)
        return entry

    def build_track_entry(self, track):
        album_uri = track['album']['uri']
        row = TrackRow(uri=track['uri'])
        image_responses = track['album']['images']

        track_name_string = track['name']
        artist_string = reduce(
            lambda a, b: {'name': a['name'] + ", " + b['name']},
            track['artists'][1:],
            track['artists'][0])['name']
        track_label_string = '<b>' + GLib.markup_escape_text(
            track_name_string) + '</b>' + '\n' + GLib.markup_escape_text(artist_string)
        return self.__build_generic_entry(
            row, image_responses, album_uri, track_label_string)

    def build_artist_entry(self, artist_response):
        artist_uri = artist_response['uri']
        row = ArtistRow(uri=artist_uri)
        image_responses = artist_response['images']
        label_markup = '<b>' + GLib.markup_escape_text(
            artist_response['name']) + '</b>' + '\n' + GLib.markup_escape_text(
            str(artist_response['followers']['total']) + ' followers')
        return self.__build_generic_entry(
            row, image_responses, artist_uri, label_markup)

    def build_episode_entry(self, episode_response):
        if episode_response is None:
            return self.__build_generic_entry(
                EpisodeRow(uri='episode::Response is None'),
                None, "No Uri. Episode is None", "No Uri. Episode is None")
        episode_uri = episode_response['uri']
        row = EpisodeRow(uri=episode_uri)
        image_responses = episode_response['images']
        label_markup = '<b>' + GLib.markup_escape_text(
            episode_response['name']) + '</b>' + '\n' + GLib.markup_escape_text(
            episode_response['description'])
        return self.__build_generic_entry(
            row, image_responses, episode_uri, label_markup)

    def build_show_entry(self, show_response):
        show_uri = show_response['uri']
        row = ShowRow(uri=show_uri)
        image_responses = show_response['images']
        label_markup = '<b>' + GLib.markup_escape_text(
            show_response['name']) + '</b>' + '\n' + GLib.markup_escape_text(show_response['publisher'])
        return self.__build_generic_entry(
            row, image_responses, show_uri, label_markup)

    def build_album_entry(self, album_response):
        album_uri = album_response['uri']
        row = AlbumRow(uri=album_uri)
        image_responses = album_response['images']
        artist_string = reduce(
            lambda a, b: {'name': a['name'] + ", " + b['name']},
            album_response['artists'][1:],
            album_response['artists'][0])['name']
        label_markup = '<b>' + GLib.markup_escape_text(
            album_response['name']) + '</b>' + '\n' + GLib.markup_escape_text(artist_string)
        return self.__build_generic_entry(
            row, image_responses, album_uri, label_markup)

    def build_playlist_entry(self, playlist_response):
        playlist_uri = playlist_response['uri']
        row = PlaylistRow(uri=playlist_uri)
        image_responses = playlist_response['images']
        return self.__build_generic_entry(
            row, image_responses, playlist_uri, GLib.markup_escape_text(
                playlist_response['name']))

    def build_search_results(self, search_result_box,
                           search_response, set_search_overlay_function):
        def _search_result_helper(
                search_type, name, build_entry_function, activation_handler):
            response = search_response[search_type]
            result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            result_title = Gtk.Label(xalign=0)
            result_title.set_markup('<b>' + name + '</b>')
            result_box.pack_start(result_title, False, True, 0)
            if len(response['items']) != 0:
                results_list = Gtk.ListBox()
                results_list.connect("row-activated", activation_handler)
                list_loader_thread = threading.Thread(
                    daemon=True, target=self.load_generic_list, args=(
                        results_list, response['items'], build_entry_function, None))
                list_loader_thread.start()
                result_box.pack_start(results_list, False, True, 0)
                search_result_box.pack_start(result_box, False, True, 0)
            else:
                not_found_label = Gtk.Label(xalign=0)
                not_found_label.set_markup(
                    '_could not find any ' + search_type +
                    ' matching your search query...')
                result_box.pack_start(not_found_label, False, True, 0)
                search_result_box.pack_end(result_box, False, True, 0)

        search_queries = [{'type': 'tracks',
                          'name': 'Tracks',
                          'build_entry_function': self.build_track_entry,
                          'activation_handler': lambda _,
                          entry: sp.start_playback(uris=[entry.get_uri()])},
                         {'type': 'artists',
                          'name': 'Artists',
                          'build_entry_function': self.build_artist_entry,
                          'activation_handler': lambda _,
                          entry: set_search_overlay_function(self.build_artist_page(entry.get_uri()))},
                         {'type': 'albums',
                          'name': 'Albums',
                          'build_entry_function': self.build_album_entry,
                          'activation_handler': lambda _,
                          entry: set_search_overlay_function(self.build_album_page(entry.get_uri()))},
                         {'type': 'playlists',
                          'name': 'Playlists',
                          'build_entry_function': self.build_playlist_entry,
                          'activation_handler': lambda _,
                          entry: set_search_overlay_function(self.build_playlist_page(entry.get_uri()))},
                         {'type': 'shows',
                          'name': 'Shows',
                          'build_entry_function': self.build_show_entry,
                          'activation_handler': lambda _,
                          entry: set_search_overlay_function(self.build_show_page(entry.get_uri()))},
                         {'type': 'episodes',
                          'name': 'Episodes',
                          'build_entry_function': self.build_episode_entry,
                          'activation_handler': lambda _,
                          entry: sp.start_playback(uris=[entry.get_uri()])}]
        for search_query in search_queries:
            _search_result_helper(
                search_query['type'],
                search_query['name'],
                search_query['build_entry_function'],
                search_query['activation_handler'])
        search_result_box.show_all()

    # TODO pushWidgetFunction to be used for example when clicking on the
    # artist inside the playlistpage
    def load_library(self, listbox, set_widget_function, _push_widget_function):
        listbox.set_placeholder(Gtk.Label("Loading library..."))

        def _load_library_helper():
            def load_saved_tracks_entry():
                def build_saved_tracks_entry():
                    fake_playlist_response = {
                            'uri': 'Saved Tracks',
                            'name': 'Liked Songs',
                            'images': None
                    }
                    return self.build_playlist_entry(fake_playlist_response)

                saved_tracks_entry = build_saved_tracks_entry()
                listbox.insert(saved_tracks_entry, 0)

            def on_row_activated(listbox, entry):
                if entry.get_uri() == 'Saved Tracks':
                    widget = self.build_saved_tracks_page()  # TODO implement that function
                else:
                    widget = self.build_playlist_page(entry.get_uri())
                set_widget_function(widget)

            listbox.connect("row-activated", on_row_activated)
            GLib.idle_add(load_saved_tracks_entry)
            playlists = self.get_playlists()
            self.load_generic_list(listbox,
                                   playlists,
                                   self.build_playlist_entry,
                                   None)

        threading.Thread(daemon=True, target=_load_library_helper).start()

    def async_load_playlists(self, playlists_list):
        # TODO use insert
        def add_playlist_entry(playlist):
            playlist_uri = playlist['uri']
            row = PlaylistRow(uri=playlist_uri)
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            image_responses = playlist['images']

            desired_size = 60

            cover_art = self.cover_art_loader.get_loading_image()
            hbox.pack_start(cover_art, False, True, 5)
            self.cover_art_loader.async_update_cover(
                cover_art, urls=image_responses, uri=playlist_uri,
                dimensions=Dimensions(desired_size, desired_size, True))
            name_label = Gtk.Label(playlist['name'], xalign=0)
            name_label.set_max_width_chars(32)
            name_label.set_line_wrap(True)
            name_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            hbox.pack_end(name_label, True, True, 0)
            row.add(hbox)
            playlists_list.add(row)
            playlists_list.show_all()

        def load_playlists():
            all_playlists = []
            offset = 0
            page_size = 50
            keep_going = True
            while keep_going:
                playlists_response = sp.get().current_user_playlists(limit=page_size, offset=offset)
                keep_going = playlists_response['next'] is not None
                offset += page_size
                all_playlists += playlists_response['items']

            def add_all_playlist_entries():
                for playlist in all_playlists:
                    GLib.idle_add(
                        add_playlist_entry,
                        playlist,
                        priority=GLib.PRIORITY_LOW)

            add_all_playlist_entries()

        thread = threading.Thread(target=load_playlists)
        thread.start()
