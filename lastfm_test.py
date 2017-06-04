import pylast
import time
import subprocess
import os
from lastfm import *

current_dir = os.path.dirname(os.path.abspath(__file__))
cef3d_path = os.path.join(current_dir,'cef3d')
cef3d_exe_path = os.path.join(current_dir,'cef3d',"Cef3DHtmlRenderer.exe")
cef3d_output_path = os.path.join(current_dir,"html_render")

start = time.time()

target_user = "arkenthera"
lastfm_wrap = LastFmWrapper()

try:
    np = lastfm_wrap.get_now_playing(target_user)
except:
    np = None

if not np == None:
    artist = np.artist
    album = np.get_album()

    # Initialize with defaults
    # Cant be blank
    song_name = "-"
    artist_name = "-"
    artist_scrobbles = 0
    album_scrobbles = 0
    genre = "metal"
    user_name = "arkenthera"
    user_avatar = "avatar.webp"
    user_artist_count = 0
    user_scrobbles = 0
    user_favourites = 0
    total_scrobbles = 0

    album_cover = "artist_not_found.jpg"
    artist_cover = "artist_not_found.jpg"

    recent_trakcs = lastfm_wrap.get_recent_trakcs(target_user,7)
    recent_track_array = []

    for rt in recent_trakcs:
        rt_track = rt.track
        rt_album_title = rt.album

        rt_album = lastfm_wrap.get_album_from_artist(rt.track.artist, rt_album_title)
        recent_track_array.append(rt_album.get_cover_image())
        recent_track_array.append(rt_track.title)

    # Get album info
    np_album = lastfm_wrap.get_album_from_artist(np.artist, np.title)
    # Song Name
    song_name = np.title
    # Artist Name
    artist = np.artist

    # Artist playcount
    artist_scrobbles = np.artist.get_playcount()

    # Artist cover
    try:
        artist_cover_image = artist.get_cover_image()
        if not artist_cover_image == None:
            artist_cover = artist_cover_image
    except:
        pass
    # Duration instead of genre
    # Format the duration, its in seconds
    duration = np.get_duration() / 1000

    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)

    genre = "{}:{}".format(int(minutes),seconds)

    # user info
    lastfm_user = lastfm_wrap.get_user(target_user)
    user_scrobbles = lastfm_user.get_playcount()
    #user_artist_count = lastfm_user.get

    # Additional album info
    if not np_album == None:
        try:
            album_cover_image = np_album.get_cover_image()# COVER_SMALL
            if not album_cover_image == None:
                album_cover = album_cover_image
        except:
            pass

    artist_name = artist.name

    end = time.time()
    print("Last.fm Stage took " + str(end - start))
    start = time.time()

    params = [cef3d_exe_path, # target process
            os.path.join(cef3d_path, "assets", "index.html"),os.path.join(cef3d_output_path,"output.png"), # source html, target png
            song_name, artist_name, album_cover, str(artist_scrobbles), str(album_scrobbles), str(total_scrobbles), genre, user_name, user_avatar, str(user_artist_count), str(user_scrobbles), str(user_favourites), str(artist_cover)]

    for rta in recent_track_array:
        params.append(rta)
    print(params)
    cef3d_proc = subprocess.Popen(params,stdout=subprocess.PIPE)


    for line in cef3d_proc.stdout:
        print(line.rstrip().decode('ascii'))


    end = time.time()
    print("Cef3D stage took " + str(end - start))