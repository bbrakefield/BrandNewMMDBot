import unittest
import asyncio
import sys
import time
from contextlib import closing
from commands import *

class MockDiscordUser:
    def __init__(self,id, avatar_url, is_bot, created_at, discriminator, display_name, name, join_date):
        self.id = id
        self.avatar_url = avatar_url
        self.bot = is_bot
        self.created_at = created_at
        self.discriminator = discriminator
        self.display_name = display_name
        self.name = name


class MockDiscordMember:
    def __init__(self,id, join_date):
        self.id = id
        self.joined_at = join_date




class MockDiscordMessage:
    def __init__(self, content, author):
        self.content = content
        self.author = author

class MockDiscordClient:
    async def get_user_info(self, user_id):
        return MockDiscordUser(user_id, "https://lastfm-img2.akamaized.net/i/u/300x300/59b6d6afd9a2462f85060f6c32def3f9.png", False, datetime.datetime.now(), 2345, "arkenthera", "arkenthera", datetime.datetime.now())


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.mock_client = MockDiscordClient()
        self.cmd = Commands(None)
        self.cmd.client = self.mock_client

        self.mock_author = MockDiscordMember(id="77509464290234368", join_date=datetime.datetime.now())
        self.cmd_prefix = self.cmd.prefix


    def test_cmd_nowplaying_no_parameters(self):
        cmd = "nowplaying"
        cmd_text = "{}{}".format(self.cmd_prefix, cmd)

        message = MockDiscordMessage(content=cmd_text, author=self.mock_author)
        result = self.cmd.parse_cmd_with_user("nowplaying", message, [])

        # Should not be equal to a Response
        self.assertIs(isinstance(result, Response), False)

        # Should be an instance of CmdParseResult
        self.assertIs(isinstance(result, CmdParseResult), True)

        #
        self.assertEqual(result.lastfm_user_name, "arkenthera")


    def test_cmd_nowplaying_lastfm_username(self):
        cmd = "nowplaying"
        cmd_text = "{}{} arkenthera".format(self.cmd_prefix, cmd)

        message = MockDiscordMessage(content=cmd_text, author=self.mock_author)
        result = self.cmd.parse_cmd_with_user("nowplaying", message, [])

        # Should not be equal to a Response
        self.assertIs(isinstance(result, Response), False)

        # Should be an instance of CmdParseResult
        self.assertIs(isinstance(result, CmdParseResult), True)

        #
        self.assertEqual(result.lastfm_user_name, "arkenthera")

    def test_cmd_nowplaying_user_mentions(self):
        cmd = "nowplaying"
        cmd_text = "{}{}".format(self.cmd_prefix, cmd)

        message = MockDiscordMessage(content=cmd_text, author=self.mock_author)
        result = self.cmd.parse_cmd_with_user("nowplaying", message, [self.mock_author])

        # Should not be equal to a Response
        self.assertIs(isinstance(result, Response), False)

        # Should be an instance of CmdParseResult
        self.assertIs(isinstance(result, CmdParseResult), True)

        #
        self.assertEqual(result.lastfm_user_name, "arkenthera")

class TestLogic(unittest.TestCase):
    def setUp(self):
        self.mock_client = MockDiscordClient()
        self.cmd = Commands(None)
        self.cmd.client = self.mock_client

        self.mock_author = MockDiscordMember(id="77509464290234368", join_date=datetime.datetime.now())
        self.cmd_prefix = self.cmd.prefix

    def test_cmd_nowplaying(self):
        with closing(asyncio.get_event_loop()) as loop:
            cmd = "nowplaying"
            cmd_text = "{}{}".format(self.cmd_prefix, cmd)

            message = MockDiscordMessage(content=cmd_text, author=self.mock_author)
            now_playing_task = self.cmd.cmd_nowplaying(message=message, user_mentions=[])

            tasks = [now_playing_task]
            tasks = asyncio.gather(*tasks)
            result = loop.run_until_complete(tasks)

    def test_cmd_setlastfm(self):
        with closing(asyncio.get_event_loop()) as loop:
            cmd = "setlastfm"
            cmd_text = "{}{} arkenthera".format(self.cmd_prefix, cmd)

            message = MockDiscordMessage(content=cmd_text, author=self.mock_author)
            task = self.cmd.cmd_setlastfm(message=message)

            tasks = [task]
            tasks = asyncio.gather(*tasks)
            result = loop.run_until_complete(tasks)



if __name__ == '__main__':
    unittest.main()