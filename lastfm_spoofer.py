import logging
import inspect
import sys
from peewee import *
from database import *
import pylast
import datetime
import logging

API_KEY = "1c15b9ea24af56c25eac1d40b24cf6b5"
API_SECRET = "2fc65d3ac585f3738b8c56a8b6013d6f"

# Options
# Are we creating the db from scratch or updating records?
IsUpdating = False

class LastfmUtility:
    def __init__(self, lastfm):
        self.lastfm = lastfm

    def save_artist_info(self, user_name,lastfm_artist):
        lastfm_user = self.lastfm.get_user(user_name)


        # Find in database
        artist_in_db = None
        try:
            artist_in_db = LastfmArtist.select().where(LastfmArtist.name == lastfm_artist.name).get()
        except:
            pass
        if artist_in_db == None:
            artist = self.pylast_artist_to_db_artist(lastfm_artist)

            try:
                artist_in_db = LastfmArtist.create(name = artist.name , play_count = artist.play_count, listener_count = artist.listener_count, cover_image = artist.cover_image, bio = artist.bio, url = artist.url)
                log_artist_str = "Adding LastfmArtist \n"
                log_artist_str += "Name {}\n Plays: {}\n Listeners: {} \n CoverImage: {}\n Bio: {}\n Url: {} \n".format(artist.name, artist.play_count, artist.listener_count, artist.cover_image, artist.bio, artist.url)
                logging.info(log_artist_str)
            except Exception as ex:
                print("Error creating LastfmArtist")
                print(ex)
        else:
            logging.info("Skipping artist {}, it already exists.".format(artist_in_db))

        if not artist_in_db == None:
            # Search this LastfmUserArtist
            user_artist_in_db = None
            try:
                user_artist_in_db = LastfmUserArtist.select().where(LastfmUserArtist.artist == artist_in_db, LastfmUserArtist.user == lastfm_user).get()
            except:
                pass
            if user_artist_in_db == None:
                try:
                    LastfmUserArtist.create(artist = artist_in_db, user = lastfm_user, play_count = artist.play_count)
                    log_userartist_str = "Adding LastfmUserArtist \n"
                    log_userartist_str += "Artist: {} \n Plays: {}".format(artist_in_db.name, artist.play_count)
                    logging.info(log_userartist_str)
                except Exception as ex:
                    print("Error creating LastfmUserArtist")
                    print(ex)

            else:
                logging.info("Skipping user artist {} because it already exists for {}".format(user_artist_in_db.artist.name, lastfm_user.name))
        return artist_in_db




    #
    #
    def save_user_info(self,username):
        # user_id = self.lastfm_user.get_id() doesnt always return an ID ??
        lastfm_user = self.lastfm.get_user(username)
        user_name = username
        user_real_name = username
        user_image = lastfm_user.get_image()
        user_playcount = lastfm_user.get_playcount()
        user_age = lastfm_user.get_age()
        user_gender = lastfm_user.get_gender()
        loved_count = 0
        try:
            loved_tracks = lastfm_user.get_loved_tracks(limit=1000)
            loved_count = len(loved_tracks)
        except:
            pass
        
        user_registered = lastfm_user.get_unixtime_registered()

        if not user_registered == None:
            user_registered = datetime.datetime.fromtimestamp(int(user_registered))

        user_playlist_count = 0
        user_in_db = None
        try:
            user_in_db = LastfmUser.create(name=user_name, real_name=user_real_name, image=user_image, play_count=user_playcount,
                              age=user_age, gender=user_gender, registered=user_registered,
                              playlist_count=user_playlist_count, loved_count = loved_count)

            log_user_str = "Last.fm UserInfo for {}\n".format(username)
            log_user_str += "user_real_name: {}\n".format(user_real_name)
            log_user_str += "user_image: {}\n".format(user_image)
            log_user_str += "user_playcount: {}\n".format(user_playcount)
            log_user_str += "user_age: {}\n".format(user_age)
            log_user_str += "user_gender: {}\n".format(user_gender)
            log_user_str += "user_registered: {}\n".format(str(user_registered))

            logging.info(log_user_str)

            return user_in_db
        except Exception as ex:
            print("Error creating user {}".format(username))
            print(ex)
            return None

    # Helper methods
    def pylast_artist_to_db_artist(self,pylast_artist):
        artist = LastfmArtist()
        artist.name = pylast_artist.get_name()
        artist.cover_image = pylast_artist.get_cover_image()
        artist.play_count = pylast_artist.get_playcount()
        artist.listener_count = pylast_artist.get_listener_count()
        artist.bio = pylast_artist.get_bio("summary")
        artist.url = pylast_artist.get_url()
        return artist