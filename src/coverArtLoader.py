# add xdg to flatpak
from xdg import XDG_CACHE_HOME

import requests
import gi
from gi.repository import Gtk, GdkPixbuf

from .config import Config

class CoverArtLoader:

	# def __init__(self):
	# 	pass

	def downloadToFile(self, url, toFile):
		response = requests.get(url)
		open(toFile, 'wb').write(response.content)

	def loadImage(self, path, width, height):
		pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=str(path), width=width, height=height, preserve_aspect_ratio=True)
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
			imageSize=60
			return self.loadImage(path=cachePath, width=imageSize, height=imageSize)
		return None

	def loadCoverFromDownload(self, url, coverType, ID):
		self.downloadToFile(url=url, toFile=self.getCoverPath(coverType, ID))
		return self.loadCoverFromCache(coverType, ID)

	def loadCover(self, coverType, ID, url):
		cover = self.loadCoverFromCache(coverType, ID)
		if cover:
			return cover
		return self.loadCoverFromDownload(coverType=coverType, ID=ID, url=url)

	def loadPlaylistCover(self, ID, url):
		return self.loadCover('playlist', ID, url)

	def loadAlbumCover(self, ID, url):
		return self.loadCover('album', ID, url)
