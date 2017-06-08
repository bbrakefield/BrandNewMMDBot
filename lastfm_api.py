import json
import requests
import logging
import datetime

API_KEY = "1c15b9ea24af56c25eac1d40b24cf6b5"
API_SECRET = "2fc65d3ac585f3738b8c56a8b6013d6f"


def get_page_endpoint(endpoint,user_name, limit_page, page):
    return "http://ws.audioscrobbler.com/2.0/?method={}&user={}&api_key={}&limit={}&page={}&format=json".format(endpoint,
        user_name, API_KEY, limit_page, page)

class LastfmAPIArtist:
    def __init__(self, name, url, play_count, image, listeners):
        self.name = name
        self.url = url
        self.play_count = play_count
        self.image = image
        self.listeners = listeners

class LastfmAPIAlbum:
    def __init__(self, name, play_count, url, artist, image):
        self.name = name
        self.play_count = play_count
        self.url = url
        self.artist = artist
        self.image = image

class LastfmAPITrack:
    def __init__(self,title, artist,album, image, is_nowplaying):
        self.artist = artist
        self.album = album
        self.image = image
        self.is_nowplaying = is_nowplaying
        self.title = title

class LastfmAPIUser:
    def __init__(self, name, image, playlist_count, scrobbles, registered):
        self.name = name
        self.image = image
        self.playlist_count = playlist_count
        self.scrobbles = scrobbles
        self.registered = registered

class LastfmUserAlbumWrapper:
    def __init__(self,albums, total_albums):
        self.total_albums = total_albums
        self.albums = albums


class LastfmUserArtistWrapper:
    def __init__(self, artists, total_artists):
        self.total_artists = total_artists
        self.artists = artists


class LastfmUserArtistMeta:
    def __init__(self, total_artists):
        self.total_artists = total_artists

