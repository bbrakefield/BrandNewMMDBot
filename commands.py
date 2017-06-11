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
                    lastfm_user = None

                # if lastfm_user is not None:
                #     user = User.select().where(User.lastfm_user == lastfm_user).get()

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
        result = self.parse_cmd_with_user("np" if stats is False else "npstats", message, user_mentions)

        logging.info("nowplaying is ready to execute")
        logging.info("User Name: {}".format(result.lastfm_user_name))

        np = None

        api_time_start = time.time()

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
                        user_avatar = self.cache.get_cache_path_from_filename(url2filename(user_avatar))
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
            if len(r_track.image) > 0:
                if r_track.image is not None and self.cache.exists_in_cache(url2filename(r_track.image)) is False:
                    files_to_download.append(r_track.image)

        api_time_end = time.time()
        api_time = api_time_end - api_time_start

        download_time_start = time.time()

        now_playing_entry = NowPlayingEntry(
            now_playing_track = now_playing_track,
            recent_tracks = recent_tracks,
            user_avatar = user_avatar,
            cmd_parse_result = result,
            channel = message.channel,
            send_stats = stats,
            api_time = api_time,
            download_time_start = download_time_start
        )
        if len(files_to_download) > 0:
            parallel_downloader = ParallelDownloader(files_to_download, download_cache, now_playing_entry,
                                                     self.nowplaying_download_complete)
        else:
            await self.nowplaying_download_complete([],now_playing_entry)

    async def nowplaying_download_complete(self, urls, data):
        download_time_end = time.time()
        now_playing_track = data.now_playing_track
        recent_tracks = data.recent_tracks
        cmd_parse_result = data.cmd_parse_result
        
        album_cover = None
        artist_cover = None
        user_avatar = None

        if data.user_avatar is not None:
            if len(data.user_avatar) > 0:
                data.user_avatar = data.user_avatar.replace('\\', '/')
            else:
                data.user_avatar = "-"
        else:
            data.user_avatar = "-"

        if now_playing_track.image is not None:
            now_playing_track.image = now_playing_track.image.replace('\\', '/')

        song_name = now_playing_track.title
        artist_name = now_playing_track.artist.name
        artist_scrobbles = 0  # not used
        album_scrobbles = 0  # not used
        duration = "-"
        user_name = cmd_parse_result.lastfm_user_name
        user_avatar = data.user_avatar
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

        download_time = download_time_end - data.download_time_start
        logging.info("Start rendering..")

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
            subprocess.run(params, timeout=6,stdout=subprocess.DEVNULL)
        except:
            logging.error("Subprocess crashed or timeout")
            await self.client.safe_send_message(
                    data.channel, "There was a problem with the request {}".format(self.client.emoji.FeelsMetalHead))

            return

        output_file = os.path.join(cef3d_output_path, target_file)

        render_end_time = time.time()
        render_time = (render_end_time - render_start_time)
        logging.info("Cef3D stage took " + str(render_end_time - render_start_time))

        if urls is not None and len(urls) > 0:
            stats = "Last.fm API: **{:0.2f}** seconds\nDownloading: **{:0.2f}** seconds (**{}** items)\nRendering: **{:0.2f}** seconds".format((data.api_time), (download_time), len(urls), (render_time))
        else:
            stats = "Last.fm API: **{:0.2f}** seconds\nDownloading: **{:0.2f}** seconds\nRendering: **{:0.2f}** seconds".format(
                (data.api_time), (download_time), (render_time))

        with open(output_file, 'rb') as f:
            if data.send_stats:
                await self.client.send_file(data.channel, f, content=stats)
            else:
                await self.client.send_file(data.channel, f)

            # Update stats after sending the image
            if cmd_parse_result.lastfm_user is not None:
                try:
                    lastfm_username = cmd_parse_result.lastfm_user.name
                    logging.info("Updating user... {}".format(lastfm_username))

                    api_user = self.lastfm.get_user(lastfm_username)
                    if api_user is None:
                        logging.error("Could not retrieve Last.fm user")
                        return None

                    # Artist count
                    artist_count = self.lastfm.get_user_artistcount(lastfm_username)
                    album_count = self.lastfm.get_user_albumcount(lastfm_username)
                    try:
                        LastfmUser.update(artist_count=artist_count, album_count=album_count, image=api_user.image, play_count=api_user.scrobbles).where(LastfmUser.name == lastfm_username).execute()
                    except:
                        logging.error("Could not update LastfmUser {}".format(lastfm_username))
                except:
                    logging.error("There was an error trying to update this user")



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
