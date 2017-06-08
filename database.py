from peewee import *

db = SqliteDatabase("mmd.db")

class LastfmUser(Model):
    name = CharField(primary_key=True)
    real_name = CharField()
    image = CharField(null=True)
    play_count = IntegerField(null=True)
    age = IntegerField(null=True)
    gender = CharField(null=True)
    registered = TimestampField(null=True)
    playlist_count = IntegerField(null=True)
    loved_count = IntegerField()
    artist_count = IntegerField()
    album_count = IntegerField()

    class Meta:
        database = db

class User(Model):
    id = BigIntegerField(primary_key=True)
    avatar_url = CharField()
    is_bot = BooleanField()
    register_date = DateTimeField()
    name = CharField()
    display_name = CharField()
    join_date = DateTimeField()
    discriminator = IntegerField()
    lastfm_user = ForeignKeyField(LastfmUser, related_name="lastfm_users", null = True)

    #
    class Meta:
        database = db


class DiscussionAlbum(Model):
    user = ForeignKeyField(User, related_name="discussion_album_users")
    url = CharField()
    date = DateTimeField()

    class Meta:
        database = db

class AlbumRating(Model):
    entry = ForeignKeyField(DiscussionAlbum, related_name="album_rating_entries")
    user = ForeignKeyField(User, related_name="album_rating_users")
    date = DateTimeField()
    rating = IntegerField()

    class Meta:
        database = db

class LastfmArtist(Model):
    name = CharField()
    play_count = IntegerField()
    listener_count = IntegerField()
    cover_image = CharField()
    cover_image_local = CharField(null=True)
    bio = CharField()
    url = CharField()

    class Meta:
        database = db

class LastfmUserArtist(Model):
    artist = ForeignKeyField(LastfmArtist, related_name="lastfm_user_artist_artists")
    user = ForeignKeyField(LastfmUser, related_name="lastfm_user_artist_users")
    play_count = IntegerField()

    class Meta:
        database = db

class LastfmAlbum(Model):
    title = CharField()
    artist = ForeignKeyField(LastfmArtist, related_name="lastfm_album_artists", null = True)
    cover_image = CharField()
    cover_image_local = CharField(null = True)
    url = CharField()

    class Meta:
        database = db

class LastfmUserAlbum(Model):
    album = ForeignKeyField(LastfmAlbum, related_name="lastfm_user_album_albums")
    user = ForeignKeyField(LastfmUser, related_name="lastfm_user_album_users")
    play_count = IntegerField()

    class Meta:
        database = db

class LastfmTrack(Model):
    title = CharField()
    artist = ForeignKeyField(LastfmArtist, related_name="lastfm_track_artists", null = True)
    album = ForeignKeyField(LastfmAlbum, related_name="lastfm_track_albums", null = True)
    duration = CharField()
    url = CharField()

    class Meta:
        database = db

class BotConfig(Model):
    command_prefix = CharField()

    class Meta:
        database = db


class UserConfig(Model):
    user = ForeignKeyField(User, related_name="user_config_users")
    chart_type = CharField()
    chart_size = CharField()

    class Meta:
        database = db

db.connect()

try:
    db.create_tables([
    UserConfig,
    BotConfig,
    User,
    LastfmUser
    # DiscussionAlbum,
    # AlbumRating,
    # LastfmTrack,
    # LastfmAlbum,
    # LastfmArtist,
    # LastfmUserAlbum,
    # LastfmUserArtist
    ])
except Exception as ex:
    print(ex)
    pass