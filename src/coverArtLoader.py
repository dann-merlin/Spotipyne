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

# add xdg to flatpak
import threading
import os
from xdg import XDG_CACHE_HOME

import requests
import gi
from gi.repository import Gtk, GdkPixbuf, GLib

from .config import Config

class CoverArtLoader:

	def __init__(self):
		self.imageSize = 60
		self.icon_theme = Gtk.IconTheme.get_default()


	def getLoadingImage(self):
		return Gtk.Image.new_from_icon_name("image-loading-symbolic.symbolic", Gtk.IconSize.DIALOG)

	def getErrorImage(self):
		return Gtk.Image.new_from_icon_name("image-missing-symbolic.symbolic", Gtk.IconSize.DIALOG)

	def downloadToFile(self, url, toFile):
		response = requests.get(url)
		open(toFile, 'wb').write(response.content)

	def cropToSquare(self, pixbuf):
		height = pixbuf.get_height()
		width = pixbuf.get_width()
		smallerValue = height if height < width else width
		src_x = (width - smallerValue) // 2
		src_y = (height - smallerValue) // 2
		return pixbuf.new_subpixbuf(src_x, src_y, smallerValue, smallerValue)

	def loadImage(self, path, width, height):
		try:
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename=str(path), width=width, height=height)
		except GLib.Error:
			os.remove(path)
			return self.getErrorImage()

		buf_height = pixbuf.get_height()
		buf_width = pixbuf.get_width()
		if buf_width != buf_height:
			if buf_width > buf_height:
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename=str(path), width=-1, height=height)
			else:
				pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename=str(path), width=width, height=-1)
			pixbuf = self.cropToSquare(pixbuf)

		image = Gtk.Image.new_from_pixbuf(pixbuf)
		return image

	def getCoverPath(self, coverType, ID):
		possibleTypes = [ 'playlist', 'album' ]
		if coverType not in possibleTypes:
			coverType = 'ERRORTypeDoesNotExist'
		playlistCachePathDir = XDG_CACHE_HOME / Config.applicationID / 'coverArt' / coverType
		playlistCachePathDir.mkdir(parents=True, exist_ok=True)
		playlistCachePath = playlistCachePathDir / ID
		return playlistCachePath

	def loadCoverFromCache(self, coverType, ID):
		cachePath = self.getCoverPath(coverType, ID)
		if cachePath.is_file():
			return self.loadImage(path=cachePath, width=self.imageSize, height=self.imageSize)
		return None

	# def loadCoverFromDownload(self, url, coverType, ID):
	# 	self.downloadToFile(url=url, toFile=self.getCoverPath(coverType, ID))
	# 	return self.loadCoverFromCache(coverType, ID)

	def asyncUpdateCover(self, coverType, parent, updateMe, ID, url):
		def updateInParent(newChild):
			parent.remove(updateMe)
			parent.pack_start(newChild, False, True, 5)
			parent.show_all()

		def tryReloadOrFail():
			newCover = self.loadCoverFromCache(coverType=coverType, ID=ID)
			if not newCover:
				newCover = self.getErrorImage()
			updateInParent(newCover)

		def updateCover():
			self.downloadToFile(url=url, toFile=self.getCoverPath(coverType, ID))
			GLib.idle_add(tryReloadOrFail)

		newCover = self.loadCoverFromCache(coverType=coverType, ID=ID)
		if not newCover:
			thread = threading.Thread(target=updateCover)
			thread.start()
		else:
			updateInParent(newCover)

	def asyncUpdatePlaylistCover(self, parent, updateMe, ID, url):
		self.asyncUpdateCover('playlist', parent, updateMe, ID, url)

	def asyncUpdateAlbumCover(self, parent, updateMe, ID, url):
		self.asyncUpdateCover('album', parent, updateMe, ID, url)
