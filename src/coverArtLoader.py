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
def getCoverPath(uri):
	if not getCoverPath.cache_path:
		getCoverPath.cache_path = BaseDirectory.save_cache_path(Config.applicationID + 'coverArt')

	return getCoverPath.cache_path + uri

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

# TODO - this is wrong
# def make_square_of_size(pixbuf, size):
# 	buf_height = pixbuf.get_height()
# 	buf_width = pixbuf.get_width()
# 	if buf_width != buf_height:
# 		if buf_width > buf_height:
# 			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename=str(path), width=-1, height=height)
# 		else:
# 			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename=str(path), width=width, height=-1)
# 		pixbuf = self.cropToSquare(pixbuf)

# 	return pixbuf

class Dimensions:
	def __init__(self, width, height):
		self.width = width
		self.height = height

class PixbufCache:

	class PixbufCacheEntry:

		def __init__(self):
			self.entryLock = threading.Lock()
			self.pixbuf = None

	def __init__(self):
		self.__pixbufs_lock = threading.Lock()
		self.__pixbufs = {}
		errorImage = getErrorImage()
		self.__errorPixbuf = errorImage.get_pixbuf()

	def __fetch_pixbuf(self, uri, url=None):
		cachePath = getCoverPath(uri)
		if os.path.isfile(cachePath):
			loaded = load_pixbuf_from_file(path=cachePath)
			return self.__errorPixbuf if loaded is None else loaded
		if url:
			downloadToFile(url, cachePath)
			self.__fetch_pixbuf(uri, None)
		return self.__errorPixbuf

	def get_pixbuf(self, uri, dimensions, url):
		pixbufEntry = None
		with self.__pixbufs_lock:
			if uri not in self.__pixbufs.keys():
				self.__pixbufs[uri] = self.PixbufCacheEntry()
			pixbufEntry = self.__pixbufs[uri]

		with pixbufEntry.entryLock:
			if not pixbufEntry.pixbuf:
				pixbufEntry.pixbuf = self.__fetch_pixbuf(uri, url)
			return pixbufEntry.pixbuf # TODO scale before return

class CoverArtLoader:

	def __init__(self):
		self.imageSize = 60
		self.pixbuf_cache = PixbufCache()

	# GTK
	def getLoadingImage(self):
		return Gtk.Image.new_from_icon_name("image-loading-symbolic.symbolic", Gtk.IconSize.DIALOG)

	# def cropToSquare(self, pixbuf):
	# 	height = pixbuf.get_height()
	# 	width = pixbuf.get_width()
	# 	smallerValue = height if height < width else width
	# 	src_x = (width - smallerValue) // 2
	# 	src_y = (height - smallerValue) // 2
	# 	return pixbuf.new_subpixbuf(src_x, src_y, smallerValue, smallerValue)

	def asyncUpdateCover(self, parent, updateMe, uri, url):

		# GTK
		def updateInParent(image):
			parent.remove(updateMe)
			parent.pack_start(image, False, True, 5)
			parent.show_all()

		def updateInParent_pixbuf(newChild):

			# GTK
			def toImage():
				updateInParent(Gtk.Image.new_from_pixbuf(newChild))
			GLib.idle_add(priority=GLib.PRIORITY_LOW, function=toImage)

		# def tryReloadOrFail():
		# 	newCover = self.loadCoverFromCache(uri=uri)
		# 	if not newCover:
		# 		# GTK
		# 		def fail():
		# 			updateInParent(getErrorImage())
		# 		GLib.idle_add(priority=GLib.PRIORITY_LOW, function=fail)
		# 	else:
		# 		updateInParent_pixbuf(newCover)

		# def updateCover():
		# 	self.downloadToFile(url=url, toFile=self.getCoverPath(uri))
		# 	tryReloadOrFail()

		# def tryCacheFirst():
		# 	newCover = self.loadCoverFromCache(uri=uri)
		# 	if not newCover:
		# 		updateCover()
		# 	else:
		# 		updateInParent_pixbuf(newCover)
		def getPixbufAndUpdate():
			dim = Dimensions(60, 60)
			pixbuf = self.pixbuf_cache.get_pixbuf(uri=uri, dimensions=dim, url=url)
			updateInParent_pixbuf(pixbuf)
		thread = threading.Thread(target=getPixbufAndUpdate)
		thread.start()
