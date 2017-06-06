from database import *
from parallel_downloader import *
from lastfm import *
import time
import sys
import subprocess

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

class Commands:
    def __init__(self, client):
        self.lastfm = LastFmWrapper()
        self.bot_config = None
        self.client = client
        try:
            self.bot_config = BotConfig.select().get()
        except:
            logging.info("Error retrieving bot config")
        
        self.prefix = self.bot_config.command_prefix

    async def nowplaying_download_complete(self,urls,data):
        artist_image_local = None
        album_image_local = None
        user_image_local = None

        album_in_db = None
        user_in_db = None

        download_time = 0
        if not urls == None and len(urls) > 0:
            download_time = time.time() - data.download_start_time

        need_update = False
        # Check for local images
        if not data.artist == None:
            artist_image_local = data.artist.cover_image_local
        if not data.album == None:
            album_image_local = data.album.cover_image_local
        if not urls == None and len(urls) > 0:
            for url in urls:
                if not data.artist == None and url == data.artist.cover_image:
                    artist_image_local = get_cache_path_from_url(url)
                    need_update = True
                elif not data.album == None and url == data.album.cover_image:
                    album_image_local = get_cache_path_from_url(url)
                    need_update = True

                if not data.user_in_db == None and url == data.user_in_db.avatar_url:
                    user_image_local = get_cache_path_from_url(url)
                    need_update = True

            if not artist_image_local == None and need_update:
                try:
                    LastfmArtist.update(cover_image_local=artist_image_local).where(LastfmArtist.name == data.artist.name).execute()
                except:
                    logging.info("Could not update LastfmArtist {}".format(data.artist.name))
                    pass

            if not data.album == None and not album_image_local == None and need_update:
                try:
                    LastfmAlbum.update(cover_image_local=album_image_local).where(
                        LastfmAlbum.title == data.album.title).execute()
                except:
                    logging.info("Could not update LastfmAlbum {}".format(data.album.name))
                    pass
            if not data.user_in_db == None and not user_image_local == None and need_update:
                try:
                    User.update(avatar_url_local=user_image_local).where(User.id == data.user_in_db.id).execute()
                except:
                    logging.info("Could not update User {}".format(data.user_in_db.id))

        need_update = False
        for rt_track in data.recent_trakcs:
            rt_album = rt_track.album
            rt_artist = rt_track.artist

            rt_album_image_local = None
            if not rt_album == None:
                if not urls == None and len(urls) > 0:
                    for url in urls:
                        if url == rt_album.cover_image:
                            rt_album_image_local = get_cache_path_from_url(rt_album.cover_image)
                            need_update = True

                    if not rt_album_image_local == None and need_update:
                        try:
                            LastfmAlbum.update(cover_image_local=rt_album_image_local).where(
                                LastfmAlbum.title == rt_album.title).execute()
                        except:
                            logging.info("Could not update LastfmAlbum {}".format(rt_album.title))
                            pass

            need_update = False
            rt_artist_image_local = None
            if not rt_artist == None:
                if not urls == None and len(urls) > 0:
                    for url in urls:
                        if url == rt_artist.cover_image:
                            rt_artist_image_local = get_cache_path_from_url(rt_artist.cover_image)
                            need_update = True

                    if not rt_artist_image_local == None and need_update:
                        try:
                            LastfmArtist.update(cover_image_local=rt_artist_image_local).where(
                                LastfmArtist.name == rt_artist.name).execute()
                        except:
                            logging.warning("Could not update LastfmArtist {}".format(rt_artist.name))


        song_name = data.title
        artist_name = "-"
        artist_scrobbles = 0  # not used
        album_scrobbles = 0  # not used
        duration = "-"
        user_name = data.lastfm_user.name
        user_avatar = "-"
        user_artist_count = 0  # not used
        user_scrobbles = data.lastfm_user.play_count  # not used
        user_favourites = data.lastfm_user.loved_count  # not used
        total_scrobbles = 0  # not used
        album_cover = album_image_local
        artist_cover = artist_image_local

        # Artist
        if not data.artist == None:
            artist_name = data.artist.name
            artist_in_db = LastfmArtist.select().where(LastfmArtist.name == data.artist.name).get()

        # Album
        if not data.album == None:
            album_in_db = LastfmAlbum.select().where(LastfmAlbum.title == data.album.title).get()

        if not data.user_in_db == None:
            user_in_db = User.select().where(User.id == data.user_in_db.id).get()

        # Track
        # track_in_db = None

        # try:
        #     track_in_db = LastfmTrack.select().where(LastfmTrack.title == data.title, LastfmTrack.artist == artist_in_db, LastfmTrack.album == album_in_db).get()
        # except:
        #     logging.info("Track not found")

        if not artist_in_db == None:
            artist_cover = artist_in_db.cover_image_local

        if not album_in_db == None:
            album_cover = album_in_db.cover_image_local

        if not user_in_db == None:
            user_avatar = user_in_db.avatar_url_local

        recent_trakcs_array = []

        if not artist_cover == None:
            artist_cover = artist_cover.replace('\\','/')

        if not album_cover == None:
            album_cover = album_cover.replace('\\', '/')

        if not user_avatar == None:
            user_avatar = user_avatar.replace('\\', '/')

        for rt in data.recent_trakcs:
            rt_album_in_db = None
            cover = None
            if not rt.album == None:
                try:
                    rt_album_in_db = LastfmAlbum.select().where(LastfmAlbum.title == rt.album.title).get()
                except:
                    pass

            text = "{} - {}".format(rt.artist.name,rt.track.title)
            if not rt_album_in_db == None:
                cover = rt_album_in_db.cover_image_local

            if cover == None:
                cover = "artist_not_found.jpg"

            recent_trakcs_array.append(cover.replace('\\','/'))
            recent_trakcs_array.append(text)

        c = len(recent_trakcs_array)
        for i in range(12 - c):
            recent_trakcs_array.append("artist_not_found.jpg")


        if album_cover == None:
            logging.warning("Setting default album cover")
            album_cover = "artist_not_found.jpg"

        if artist_cover == None:
            logging.warning("Setting default artist cover")
            artist_cover = "artist_not_found.jpg"

        if user_avatar == None:
            logging.warning("Setting default user image")
            user_avatar = "-"

        if data.user_in_db == None and data.lastfm_user == None:
            logging.warning("Setting default user image")
            user_avatar = "-"

        render_start_time = time.time()
        target_file = user_name + ".png"
        params = [cef3d_exe_path,  # target process
                  os.path.join(cef3d_path, "assets", "index.html"), os.path.join(cef3d_output_path, target_file),
                  # source html, target png
                  song_name, artist_name, album_cover, str(artist_scrobbles), str(album_scrobbles),
                  str(total_scrobbles), duration, user_name, user_avatar, str(user_artist_count), str(user_scrobbles),
                  str(user_favourites), str(artist_cover)]

        for rta in recent_trakcs_array:
            params.append(rta)
        #cef3d_proc = subprocess.Popen(params, stdout=subprocess.PIPE)

        #cef3d_proc.communicate()

        try:
            subprocess.run(params, timeout=6,stdout=subprocess.DEVNULL)
        except:
            await self.safe_send_message(
                    data.channel, "There was a problem with the request ",self.client.emoji.FeelsMetalHead,
                    expire_in=10)


        render_end_time = time.time()
        render_time = (render_end_time - render_start_time)
        logging.info("Cef3D stage took " + str(render_end_time - render_start_time))
        download_item_count = 0
        if not urls == None:
            download_item_count = len(urls)
        total = data.lastfm_fetch_time + download_time + render_time


        sendStats = data.sendStats
        content = None
        if sendStats:
            content = "Last.fm API: **{:0.2f}** seconds \nDownloading: **{:0.2f}** seconds ({} items) \nRendering: **{:0.2f}** seconds\nTotal: **{:0.2f}** seconds".format(
                data.lastfm_fetch_time, download_time,download_item_count, render_time, total)
        output_file = os.path.join(cef3d_output_path, target_file)

        logging.info("Sending to Discord..")
        # Finally, send to discord
        with open(output_file, 'rb') as f:
            if sendStats:
                await self.client.send_file(data.channel, output_file, content=content)
            else:
                await self.client.send_file(data.channel, output_file)


    def process_track(self,track, lastfm_user,download_queue, is_recent_track=False):
        # Now playing song title
        np_title = track.title

        # Now playting artist
        np_artist = track.artist

        # Album
        np_album = track.get_album()

        artist_in_db = None
        album_in_db = None

        if not np_artist == None:
            np_artist_name = np_artist.name
            # Find artist in database
            try:
                artist_in_db = LastfmArtist.select().where(LastfmArtist.name == np_artist_name).get()
            except:
                logging.info("Artist {} not found in database".format(np_artist_name))
                if not is_recent_track:
                    try:
                        artist_in_db = self.lastfm.utility.save_artist_info(lastfm_user, np_artist)
                    except:
                        logging.info("Could not add Artist {} to the database".format(np_artist_name))
                        pass
                pass
        else:
            logging.info("Artist returned None from Last.fm")

        # Artist cover
        # Look at the db 'cover_image_local'
        # If it exists, skip
        # If it doesnt exists, add the remote URL to download queue
        if not artist_in_db == None:
            artist_cover_local = artist_in_db.cover_image_local

            if artist_cover_local == None:
                if not artist_in_db.cover_image in download_queue:
                    download_queue.append(artist_in_db.cover_image)

        # Find album in database
        if not np_album == None and not artist_in_db == None:
            try:
                album_in_db = LastfmAlbum.select().where(LastfmAlbum.title == np_album.title).get()
            except:
                logging.info("Album {} not found in database".format(np_album.title))
                try:
                    album_in_db = LastfmAlbum.create(title=np_album.title, artist=artist_in_db,
                                                     cover_image=np_album.get_cover_image(), url=np_album.get_url())
                except:
                    logging.info("Could not add Album {} to the database", np_album.title)
                    pass
                pass
        else:
            logging.info("Album returned null from Last.fm")

        # Find track in db
        # try:
        #     LastfmTrack.select().where(LastfmTrack.title == np_title, LastfmTrack.artist == artist_in_db, LastfmTrack.album == album_in_db).get()
        # except:
        #     logging.info("Track not found")
        #
        #     try:
        #         LastfmTrack.create(title = np_title, duration = track.get_duration(), artist = artist_in_db, album = album_in_db, url = track.get_url())
        #     except:
        #         logging.info("Could not create track {}".format(np_title))


        # Album cover
        if not album_in_db == None:
            album_cover_local = album_in_db.cover_image_local

            if (album_cover_local == None or len(album_cover_local) == 0) and not album_in_db.cover_image in download_queue:
                download_queue.append(album_in_db.cover_image)
        return artist_in_db, album_in_db



    async def cmd_nowplaying(self, message, user_mentions, stats=False):
        start_time = time.time()

        # Possible usages
        # 1: <prefix>nowplaying lastfm_user
        # 2: <prefix>nowplaying @mention
        # 3: <prefix>nowplaying
        message_content = message.content
        split = message_content.split('{}{} '.format(self.prefix, "npstats" if stats == True else "np"))

        user = None
        lastfm_user = None
        lastfm_user_name = None
        mentioned_user = None

        # If there is a mention
        # try looking it up in the database
        if len(user_mentions) > 0:
            mentioned_user = user_mentions[0]
            try:
                user = User.select().where(User.id == mentioned_user.id).get()
            except:
                logging.info("Could not find mentioned user in DB")
        else:
            # No mention, must be case 1 or 3
            params_len = len(split)

            # Case 3
            if params_len == 1:
                try:
                    user = User.select().where(User.id == message.author.id).get()
                except:
                    logging.error("No user was specified and the message author isnt on DB.")
                    return Response("There is a problem with this user!")

            elif params_len == 2:
                # Case 1
                lastfm_user_name = split[1]


                try:
                    lastfm_user = LastfmUser.select().where(LastfmUser.name == lastfm_user_name).get()
                except:
                    logging.info("Last.fm user not found in DB")

                if not lastfm_user == None:
                    try:
                        user = User.select().where(User.lastfm_user == lastfm_user).get()
                    except:
                        logging.info("Discord user not found in DB")
            else:
                return Response("There was an error with parameter input")

        if lastfm_user_name == None and not user == None:
            lastfm_user = user.lastfm_user
            if not lastfm_user == None:
                lastfm_user_name = lastfm_user.name

        if lastfm_user == None:
            logging.info("Unknown user, not anymore!")
            lastfm_user = self.set_lastfm(lastfm_user_name)

        if user == None and lastfm_user == None:
            logging.error("There is a problem with this request")
            return Response("There is a problem with this request")
            return None

        if lastfm_user_name == None:
            return Response("There is a problem with this request")
            return None
        

        lastfm_fetch_time = 0
        image_downloads_time = 0
        rendering_time = 0

        logging.info("nowplaying is ready to execute")
        logging.info("User Name: {}".format(lastfm_user_name))
        logging.info("Discord user found: {}".format(user))

        files_to_download = []


        # Request nowplaying from Last.fm
        now_playing = self.lastfm.get_now_playing(lastfm_user_name)

        if now_playing == None:
            return Response("**{}** is not listening to any music. <:FeelsMetalHead:279991636144947200> \n".format(lastfm_user_name))
        
        discord_user_avatar = None
        if not user == None:
            discord_user_avatar = user.avatar_url

        # Check if avatar is changed
        if not discord_user_avatar == None:
            if not mentioned_user == None:
                user_info = await self.client.get_user_info(mentioned_user.id)
            else:
                user_info = await self.client.get_user_info(message.author.id)

            if not user_info == None:
                new_discord_user_avatar = user_info.avatar_url

                if not new_discord_user_avatar == None:
                    discord_user_avatar = new_discord_user_avatar

                    # Update URL
                    try:
                        User.update(avatar_url=discord_user_avatar).execute()
                    except:
                        logging.error("Could not update new avatar URL")




        if not discord_user_avatar == None:
            if exists_in_cache(discord_user_avatar):
                discord_user_avatar = get_cache_path_from_url(discord_user_avatar)
            else:
                files_to_download.append(discord_user_avatar)
        
        
        artist_in_db, album_in_db = self.process_track(now_playing,lastfm_user, files_to_download)

        # Recent Tracks
        recent_trakcs = self.lastfm.get_recent_trakcs(lastfm_user_name, 4)
        recent_tracks_array = []

        for track in recent_trakcs:
            rt_artist_in_db, rt_album_in_db = self.process_track(track.track, lastfm_user, files_to_download)
            rt_track = MMDTrack(rt_artist_in_db, rt_album_in_db, track.track)
            recent_tracks_array.append(rt_track)

        # Gather download tasks from recent tracks
        # i.e. covers
        # to do

        current_time = time.time()
        lastfm_fetch_time = current_time - start_time
        logging.info("Lastfm Fetch time: {}".format(str(lastfm_fetch_time)))
        start_time = current_time

        now_playing_entry = NowPlayingEntry(lastfm_user=lastfm_user,
                                            discord_user=message.author,
                                            title = now_playing.title,
                                            user_in_db = user,
                                            artist = artist_in_db,
                                            album= album_in_db,
                                            recent_trakcs= recent_tracks_array,
                                            channel=message.channel,
                                            lastfm_fetch_time = lastfm_fetch_time,
                                            download_start_time = start_time,
                                            sendStats=stats
                                            )

        # Start downloading if there are any download items
        if len(files_to_download) > 0:
            logging.info("{} items in download queue".format(len(files_to_download)))

            # Start downloading
            parallel_downloader = ParallelDownloader(files_to_download,download_cache,now_playing_entry, self.nowplaying_download_complete)
        else:
            await self.nowplaying_download_complete(None, now_playing_entry)

    def cmd_setlastfm(self, message):
        lastfm_user_name = message
        return self.set_lastfm(lastfm_user_name)


    def set_lastfm(self, user_name):
        try:
            lastfm_user = LastfmUser.select().where(LastfmUser.name == user_name).get()
            return lastfm_user
        except:
            try:
                lastfm_user = self.lastfm.utility.save_user_info(user_name)
                return lastfm_user
            except Exception as ex:
                logging.info("Error creating user {}".format(user_name))
                print(ex)
                pass

    def test_commands(self):
        message_content = sys.argv[1].strip()

        command, *args = message_content.split()
        command = command[len(self.prefix):].lower().strip()

        handler = getattr(self,'cmd_%s' % command, None)

        handler_args = {}
        handler_args['message'] = sys.argv[1]
        handler_args['user_mentions'] = []

        response = handler(**handler_args)

# all_start = time.time()

try:
    cmd = Commands()
    argv_command = sys.argv[1]

    if argv_command == None:
        print("Need a command to work")
        exit()
    else:
        cmd.test_commands()
except:
    pass

# end_time = time.time()
# print("Program execution time: {}".format(str(end_time - all_start)))