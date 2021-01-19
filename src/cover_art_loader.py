# cover_art_loader.py
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
import os
from xdg import BaseDirectory

import requests
from gi.repository import Gtk, GdkPixbuf, GLib

from .config import Config


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


@static_vars(cache_path=None)
def get_cover_path(uri, dim):
    if not get_cover_path.cache_path:
        get_cover_path.cache_path = BaseDirectory.save_cache_path(
            Config.applicationID + '/coverArt/'
        )
    return get_cover_path.cache_path + uri + ":" + str(dim)


# GTK
@static_vars(image=None)
def get_error_image():
    if not get_error_image.image:
        get_error_image.image = Gtk.Image.new_from_icon_name(
            "image-missing-symbolic.symbolic",
            Gtk.IconSize.DIALOG
        )
    return get_error_image.image


def load_pixbuf_from_file(path):
    try:
        return GdkPixbuf.Pixbuf.new_from_file(filename=path)
    except GLib.Error as gliberr:
        print(gliberr)
        try:
            os.remove(path)
        except Exception as e:
            print(e)
        return None


def get_desired_image_for_size(desired_size, image_responses):
    image_responses = sorted(image_responses, key=lambda img: img['width'])
    for image in image_responses:
        if image['width'] is None or image['height'] is None:
            continue
        smaller = image['height'] \
            if image['width'] > image['height'] \
            else image['width']
        if smaller >= desired_size:
            return image['url'], Dimensions(
                image['width'],
                image['height'],
                image['width'] == image['height']
            )
    try:
        if image_responses[-1]:
            image = image_responses[-1]
            return image['url'], Dimensions(
                image['width'],
                image['height'],
                image['width'] == image['height']
            )
    except IndexError:
        pass
    return None, Dimensions(desired_size, desired_size, True)


def download_to_file(url, toFile):
    response = requests.get(url)
    open(toFile, 'wb').write(response.content)


def rename_file_if_dimensions_none(uri, cache_path):
    loaded = load_pixbuf_from_file(path=cache_path)
    w = loaded.get_width()
    h = loaded.get_height()
    read_dim = Dimensions(w, h, w == h)
    new_filename = get_cover_path(uri, read_dim)
    os.rename(cache_path, new_filename)
    return read_dim


def crop_to_square(pixbuf):
    height = pixbuf.get_height()
    width = pixbuf.get_width()
    smallerValue = height if height < width else width
    src_x = (width - smallerValue) // 2
    src_y = (height - smallerValue) // 2
    return pixbuf.new_subpixbuf(src_x, src_y, smallerValue, smallerValue)


class Dimensions:

    def __key(self):
        return (self.width, self.height, self.be_square)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, Dimensions):
            return self.__key() == other.__key()
        return NotImplemented

    def __gt__(self, other):
        if self.width is None or self.height is None:
            return True
        if other.width is None or other.height is None:
            return False
        return self.width > other.width and self.height > other.height

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __lt__(self, other):
        if self.width is None or self.height is None:
            return False
        if other.width is None or other.height is None:
            return True
        return self.width < other.width and self.height < other.height

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __init__(self, width, height, be_square=False):
        self.width = width
        self.height = height
        if be_square:
            self.height = self.width
        self.be_square = be_square

    def __str__(self):
        return str(self.width) + "x" + str(self.height) + "x" + str(self.be_square)


def scale_to_dimension(pixbuf, dim):
    cropped = pixbuf
    if dim.be_square:
        cropped = crop_to_square(pixbuf)
    return cropped.scale_simple(
        dim.width,
        dim.height,
        GdkPixbuf.InterpType.BILINEAR
    )


class PixbufCache:

    class PixbufCacheEntry:

        def __init__(self):
            self.pixbufs_scaled = {}
            self.used_by = 0
            self.error = False

        def __get_image(self, uri, dim, url=None):
            cache_path = get_cover_path(uri, dim)
            if os.path.isfile(cache_path):
                loaded = load_pixbuf_from_file(path=cache_path)
                if loaded:
                    return loaded
            if url:
                download_to_file(url, cache_path)
                if dim.height is None or dim.width is None:
                    dim = rename_file_if_dimensions_none(uri, cache_path)
                return self.__get_image(uri, dim, None)
            return None

        def get_scaled(self, uri, dim, urls):
            self.used_by += 1

            if self.error:
                return None

            if dim in self.pixbufs_scaled.keys():
                return self.pixbufs_scaled[dim]

            big_enough_dims = [scale for scale in self.pixbufs_scaled.keys() if scale <= dim]
            if len(big_enough_dims) > 0:
                self.pixbufs_scaled[dim] = scale_to_dimension(
                    self.pixbufs_scaled[min(big_enough_dims)],
                    dim
                )
            else:
                image_url, desired_dim = get_desired_image_for_size(
                    dim.height,
                    urls
                )
                bigger_img = self.__get_image(uri, desired_dim, image_url)
                self.pixbufs_scaled[desired_dim] = bigger_img
                self.pixbufs_scaled[dim] = scale_to_dimension(bigger_img, dim)

            return self.pixbufs_scaled[dim]

        def dec_used(self):
            self.used_by -= 1

            if self.used_by <= 0:
                self.pixbufs_scaled = {}

    def __init__(self):
        self.__pixbufs_lock = threading.Lock()
        self.__pixbufs = {}

    def get_pixbuf(self, uri, dimensions, urls):
        pixbuf_entry_pair = None
        with self.__pixbufs_lock:
            if uri not in self.__pixbufs.keys():
                self.__pixbufs[uri] = (
                    self.PixbufCacheEntry(),
                    threading.Lock()
                )
            pixbuf_entry_pair = self.__pixbufs[uri]

        with pixbuf_entry_pair[1]:
            return pixbuf_entry_pair[0].get_scaled(uri, dimensions, urls)

    def forget_pixbuf(self, uri):
        with self.__pixbufs_lock:
            if uri not in self.__pixbufs.keys():
                return
            self.__pixbufs[uri] = (
                self.PixbufCacheEntry(),
                self.__pixbufs[uri][1]
            )


class CoverArtLoader:

    def __init__(self):
        self.imageSize = 60
        self.pixbuf_cache = PixbufCache()

    # GTK
    def get_loading_image(self):
        return Gtk.Image.new_from_icon_name(
            "image-loading-symbolic.symbolic", Gtk.IconSize.DIALOG)

    def async_update_cover(self, update_me, uri, urls,
                           dimensions=Dimensions(16, 16, True)):

        def update_in_parent_pixbuf(new_child):
            # GTK
            def to_image():
                update_me.set_from_pixbuf(new_child)
            GLib.idle_add(priority=GLib.PRIORITY_LOW, function=to_image)

        def update_in_parent_error():
            # GTK
            def error_image():
                update_me.set_from_icon_name(
                    "image-missing-symbolic.symbolic", Gtk.IconSize.DIALOG)
            GLib.idle_add(priority=GLib.PRIORITY_LOW, function=error_image)

        def get_pixbuf_and_update():
            pixbuf = self.pixbuf_cache.get_pixbuf(
                uri=uri, dimensions=dimensions, urls=urls)
            if pixbuf:
                update_in_parent_pixbuf(pixbuf)
            else:
                update_in_parent_error()

        thread = threading.Thread(target=get_pixbuf_and_update)
        thread.start()

    def forget_image(self, uri):
        self.pixbuf_cache.forget_pixbuf(uri)
