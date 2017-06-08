from database import *
from parallel_downloader import *
from lastfm import *
import time
import sys
import subprocess
from cache import *

current_dir = os.path.dirname(os.path.abspath(__file__))
cef3d_path = os.path.join(current_dir,'cef3d')
cef3d_exe_path = os.path.join(current_dir,'cef3d',"Cef3DHtmlRenderer.exe")
cef3d_output_path = os.path.join(current_dir,"html_render")

class NowPlayingEntry:
    def __init__(self,**kw_args):
        self.__dict__.update(kw_args)

class Response:
    def __init__(self, content, reply=False, delete_after=0):
        self.content = content
        self.reply = reply
        self.delete_after = delete_after

class CmdParseResult:
    def __init__(self, user, lastfm_user, lastfm_user_name, cmd_mode):
        self.user = user
        self.lastfm_user = lastfm_user
        self.lastfm_user_name = lastfm_user_name
        self.cmd_mode = cmd_mode

class Commands:
    def __init__(self, client):
        self.lastfm = LastFmWrapper()
        self.bot_config = None
        self.client = client
        try:
            self.bot_config = BotConfig.select().get()
        except:
            logging.error("Error retrieving bot config")
        
        self.prefix = self.bot_config.command_prefix

        self.cache = Cache()

    # async def nowplaying_download_complete(self,urls,data):
    #     artist_image_local = None
    #     album_image_local = None
    #     user_image_local = None
    #
    #     album_in_db = None
    #     user_in_db = None
    #
    #     download_time = 0
    #     if not urls == None and len(urls) > 0:
    #         download_time = time.time() - data.download_start_time
    #
    #     need_update = False
    #     # Check for local images
    #     if not data.artist == None:
    #         artist_image_local = data.artist.cover_image_local
    #     if not data.album == None:
    #         album_image_local = data.album.cover_image_local
    #     if not urls == None and len(urls) > 0:
    #         for url in urls:
    #             if not data.artist == None and url == data.artist.cover_image:
    #                 artist_image_local = get_cache_path_from_url(url)
    #                 need_update = True
    #             elif not data.album == None and url == data.album.cover_image:
    #                 album_image_local = get_cache_path_from_url(url)
    #                 need_update = True
    #
    #             if not data.user_in_db == None and url == data.user_in_db.avatar_url:
    #                 user_image_local = get_cache_path_from_url(url)
    #                 need_update = True
    #
    #         if not artist_image_local == None and need_update:
    #             try:
    #                 LastfmArtist.update(cover_image_local=artist_image_local).where(LastfmArtist.name == data.artist.name).execute()
    #             except:
    #                 logging.info("Could not update LastfmArtist {}".format(data.artist.name))
    #                 logging.warning("Could not update LastfmArtist")
    #                 pass
    #
    #         if not data.album == None and not album_image_local == None and need_update:
    #             try:
    #                 LastfmAlbum.update(cover_image_local=album_image_local).where(
    #                     LastfmAlbum.title == data.album.title).execute()
    #             except:
    #                 logging.info("Could not update LastfmAlbum {}".format(data.album.title))
    #                 logging.warning("Could not update LastfmAlbum")
    #                 pass
    #         if not data.user_in_db == None and not user_image_local == None and need_update:
    #             try:
    #                 User.update(avatar_url_local=user_image_local).where(User.id == data.user_in_db.id).execute()
    #             except:
    #                 logging.warning("Could not update User {}".format(data.user_in_db.id))
    #
    #     need_update = False
    #     for rt_track in data.recent_trakcs:
    #         rt_album = rt_track.album
    #         rt_artist = rt_track.artist
    #
    #         rt_album_image_local = None
    #         if not rt_album == None:
    #             if not urls == None and len(urls) > 0:
    #                 for url in urls:
    #                     if url == rt_album.cover_image:
    #                         rt_album_image_local = get_cache_path_from_url(rt_album.cover_image)
    #                         need_update = True
    #
    #                 if not rt_album_image_local == None and need_update:
    #                     try:
    #                         LastfmAlbum.update(cover_image_local=rt_album_image_local).where(
    #                             LastfmAlbum.title == rt_album.title).execute()
    #                     except:
    #                         logging.info("Could not update LastfmAlbum {}".format(rt_album.title))
    #                         logging.warning("Could not update LastfmAlbum")
    #                         pass
    #
    #         need_update = False
    #         rt_artist_image_local = None
    #         if not rt_artist == None:
    #             if not urls == None and len(urls) > 0:
    #                 for url in urls:
    #                     if url == rt_artist.cover_image:
    #                         rt_artist_image_local = get_cache_path_from_url(rt_artist.cover_image)
    #                         need_update = True
    #
    #                 if not rt_artist_image_local == None and need_update:
    #                     try:
    #                         LastfmArtist.update(cover_image_local=rt_artist_image_local).where(
    #                             LastfmArtist.name == rt_artist.name).execute()
    #                     except:
    #                         logging.info("Could not update LastfmArtist {}".format(rt_artist.name))
    #                         logging.warning("Could not update LastfmArtist")
    #
    #
    #     song_name = data.title
    #     artist_name = "-"
    #     artist_scrobbles = 0  # not used
    #     album_scrobbles = 0  # not used
    #     duration = "-"
    #     user_name = data.lastfm_user.name
    #     user_avatar = "-"
    #     user_artist_count = 0  # not used
    #     user_scrobbles = data.lastfm_user.play_count  # not used
    #     user_favourites = data.lastfm_user.loved_count  # not used
    #     total_scrobbles = 0  # not used
    #     album_cover = album_image_local
    #     artist_cover = artist_image_local
    #
    #     # Artist
    #     if not data.artist == None:
    #         artist_name = data.artist.name
    #         artist_in_db = LastfmArtist.select().where(LastfmArtist.name == data.artist.name).get()
    #
    #     # Album
    #     if not data.album == None:
    #         album_in_db = LastfmAlbum.select().where(LastfmAlbum.title == data.album.title).get()
    #
    #     if not data.user_in_db == None:
    #         user_in_db = User.select().where(User.id == data.user_in_db.id).get()
    #
    #     # Track
    #     # track_in_db = None
    #
    #     # try:
    #     #     track_in_db = LastfmTrack.select().where(LastfmTrack.title == data.title, LastfmTrack.artist == artist_in_db, LastfmTrack.album == album_in_db).get()
    #     # except:
    #     #     logging.info("Track not found")
    #
    #     if not artist_in_db == None:
    #         artist_cover = artist_in_db.cover_image_local
    #
    #     if not album_in_db == None:
    #         album_cover = album_in_db.cover_image_local
    #
    #     if not user_in_db == None:
    #         user_avatar = user_in_db.avatar_url_local
    #
    #     recent_trakcs_array = []
    #
    #     if not artist_cover == None:
    #         artist_cover = artist_cover.replace('\\','/')
    #
    #     if not album_cover == None:
    #         album_cover = album_cover.replace('\\', '/')
    #
    #     if not user_avatar == None:
    #         user_avatar = user_avatar.replace('\\', '/')
    #
    #     for rt in data.recent_trakcs:
    #         rt_album_in_db = None
    #         cover = None
    #         if not rt.album == None:
    #             try:
    #                 rt_album_in_db = LastfmAlbum.select().where(LastfmAlbum.title == rt.album.title).get()
    #             except:
    #                 pass
    #
    #         text = "{} - {}".format(rt.artist.name,rt.track.title)
    #         if not rt_album_in_db == None:
    #             cover = rt_album_in_db.cover_image_local
    #
    #         if cover == None:
    #             cover = "artist_not_found.jpg"
    #
    #         recent_trakcs_array.append(cover.replace('\\','/'))
    #         recent_trakcs_array.append(text)
    #
    #     c = len(recent_trakcs_array)
    #     for i in range(12 - c):
    #         recent_trakcs_array.append("artist_not_found.jpg")
    #
    #
    #     if album_cover == None:
    #         logging.warning("Setting default album cover")
    #         album_cover = "artist_not_found.jpg"
    #
    #     if artist_cover == None:
    #         logging.warning("Setting default artist cover")
    #         artist_cover = "artist_not_found.jpg"
    #
    #     if user_avatar == None:
    #         logging.warning("Setting default user image")
    #         user_avatar = "-"
    #
    #     if data.user_in_db == None and data.lastfm_user == None:
    #         logging.warning("Setting default user image")
    #         user_avatar = "-"
    #
    #     render_start_time = time.time()
    #     target_file = user_name + ".png"
    #     params = [cef3d_exe_path,  # target process
    #               os.path.join(cef3d_path, "assets", "index.html"), os.path.join(cef3d_output_path, target_file),
    #               # source html, target png
    #               song_name, artist_name, album_cover, str(artist_scrobbles), str(album_scrobbles),
    #               str(total_scrobbles), duration, user_name, user_avatar, str(user_artist_count), str(user_scrobbles),
    #               str(user_favourites), str(artist_cover)]
    #
    #     for rta in recent_trakcs_array:
    #         params.append(rta)
    #     #cef3d_proc = subprocess.Popen(params, stdout=subprocess.PIPE)
    #
    #     #cef3d_proc.communicate()
    #
    #     try:
    #         subprocess.run(params, timeout=6,stdout=subprocess.DEVNULL)
    #     except:
    #         logging.error("Subprocess crashed or timeout")
    #         await self.safe_send_message(
    #                 data.channel, "There was a problem with the request ",self.client.emoji.FeelsMetalHead,
    #                 expire_in=10)
    #
    #
    #     render_end_time = time.time()
    #     render_time = (render_end_time - render_start_time)
    #     logging.info("Cef3D stage took " + str(render_end_time - render_start_time))
    #     download_item_count = 0
    #     if not urls == None:
    #         download_item_count = len(urls)
    #     total = data.lastfm_fetch_time + download_time + render_time
    #
    #
    #     sendStats = data.sendStats
    #     content = None
    #     if sendStats:
    #         content = "Last.fm API: **{:0.2f}** seconds \nDownloading: **{:0.2f}** seconds ({} items) \nRendering: **{:0.2f}** seconds\nTotal: **{:0.2f}** seconds".format(
    #             data.lastfm_fetch_time, download_time,download_item_count, render_time, total)
    #         logging.info(content)
    #     output_file = os.path.join(cef3d_output_path, target_file)
    #
    #     logging.info("Sending to Discord..")
    #     # Finally, send to discord
    #     with open(output_file, 'rb') as f:
    #         if sendStats:
    #             await self.client.send_file(data.channel, output_file, content=content)
    #         else:
    #             await self.client.send_file(data.channel, output_file)
    #
    #
    # def process_track(self,track, lastfm_user,download_queue, is_recent_track=False):
    #     # Now playing song title
    #     np_title = track.title
    #
    #     # Now playting artist
    #     np_artist = track.artist
    #
    #     # Album
    #     np_album = track.album
    #
    #     artist_in_db = None
    #     album_in_db = None
    #
    #     if not np_artist == None:
    #         np_artist_name = np_artist.name
    #         # Find artist in database
    #         try:
    #             artist_in_db = LastfmArtist.select().where(LastfmArtist.name == np_artist_name).get()
    #         except:
    #             logging.info("Artist {} not found in database".format(np_artist_name))
    #             if not is_recent_track:
    #                 try:
    #                     artist_in_db = self.lastfm.utility.save_artist_info(lastfm_user, np_artist)
    #                 except:
    #                     logging.info("Could not add Artist {} to the database".format(np_artist_name))
    #                     pass
    #             pass
    #     else:
    #         logging.warning("Artist returned None from Last.fm")
    #
    #     # Artist cover
    #     # Look at the db 'cover_image_local'
    #     # If it exists, skip
    #     # If it doesnt exists, add the remote URL to download queue
    #     if not artist_in_db == None:
    #         artist_cover_local = artist_in_db.cover_image_local
    #
    #         if artist_cover_local == None:
    #             if not artist_in_db.cover_image in download_queue:
    #                 download_queue.append(artist_in_db.cover_image)
    #
    #     # Find album in database
    #     if not np_album == None and not artist_in_db == None:
    #         try:
    #             album_in_db = LastfmAlbum.select().where(LastfmAlbum.title == np_album.title).get()
    #         except:
    #             logging.info("Album {} not found in database".format(np_album.title))
    #             try:
    #                 album_in_db = LastfmAlbum.create(title=np_album.title, artist=artist_in_db,
    #                                                  cover_image=np_album.get_cover_image(), url=np_album.get_url())
    #             except:
    #                 logging.info("Could not add Album {} to the database", np_album.title)
    #                 pass
    #             pass
    #     else:
    #         logging.info("Album returned null from Last.fm")
    #
    #     # Find track in db
    #     # try:
    #     #     LastfmTrack.select().where(LastfmTrack.title == np_title, LastfmTrack.artist == artist_in_db, LastfmTrack.album == album_in_db).get()
    #     # except:
    #     #     logging.info("Track not found")
    #     #
    #     #     try:
    #     #         LastfmTrack.create(title = np_title, duration = track.get_duration(), artist = artist_in_db, album = album_in_db, url = track.get_url())
    #     #     except:
    #     #         logging.info("Could not create track {}".format(np_title))
    #
    #
    #     # Album cover
    #     if not album_in_db == None:
    #         album_cover_local = album_in_db.cover_image_local
    #
    #         if (album_cover_local == None or len(album_cover_local) == 0) and not album_in_db.cover_image in download_queue:
    #             download_queue.append(album_in_db.cover_image)
    #     return artist_in_db, album_in_db

    def parse_cmd_with_user(self,cmd, message, user_mentions):
        message_content = message.content
        split = message_content.split('{}{} '.format(self.prefix, cmd))

        user = None  # User
        lastfm_user = None  # LastfmUser
        lastfm_user_name = None  # lastfm user name string
        mentioned_user = None
        cmd_mode = 0

        if len(user_mentions) > 0:
            mentioned_user = user_mentions[0]
            try:
                user = User.select().where(User.id == mentioned_user.id).get()
                cmd_mode = 3
            except:
                pass

        if mentioned_user is not None:
            lastfm_user = user.lastfm_user # Can be null

        # Case 1/3
        if lastfm_user is None:
            params_len = len(split)
            if params_len == 1:
                try:
                    user = User.select().where(User.id == message.author.id).get()
                    lastfm_user = user.lastfm_user
                    cmd_mode = 1
                except Exception as ex:
                    logging.error("Could not find author on database")
                    logging.error(ex)
                    pass
            elif params_len == 2:
                lastfm_user_name = split[1]
                cmd_mode = 2
                try:
                    lastfm_user = LastfmUser.select().where(LastfmUser.name == lastfm_user_name).get()
                except:
                    logging.error("Could not find user {} on database".format(lastfm_user_name))

                if lastfm_user is not None:
                    user = User.select().where(User.lastfm_user == lastfm_user).get()

        if lastfm_user is None and lastfm_user_name is None:
            return Response("There was an error with parameter input")

        if lastfm_user is not None:
            lastfm_user_name = lastfm_user.name

        if lastfm_user is None and lastfm_user_name is None:
            return Response("There was an error with parameter input")


        # cmd_mode 3 : mentioned user
        # cmd_mode 2 : raw last.fm username
        # cmd_cmode 1 : no user input
        return CmdParseResult(user, lastfm_user, lastfm_user_name, cmd_mode)

    async def cmd_nowplaying(self, message, user_mentions, stats=False):
        start_time = time.time()
        result = self.parse_cmd_with_user("np", message, user_mentions)

        logging.info("nowplaying is ready to execute")
        logging.info("User Name: {}".format(result.lastfm_user_name))

        np = None

        np = self.lastfm.get_recent_tracks(result.lastfm_user_name, limit=3) # Last 4 tracks, first should be nowplaying
        if np is not None and len(np) > 0 and np[0].is_nowplaying is not True:
            np = None
        elif len(np) == 0:
            np = None

        if np == None:
            return Response("**{}** is not listening to any music. <:FeelsMetalHead:279991636144947200> \n".format(
                result.lastfm_user_name))

        now_playing_track = np[0]
        recent_tracks = []
        tracks_len = len(np)
        for i in range(tracks_len):
            if i == 0:
                continue
            recent_tracks.append(np[i])


        files_to_download = []
        # Avatar logic
        # Case 0 : If the command doesnt have any user input, use discord avatar
        # Case 1 : If there is a mentioned user, get mentioned user's avatar
        # Case 2 : If there is a raw last.fm user, get that avatar from Last.fm

        user_avatar = None
        # Case 0
        if result.cmd_mode == 1 or result.cmd_mode == 3:
            avatar_cache_entry = self.cache.get_discord_user_avatar(result.user)
            user_avatar = avatar_cache_entry.location
            # If the user avatar doesnt exist on disk, add it to download items
            if avatar_cache_entry.exists:
                pass
            elif avatar_cache_entry.needs_download:
                files_to_download.append(avatar_cache_entry.url)

        if result.cmd_mode == 2:
            # Check if this user is known
            try:
                lastfm_user = LastfmUser.select().where(LastfmUser.name == result.lastfm_user_name).get()
                if lastfm_user.image is not None and len(lastfm_user.image) > 0:
                    user_avatar = lastfm_user.image
                    if self.cache.exists_in_cache(url2filename(user_avatar)) is False:
                        files_to_download.append(user_avatar)
            except:
                # User is not known, look them up
                try:
                    api_user = self.lastfm.get_user(result.lastfm_user_name)
                    artist_count = self.lastfm.get_user_artistcount(result.lastfm_user_name)
                    album_count = self.lastfm.get_user_albumcount(result.lastfm_user_name)
                except:
                    return Response("Could not find this user.")

                # Save it to DB
                try:
                    lastfm_user = LastfmUser.create(name=result.lastfm_user_name, real_name=result.lastfm_user_name,
                                                    image=api_user.image, play_count=api_user.scrobbles,
                                                    age=0, gender="", registered=api_user.registered,
                                                    playlist_count=api_user.playlist_count, loved_count=0,
                                                    artist_count=artist_count, album_count=album_count)
                    result.lastfm_user = lastfm_user
                except:
                    logging.error("Could not create LastfmUser {}".format(result.lastfm_user_name))
                    pass
                pass

        # Album cover
        album_cover = None

        if now_playing_track.image is not None:
            album_cover = now_playing_track.image

        # Check if album cover exists
        if self.cache.exists_in_cache(url2filename(album_cover)) is False:
            files_to_download.append(album_cover)

        # Check covers for 'recent tracks'
        for r_track in recent_tracks:
            if r_track.image is not None and self.cache.exists_in_cache(url2filename(r_track.image)) is False:
                files_to_download.append(r_track.image)

        now_playing_entry = NowPlayingEntry(
            now_playing_track = now_playing_track,
            recent_tracks = recent_tracks,
            user_avatar = user_avatar,
            cmd_parse_result = result,
            channel = message.channel
        )
        if len(files_to_download) > 0:
            parallel_downloader = ParallelDownloader(files_to_download, download_cache, now_playing_entry,
                                                     self.nowplaying_download_complete)
        else:
            await self.nowplaying_download_complete([],now_playing_entry)

    async def nowplaying_download_complete(self, urls, data):
        now_playing_track = data.now_playing_track
        recent_tracks = data.recent_tracks
        cmd_parse_result = data.cmd_parse_result
        
        album_cover = None
        artist_cover = None
        user_avatar = None

        if data.user_avatar is not None:
            data.user_avatar = data.user_avatar.replace('\\', '/')

        if now_playing_track.image is not None:
            now_playing_track.image = now_playing_track.image.replace('\\', '/')

        song_name = now_playing_track.title
        artist_name = now_playing_track.artist.name
        artist_scrobbles = 0  # not used
        album_scrobbles = 0  # not used
        duration = "-"
        user_name = cmd_parse_result.lastfm_user_name
        user_avatar = self.cache.get_cache_path_from_url(data.user_avatar)
        user_artist_count = cmd_parse_result.lastfm_user.artist_count
        user_scrobbles = cmd_parse_result.lastfm_user.play_count
        user_favourites = cmd_parse_result.lastfm_user.album_count
        total_scrobbles = 0  # not used

        if now_playing_track.image is not None:
            album_cover = self.cache.get_cache_path_from_url(now_playing_track.image)
            artist_cover = album_cover # temporary

        if not artist_cover == None:
            artist_cover = artist_cover.replace('\\','/')

        if not album_cover == None:
            album_cover = album_cover.replace('\\', '/')

        if not user_avatar == None:
            user_avatar = user_avatar.replace('\\', '/')

        recent_tracks_array = []
        for rt in recent_tracks:
            cover = self.cache.get_cache_path_from_url(rt.image)
            text = rt.title

            if cover == None:
                cover = "artist_not_found.jpg"

            recent_tracks_array.append(cover.replace('\\','/'))
            recent_tracks_array.append(text)

        if user_avatar == None:
            user_avatar = "-"

        if album_cover == None:
            album_cover = None

        if artist_cover == None:
            artist_cover = None

        c = len(recent_tracks_array)
        for i in range(12 - c):
            recent_tracks_array.append("artist_not_found.jpg")

        render_start_time = time.time()
        target_file = user_name + ".png"
        params = [cef3d_exe_path,  # target process
                  os.path.join(cef3d_path, "assets", "index.html"), os.path.join(cef3d_output_path, target_file),
                  # source html, target png
                  song_name, artist_name, album_cover, str(artist_scrobbles), str(album_scrobbles),
                  str(total_scrobbles), duration, user_name, user_avatar, str(user_artist_count), str(user_scrobbles),
                  str(user_favourites), str(artist_cover)]

        for rta in recent_tracks_array:
            params.append(rta)

        try:
            subprocess.run(params, timeout=6000,stdout=subprocess.DEVNULL)
        except:
            logging.error("Subprocess crashed or timeout")
            await self.client.safe_send_message(
                    data.channel, "There was a problem with the request {}".format(self.client.emoji.FeelsMetalHead),
                    expire_in=10)

        output_file = os.path.join(cef3d_output_path, target_file)

        render_end_time = time.time()
        render_time = (render_end_time - render_start_time)
        logging.info("Cef3D stage took " + str(render_end_time - render_start_time))

        with open(output_file, 'rb') as f:
            await self.client.send_file(data.channel, f)



    async def cmd_setlastfm(self, message):
        result = self.parse_cmd_with_user("setlastfm", message, [])

        # There might have been an error
        if isinstance(result, Response):
            return result

        if result.lastfm_user_name is None:
            return Response("Error! You need to input a Last.fm user name")

        result = await self.set_lastfm(message.author, result.lastfm_user_name)
        # Errored
        if isinstance(result, Response):
            return result

        if result == None:
            return Response("Error!")

        return Response("Success!")



    async def set_lastfm(self, discord_user, lastfm_username):
        # Try to find this user
        user = None
        lastfm_user = None
        try:
            user = User.select().where(User.id == discord_user.id).get()
        except:
            try:
                user = await self.add_user_to_db(discord_user)
            except Exception as ex:
                logging.error("Error creating user {}".format(discord_user.id))
                logging.error(ex)
                return None

        if user is not None:
            try:
                lastfm_user = user.lastfm_user

                api_user = self.lastfm.get_user(lastfm_username)
                if api_user is None:
                    logging.error("Could not retrieve Last.fm user")
                    return None

                # Artist count
                artist_count = self.lastfm.get_user_artistcount(lastfm_username)
                album_count = self.lastfm.get_user_albumcount(lastfm_username)

                if lastfm_user is None:
                    try:
                        lastfm_user = LastfmUser.create(name=lastfm_username, real_name=lastfm_username, image=api_user.image, play_count=api_user.scrobbles,
                                                    age=0, gender="", registered=api_user.registered, playlist_count=api_user.playlist_count, loved_count=0,artist_count=artist_count,album_count=album_count)

                        # And finally, link the users
                        User.update(lastfm_user=lastfm_user).where(User.id == user.id).execute()
                    except:
                        logging.error("Could not create LastfmUser {}".format(lastfm_username))
                        return Response("There was a problem trying to process this user.")
                else:
                    try:
                        LastfmUser.update(artist_count=artist_count, album_count=album_count, image=api_user.image, play_count=api_user.scrobbles).where(LastfmUser.name == lastfm_username).execute()
                    except:
                        logging.error("Could not update LastfmUser {}".format(lastfm_username))
            except:
                logging.error("There was an error trying to process this user {}".format(lastfm_username))
                return Response("There was a problem trying to process this user.")

        return lastfm_user



    async def add_user_to_db(self, member):
        user_info = await self.client.get_user_info(member.id)
        avatar_url = user_info.avatar_url
        isBot = user_info.bot
        created_at = user_info.created_at
        discriminator = user_info.discriminator
        display_name = user_info.display_name
        name = user_info.name
        join_date = member.joined_at

        logging.info(
            "Adding new user to DB {} {} {} {} {} {} {} {}".format(member.id, name, display_name, join_date, created_at,
                                                                   isBot, avatar_url, discriminator))

        try:
            return User.create(id=int(member.id), avatar_url=avatar_url, is_bot=isBot, register_date=created_at,
                        discriminator=discriminator, display_name=display_name, name=name, join_date=join_date)
        except Exception as error:
            logging.debug("User.create failed. Probably due to primary key already existing. {}".format(error))
            return None
