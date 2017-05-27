from peewee import *

db = SqliteDatabase("mmd.sqlite")

class User(Model):
    id = IntegerField(primary_key=True)
    avatarUrl = CharField()
    isBot = BooleanField()
    registerDate = DateTimeField()
    name = CharField()
    displayName = CharField()
    joinDate = DateTimeField()
    discriminator = IntegerField()
    lastfmUsername = CharField()

    #
    class Meta:
        database = db


class DiscussionAlbum(Model):
    user = ForeignKeyField(User, related_name="users")
    url = CharField()
    date = DateTimeField()

    class Meta:
        database = db

class AlbumRating(Model):
    entry = ForeignKeyField(DiscussionAlbum, related_name="entries")
    user = ForeignKeyField(User, related_name="users")
    date = DateTimeField()
    rating = IntegerField()

    class Meta:
        database = db

db.create_tables([User, DiscussionAlbum, AlbumRating])