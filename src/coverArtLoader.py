# add xdg to flatpak
from xdg import XDG_CACHE_HOME

import requests
import gi
from gi.repository import Gtk, GdkPixbuf

from .config import Config

class CoverArtLoader:

	def __init__(self):
		pass

	def downloadToFile(self, url, toFile):
		response = requests.get(url)
		open(toFile, 'wb').write(response.content)

	def loadImage(self, path, width, height):
		pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=str(path), width=width, height=height, preserve_aspect_ratio=True)
		image = Gtk.Image.new_from_pixbuf(pixbuf)
		return image

	def getPlaylistCoverPath(self, playlistID):
		playlistCachePathDir = XDG_CACHE_HOME / Config.applicationID / 'coverArt' / 'playlists'
		playlistCachePathDir.mkdir(parents=True, exist_ok=True)
		playlistCachePath = playlistCachePathDir / playlistID
		return playlistCachePath

	def loadPlaylistCoverFromCache(self, playlistID):
		playlistCachePath = self.getPlaylistCoverPath(playlistID)
		if playlistCachePath.is_file():
			imageSize=60
			return self.loadImage(path=playlistCachePath, width=imageSize, height=imageSize)
		return None

	def loadPlaylistCoverFromDownload(self, url, playlistID):
		self.downloadToFile(url=url, toFile=self.getPlaylistCoverPath(playlistID))
		return self.loadPlaylistCoverFromCache(playlistID)

	def loadPlaylistCover(self, playlistID, url):
		cover = self.loadPlaylistCoverFromCache(playlistID)
		if cover:
			return cover
		return self.loadPlaylistCoverFromDownload(playlistID=playlistID, url=url)
