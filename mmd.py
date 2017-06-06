import discord
import asyncio
import logging
import inspect
import sys
from commands import *
from emoji import EmojiHelper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

handler = logging.FileHandler(filename='mmd.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

class MusicBot(discord.Client):
    def __init__(self,token):
        self.auth = token
        super().__init__()

        self.commands = Commands(self)
        self.emoji = EmojiHelper()

    async def on_ready(self):
        logger.info("Bot is ready.")



    async def cmd_np(self, message,user_mentions):
        await self.send_typing(message.channel)

        response = await self.commands.cmd_nowplaying(message,user_mentions)
        if not response == None:
            return response

    async def cmd_npstats(self, message, user_mentions):
        await self.send_typing(message.channel)

        response = await self.commands.cmd_nowplaying(message, user_mentions, True)
        if not response == None:
            return response

    # Test command
    async def cmd_test(self):
        return Response("Test response", reply=True, delete_after=5)

    async def on_message(self,message):
        message_content = message.content.strip()

        if not message_content.startswith(self.commands.prefix):
            return

        command, *args = message_content.split()
        command = command[len(self.commands.prefix):].lower().strip()

        handler = getattr(self, 'cmd_%s' % command, None)
        if not handler:
            return

        argspec = inspect.signature(handler)
        params = argspec.parameters.copy()

        try:
            handler_kwargs = {}
            if params.pop('message', None):
                handler_kwargs['message'] = message

            if params.pop('channel', None):
                handler_kwargs['channel'] = message.channel

            if params.pop('author', None):
                handler_kwargs['author'] = message.author

            if params.pop('server', None):
                handler_kwargs['server'] = message.server

            if params.pop('user_mentions', None):
                handler_kwargs['user_mentions'] = list(map(message.server.get_member, message.raw_mentions))

            if params.pop('channel_mentions', None):
                handler_kwargs['channel_mentions'] = list(map(message.server.get_channel, message.raw_channel_mentions))

            response = await handler(**handler_kwargs)

            if response and isinstance(response, Response):
                content = response.content
                if response.reply:
                    content = '%s, %s' % (message.author.mention, content)

                sentmsg = await self.safe_send_message(
                    message.channel, content,
                    expire_in=response.delete_after
                )
        except Exception as ex:
            logger.error("Error handling command")
            content = "I've run into a problem while processing your command {}".format(self.emoji.FeelsMetalHead)
            sentmsg = await self.safe_send_message(
                message.channel, content,
                expire_in=10
            )
            print(ex)

    async def safe_send_message(self, dest, content, *, tts=False, expire_in=0, also_delete=None, quiet=False):
        msg = None
        try:
            msg = await self.send_message(dest, content, tts=tts)

            if msg and expire_in:
                asyncio.ensure_future(self._wait_delete_msg(msg, expire_in))

            if also_delete and isinstance(also_delete, discord.Message):
                asyncio.ensure_future(self._wait_delete_msg(also_delete, expire_in))

        except discord.Forbidden:
            if not quiet:
                self.safe_print("Warning: Cannot send message to %s, no permission" % dest.name)

        except discord.NotFound:
            if not quiet:
                self.safe_print("Warning: Cannot send message to %s, invalid channel?" % dest.name)

        return msg

    async def _wait_delete_msg(self, message, after):
        await asyncio.sleep(after)
        await self.safe_delete_message(message)

    async def safe_delete_message(self, message, *, quiet=False):
        try:
            return await self.delete_message(message)

        except discord.Forbidden:
            if not quiet:
                self.safe_print("Warning: Cannot delete message \"%s\", no permission" % message.clean_content)

        except discord.NotFound:
            if not quiet:
                self.safe_print("Warning: Cannot delete message \"%s\", message not found" % message.clean_content)

    async def safe_edit_message(self, message, new, *, send_if_fail=False, quiet=False):
        try:
            return await self.edit_message(message, new)

        except discord.NotFound:
            if not quiet:
                self.safe_print("Warning: Cannot edit message \"%s\", message not found" % message.clean_content)
            if send_if_fail:
                if not quiet:
                    print("Sending instead")
                return await self.safe_send_message(message.channel, new)

    def safe_print(self, content, *, end='\n', flush=True):
        sys.stdout.buffer.write((content + end).encode('utf-8', 'replace'))
        if flush: sys.stdout.flush()

    async def send_typing(self, destination):
        try:
            return await super().send_typing(destination)
        except discord.Forbidden:
            print("Could not send typing to %s, no permssion" % destination)

    def run(self):
        try:
            self.loop.run_until_complete(self.start(self.auth))
        except discord.errors.LoginFailure:
            logger.error("Login error")

        finally:
            logger.info("Exiting...")
            self.loop.close()



with open("token", "r") as tokenfile:
    token = ""
    for line in tokenfile:
        token += line
    bot = MusicBot(token)
    bot.run()