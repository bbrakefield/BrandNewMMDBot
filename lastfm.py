import pylast
import time
import os
from database import *
from lastfm_spoofer import *

API_KEY = "1c15b9ea24af56c25eac1d40b24cf6b5"
API_SECRET = "2fc65d3ac585f3738b8c56a8b6013d6f"

# Renamed because name collision
class MMDTrack:
    def __init__(self,artist, album, track):
        self.artist = artist
        self.album = album
        self.track = track

class LastFmWrapper:
    def __init__(self):
        self.network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
        self.utility = LastfmUtility(self)

    def get_user(self,user_name):
        lastfm_user = self.network.get_user("arkenthera")

        library = lastfm_user.get_library()
        return library.get_user()

    def get_user_from_db(self, user_name):
        try:
            return LastfmUser.select().where(LastfmUser.name == user_name).get()
        except:
            return None

    def get_now_playing(self,user_name):
        try:
            np = self.get_user(user_name).get_now_playing()
            return np
        except:
            return None

    def get_user_artists_from_db(self, user_name):
        lastfm_user = self.get_user_from_db(user_name)
        if lastfm_user == None:
            return None

        user_artists = LastfmUserArtist.select().where(LastfmUserArtist.user == lastfm_user).get()

        if len(user_artists) > 0:
            return user_artists
        else:
            return None

    def get_user_artists(self, user_name, limit=1000):
        try:
            return self.get_user(user_name).get_top_artists(limit=limit)
        except:
            return None


    def get_user_albums(self, user_name, limit=1000):
        try:
            return self.get_user(user_name).get_top_albums(limit=limit)
        except:
            return None

    def get_recent_trakcs(self, user_name, limit=10):
        try:
            return self.get_user(user_name).get_recent_tracks(limit=limit)
        except:
            return None

    def get_album_from_artist(self, artist, title):
        try:
            return pylast.Album(artist, title, self.network)
        except:
            return None

