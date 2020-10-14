# coverArtLoader.py
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
import gi
from gi.repository import Gtk, GdkPixbuf, GLib

from .config import Config

def static_vars(**kwargs):
	def decorate(func):
		for k in kwargs:
			setattr(func, k, kwargs[k])
		return func
	return decorate


@static_vars(cache_path=None)
def getCoverPath(uri, dim):
	if not getCoverPath.cache_path:
		getCoverPath.cache_path = BaseDirectory.save_cache_path(Config.applicationID + '/coverArt/')

	return getCoverPath.cache_path + uri + ":" + str(dim)

# GTK
@static_vars(image=None)
def getErrorImage():
	if not getErrorImage.image:
		getErrorImage.image = Gtk.Image.new_from_icon_name("image-missing-symbolic.symbolic", Gtk.IconSize.DIALOG)
	return getErrorImage.image

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

def downloadToFile(url, toFile):
	response = requests.get(url)
	open(toFile, 'wb').write(response.content)

def cropToSquare(pixbuf):
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

	def __init__(self, width, height, be_square=False):
		self.width = width
		self.height = height
		if be_square:
			self.height = self.width
		self.be_square = be_square

	def __str__(self):
		return str(self.width) + "x" + str(self.height) + "x" + str(self.be_square)

def scaleToDimension(pixbuf, dim):
	cropped = pixbuf
	if dim.be_square:
		cropped = cropToSquare(pixbuf)
	return cropped.scale_simple(dim.width, dim.height, GdkPixbuf.InterpType.BILINEAR)

class PixbufCache:

	class PixbufCacheEntry:

		def __init__(self):
			self.entryLock = threading.Lock()
			self.pixbuf_orig = None
			self.pixbufs_scaled = {}
			self.used_by = 0
			self.error = False

		def __get_orig(self, uri, dim, url=None):
			cachePath = getCoverPath(uri, dim)
			if os.path.isfile(cachePath):
				loaded = load_pixbuf_from_file(path=cachePath)
				if loaded:
					self.pixbufs_scaled[Dimensions(loaded.get_width(), loaded.get_height(), True)] = loaded
					self.pixbufs_scaled[Dimensions(loaded.get_width(), loaded.get_height(), False)] = loaded
					return loaded
			if url:
				downloadToFile(url, cachePath)
				return self.__get_orig(uri, dim, None)
			return None

		def get_scaled(self, uri, dim, url):
			self.used_by += 1

			if self.error:
				return None

			if dim in self.pixbufs_scaled.keys():
				return self.pixbufs_scaled[dim]

			if not self.pixbuf_orig:
				self.pixbuf_orig = self.__get_orig(uri, dim, url)
				if not self.pixbuf_orig:
					self.error = True
					return None

			if dim not in self.pixbufs_scaled.keys():
				self.pixbufs_scaled[dim] = scaleToDimension(self.pixbuf_orig, dim)
			return self.pixbufs_scaled[dim]

		def dec_used(self):
			self.used_by -= 1

			if self.used_by <= 0:
				self.pixbuf_orig = None
				self.pixbufs_scaled = {}

	def __init__(self):
		self.__pixbufs_lock = threading.Lock()
		self.__pixbufs = {}

	def get_pixbuf(self, uri, dimensions, url):
		pixbufEntryPair = None
		with self.__pixbufs_lock:
			if uri not in self.__pixbufs.keys():
				self.__pixbufs[uri] = (self.PixbufCacheEntry(), threading.Lock())
			pixbufEntryPair = self.__pixbufs[uri]

		with pixbufEntryPair[1]:
			return pixbufEntryPair[0].get_scaled(uri, dimensions, url)

	def forget_pixbuf(self, uri):
		with self.__pixbufs_lock:
			if uri not in self.__pixbufs.keys():
				return
			self.__pixbufs[uri] = (self.PixbufCacheEntry(), self.__pixbufs[uri][1])

class CoverArtLoader:

	def __init__(self):
		self.imageSize = 60
		self.pixbuf_cache = PixbufCache()

	# GTK
	def getLoadingImage(self):
		return Gtk.Image.new_from_icon_name("image-loading-symbolic.symbolic", Gtk.IconSize.DIALOG)

	def asyncUpdateCover(self, updateMe, uri, url, dimensions=Dimensions(16, 16, True)):

		def updateInParent_pixbuf(newChild):
			# GTK
			def toImage():
				updateMe.set_from_pixbuf(newChild)
			GLib.idle_add(priority=GLib.PRIORITY_LOW, function=toImage)

		def updateInParent_error():
			# GTK
			def errorImage():
				updateMe.set_from_icon_name("image-missing-symbolic.symbolic", Gtk.IconSize.DIALOG)
			GLib.idle_add(priority=GLib.PRIORITY_LOW, function=errorImage)

		def getPixbufAndUpdate():
			pixbuf = self.pixbuf_cache.get_pixbuf(uri=uri, dimensions=dimensions, url=url)
			if pixbuf:
				updateInParent_pixbuf(pixbuf)
			else:
				updateInParent_error()

		thread = threading.Thread(target=getPixbufAndUpdate)
		thread.start()

	def forget_image(self, uri):
		self.pixbuf_cache.forget_pixbuf(uri)