class LastfmAPI:
    def __init__(self):
        test = 0

    def get_user_artists(self, user_name, limit=None):
        if limit == None:
            limit = 1000
        current_page = 1

        api_method = "user.getTopArtists"

        header_request = requests.get(get_page_endpoint(api_method,user_name,limit,1))

        if header_request.status_code == 200:
            content = header_request.text
            parsed_json = json.loads(content)

            error = None
            try:
                error = parsed_json['error']
            except:
                pass
            if error is not None:
                logging.error("Last.fm API error")
                logging.error(parsed_json)
                return None
            else:
                top_artists = parsed_json['topartists']
                attr = top_artists['@attr']
                current_page = int(attr['page'])
                total_pages = int(attr['totalPages'])
                total_artists = int(attr['total'])

                logging.info("Total pages: {}".format(str(total_pages)))
                logging.info("Total Artists: {}".format(str(total_artists)))

                meta = LastfmUserArtistWrapper([], total_artists)

                # Parse this page
                artists = self.parse_artist_page(parsed_json)

                if limit is not 1:
                    for i in range(total_pages+1):
                        if i == 1 or i == 0:
                            continue
                        page_artists = []
                        logging.info("Requesting page {}".format(str(i)))
                        page_request = requests.get(get_page_endpoint(api_method,user_name,limit,i))
                        if page_request.status_code == 200:
                            page_content = page_request.text
                            page_json = json.loads(page_content)
                            page_artists = self.parse_artist_page(page_json)

                        for page_artist in page_artists:
                            artists.append(page_artist)
                    meta.artists = artists
                return meta

    def get_user_albums(self,user_name, limit=None):
        if limit == None:
            limit = 1000
        current_page = 1

        api_method = "user.getTopAlbums"

        header_request = requests.get(get_page_endpoint(api_method,user_name,limit,1))

        if header_request.status_code == 200:
            content = header_request.text
            parsed_json = json.loads(content)

            error = None
            try:
                error = parsed_json['error']
            except:
                pass
            if error is not None:
                logging.error("Last.fm API error")
                logging.error(parsed_json)
                return None
            else:
                top_albums = parsed_json['topalbums']
                attr = top_albums['@attr']
                current_page = int(attr['page'])
                total_pages = int(attr['totalPages'])
                total_albums = int(attr['total'])

                logging.info("Total pages: {}".format(str(total_pages)))
                logging.info("Total Albums: {}".format(str(total_albums)))

                meta = LastfmUserAlbumWrapper([], total_albums)

                # Parse this page
                albums = self.parse_album_page(parsed_json)

                if limit is not 1:
                    for i in range(total_pages+1):
                        if i == 1 or i == 0:
                            continue
                        page_albums = []
                        logging.info("Requesting page {}".format(str(i)))
                        page_request = requests.get(get_page_endpoint(api_method,user_name,limit,i))
                        if page_request.status_code == 200:
                            page_content = page_request.text
                            page_json = json.loads(page_content)
                            page_albums = self.parse_album_page(page_json)

                        for page_album in page_albums:
                            albums.append(page_album)
                    meta.albums = albums
                return meta

    def get_recent_tracks(self, user_name, limit=None, fetch_all=False):
        if limit == None:
            limit = 1000
        tracks = []

        api_method = "user.getRecentTracks"
        url = get_page_endpoint(api_method,user_name,limit,1)
        logging.info(url)
        header_request = requests.get(url)

        if header_request.status_code == 200:
            content = header_request.text
            parsed_json = json.loads(content)

            error = None
            try:
                error = parsed_json['error']
            except:
                pass
            if error is not None:
                logging.error("Last.fm API error")
                logging.error(parsed_json)
                return None
            else:
                recent_tracks = parsed_json['recenttracks']
                attr = recent_tracks['@attr']
                current_page = int(attr['page'])
                total_pages = int(attr['totalPages'])
                total_tracks = int(attr['total'])

                logging.info("Total pages: {}".format(str(total_pages)))
                logging.info("Total Tracks: {}".format(str(total_tracks)))

                # Parse this page
                tracks = self.parse_track_page(parsed_json)

                if fetch_all: # Note that, in our app, we wont currently need recent tracks more than 1000, so its safe to do this
                    for i in range(total_pages+1):
                        if i == 1 or i == 0:
                            continue
                        page_tracks = []
                        logging.info("Requesting page {}".format(str(i)))
                        page_request = requests.get(get_page_endpoint(api_method,user_name,limit,i))
                        if page_request.status_code == 200:
                            page_content = page_request.text
                            page_json = json.loads(page_content)
                            page_tracks = self.parse_track_page(page_json)

                        for page_track in page_tracks:
                            tracks.append(page_track)
        return tracks

    def parse_track_page(self, json):
        try:
            error = None

            track_instances = []

            try:
                error = json['error']
            except:
                pass
            if error is not None:
                logging.error("Last.fm API error")
                logging.error(json)
                return None
            else:
                recent_tracks = json['recenttracks']
                attr = recent_tracks['@attr']
                user_name = attr['user']
                current_page = int(attr['page'])

                total_pages = int(attr['totalPages'])
                total_albums = int(attr['total'])
                limit = int(attr['perPage'])

                tracks_array = recent_tracks['track']

                for track in tracks_array:
                    name = track['name']

                    url = track['url']
                    img_count = len(track['image'])
                    image = ""
                    try:
                        image = track['image'][3]['#text']
                    except:
                        logging.error("Defaulting to non-biggest album image")
                        for i in range(img_count):
                            image = track['image'][i]

                    album_inst = None
                    artist_inst = None

                    # Artist
                    try:
                        artist = track['artist']
                        artist_name = artist['#text']
                        artist_inst = LastfmAPIArtist(artist_name,"",0,"",0)
                    except:
                        pass

                    # Album
                    try:
                        album = track['album']
                        album_text = album['#text']
                        album_inst = LastfmAPIAlbum(album_text,0,"",artist_inst)
                    except:
                        pass

                    is_nowplaying = False
                    try:
                        track_attr = track['@attr']
                        if track_attr["nowplaying"] == "true":
                            is_nowplaying = True
                    except:
                        pass

                    track_inst = LastfmAPITrack(name,artist_inst,album_inst, image, is_nowplaying)
                    track_instances.append(track_inst)
            return track_instances
        except Exception as ex:
            print(ex)
            return []

    def parse_artist_page(self, json):
        try:
            error = None

            artist_instances = []

            try:
                error = json['error']
            except:
                pass
            if error is not None:
                logging.error("Last.fm API error")
                logging.error(json)
                return None
            else:
                top_artists = json['topartists']
                attr = top_artists['@attr']
                user_name = attr['user']
                current_page = int(attr['page'])

                total_pages = int(attr['totalPages'])
                total_albums = int(attr['total'])
                limit = int(attr['perPage'])

                artist_array = top_artists['artist']

                for artist in artist_array:
                    name = artist['name']
                    playcount = int(artist['playcount'])
                    url = artist['url']
                    img_count = len(artist['image'])
                    image = ""
                    try:
                        image = artist['image'][3]
                    except:
                        logging.error("Defaulting to non-biggest album image")
                        for i in range(img_count):
                            image = artist['image'][i]


                    artist_inst = LastfmAPIArtist(name,playcount,url,image,0)
                    artist_instances.append(artist_inst)
            return artist_instances
        except Exception as ex:
            print(ex)
            return []

    def parse_album_page(self, json):
        try:
            error = None

            album_instances = []

            try:
                error = json['error']
            except:
                pass
            if error is not None:
                logging.error("Last.fm API error")
                logging.error(json)
                return None
            else:
                top_albums = json['topalbums']
                attr = top_albums['@attr']
                user_name = attr['user']
                current_page = int(attr['page'])

                total_pages = int(attr['totalPages'])
                total_albums = int(attr['total'])
                limit = int(attr['perPage'])

                album_array = top_albums['album']

                for album in album_array:
                    name = album['name']
                    playcount = int(album['playcount'])
                    url = album['url']
                    img_count = len(album['image'])
                    image = ""
                    try:
                        image = album['image'][3]
                    except:
                        logging.error("Defaulting to non-biggest album image")
                        for i in range(img_count):
                            image = album['image'][i]

                    artist = album['artist']
                    artist_name = artist['name']
                    artist_url = artist['url']
                    artist_inst = LastfmAPIArtist(artist_name, artist_url,0,"",0)
                    album_inst = LastfmAPIAlbum(name,playcount,url, artist_inst, image)

                    album_instances.append(album_inst)
            return album_instances
        except Exception as ex:
            print(ex)
            return []

    def get_artist_info(self, artist_name, image_size=5):
        try:
            api_method = "artist.getInfo"

            header_request = requests.get("http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={}&api_key={}&format=json".format(artist_name, API_KEY))

            if header_request.status_code == 200:
                content = header_request.text
                parsed_json = json.loads(content)

                error = None
                try:
                    error = parsed_json['error']
                except:
                    pass
                if error is not None:
                    logging.error("Last.fm API error")
                    logging.error(parsed_json)
                    return None
                else:
                    artist_info = parsed_json['artist']
                    name = artist_info["name"]
                    url = artist_info["url"]
                    try:
                        images = artist_info["image"]
                        image_count = len(images)

                        try:
                            image = images[image_size]
                        except:
                            for i in range(image_count):
                                image = images[i]
                    except:
                        pass
                    playcount = 0
                    listeners = 0
                    try:
                        stats = artist_info["stats"]
                        listeners = stats["listeners"]
                        playcount = stats["playcount"]
                    except:
                        pass

                    return LastfmAPIArtist(name,url, playcount, image, listeners)

        except:
            return None


    def get_user_info(self, user_name, image_size=3):
        try:
            api_method = "user.getInfo"

            header_request = requests.get("http://ws.audioscrobbler.com/2.0/?method={}&user={}&api_key={}&format=json".format(api_method, user_name, API_KEY))

            if header_request.status_code == 200:
                content = header_request.text
                parsed_json = json.loads(content)

                error = None
                try:
                    error = parsed_json['error']
                except:
                    pass
                if error is not None:
                    logging.error("Last.fm API error")
                    logging.error(parsed_json)
                    return None
                else:
                    user_info = parsed_json['user']
                    name = user_info["name"]
                    url = user_info["url"]
                    try:
                        images = user_info["image"]
                        image_count = len(images)

                        try:
                            image = images[image_size]["#text"]
                        except:
                            for i in range(image_count):
                                image = images[i]["#text"]
                    except:
                        pass
                    playcount = user_info["playcount"]
                    playlist_count = user_info["playlists"]
                    registered = datetime.datetime.fromtimestamp(int(user_info["registered"]["unixtime"]))

                    return LastfmAPIUser(name, image, playlist_count, playcount, registered)

        except:
            return None