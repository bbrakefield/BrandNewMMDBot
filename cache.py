from database import *
import os
import sys
import logging
from parallel_downloader import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

current_dir = os.path.dirname(os.path.abspath(__file__))
download_cache = os.path.join(current_dir,'download_cache')

class CacheEntryResult:
    def __init__(self, exists, needs_download, location, url):
        self.exists = exists
        self.needs_download = needs_download
        self.location = location
        self.url = url


class Cache:
    def exists_in_cache(self, filename):
        abs_path = os.path.join(download_cache, filename)
        exists = os.path.isfile(abs_path)
        if not exists:
            logging.info("Doesnt exist in cache {}".format(filename))
        else:
            logging.info("Found in cache {}".format(abs_path))
        return exists

    # Only call if exists
    def get_cache_path_from_url(self, url):
        return os.path.join(download_cache, url2filename(url))

    def get_cache_path_from_filename(self, filename):
        return os.path.join(download_cache, filename)

    def get_discord_user_avatar(self, discord_user):
        try:
            user = User.select().where(User.id == discord_user.id).get()
            avatar_url = user.avatar_url

            if self.exists_in_cache(url2filename(avatar_url)):
                return CacheEntryResult(True, False, self.get_cache_path_from_url(avatar_url), avatar_url)
            else:
                return CacheEntryResult(False, True, None, avatar_url)
        except:
            pass
            return CacheEntryResult(False, False, None, None)

    def get_album_cover(self, album):
        try:
            album = LastfmAlbum.select().where(LastfmAlbum.title == album.title).get()
            cover_url = album.cover_image

            if self.exists_in_cache(url2filename(cover_url)):
                return CacheEntryResult(True, False, self.get_cache_path_from_url(cover_url), cover_url)
            else:
                return CacheEntryResult(False, True, None, cover_url)
        except:
            pass
        return CacheEntryResult(False, False, None, None)

