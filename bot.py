"""The actual bot that you run"""
import datetime
import json
import os
import time
import re

import aiohttp
import asyncpg
import discord
import alexflipnote
from discord.ext import commands
from collections import Counter

from utils.context import CustomContext


class SYSTEM32(commands.Bot):
    """Subclassed Bot"""

    def __init__(self):
        self.bot = None
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            intents=intents,
            owner_ids={809587169520910346},
            description='system 32 will be deleted')
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.author_id = 809587169520910346
        self.session = aiohttp.ClientSession()
        self.embed_color = 0x9c5cb4  # 0x1E90FF
        self.prefixes = {}
        self.bot.deleted_messages = {}
        self.command_list = []
        self.default_prefix = 'c//'
        self.socket_stats = Counter()
        self.socket_receive = 0
        self.alex = alexflipnote.Client(self.get_config('alex_api_key'))
        self.timetime = time.time()

    @staticmethod
    def get_config(item: str):
        """Gets an item from the config"""
        with open('/root/bot/SYSTEM32/config.json', 'r') as f:
            f = json.load(f)
        return f[item]

    async def get_prefix(self, message):
        """Function for getting the command prefix"""
        if message.guild is None:
            return commands.when_mentioned_or(self.default_prefix)(self, message)
        try:
            return commands.when_mentioned_or(self.prefixes[message.guild.id])(self, message)
        except KeyError:
            prefix = await self.db.fetchval("SELECT prefix FROM prefixes WHERE serverid = $1", message.guild.id)
            if prefix:
                self.prefixes[message.guild.id] = prefix
                return commands.when_mentioned_or(self.prefixes[message.guild.id])(self, message)
            else:
                await self.db.execute(
                    "INSERT INTO prefixes(serverid,prefix) VALUES($1,$2) ON CONFLICT (serverid) DO UPDATE SET prefix = $2",
                    message.guild.id, self.default_prefix)
                self.prefixes[message.guild.id] = self.default_prefix
                return commands.when_mentioned_or(self.prefixes[message.guild.id])(self, message)

    async def try_user(self, user_id: int) -> discord.User:
        """Method to try and fetch a user from cache then fetch from API"""
        user = self.get_user(user_id)
        if not user:
            user = await self.fetch_user(user_id)
        return user.name

    def starter(self):
        """Runs the bot"""
        try:
            # dsn = os.environ['dsn'] or self.get_config('DSN')
            print("Connecting to database ...")
            pool_pg = self.loop.run_until_complete(asyncpg.create_pool(dsn=self.get_config('DSN')))
            print("Connected to PostgreSQL server!")
        except Exception as e:
            print("Could not connect to database:", e)
        else:
            print("Connecting to Discord ...")
            self.uptime = datetime.datetime.utcnow()
            self.db = pool_pg
            extensions = ['jishaku', 'cogs.useful', 'cogs.owner', 'cogs.prefixes', 'cogs.economy', 'cogs.errorhandler', 'cogs.fun', 'cogs.socket', 'cogs.utilites']
            for extension in extensions:
                self.load_extension(extension)

            # from pb https://github.com/PB4162/PB-Bot/blob/38f2f5f9944a7c5fc959eaade0faf0300a18d509/utils/classes.py
            for command in self.commands:
                self.command_list.append(str(command))
                self.command_list.extend([alias for alias in command.aliases])
                if isinstance(command, commands.Group):
                    for subcommand in command.commands:
                        self.command_list.append(str(subcommand))
                        self.command_list.extend(
                            [f"{command} {subcommand_alias}" for subcommand_alias in subcommand.aliases])
                        if isinstance(subcommand, commands.Group):
                            for subcommand2 in subcommand.commands:
                                self.command_list.append(str(subcommand2))
                                self.command_list.extend(
                                    [f"{subcommand} {subcommand2_alias}" for subcommand2_alias in subcommand2.aliases])
                                if isinstance(subcommand2, commands.Group):
                                    for subcommand3 in subcommand2.commands:
                                        self.command_list.append(str(subcommand3))
                                        self.command_list.extend(
                                            [f"{subcommand2} {subcommand3_alias}" for subcommand3_alias in
                                             subcommand3.aliases])
            # token = os.environ['token'] or self.get_config('token')
            self.run(self.get_config('token'))

    async def create_tables(self):
        """Creates the needed SQL tables for this bot"""
        await self.wait_until_ready()
        await self.db.execute("CREATE TABLE IF NOT EXISTS prefixes (serverid BIGINT PRIMARY KEY,prefix VARCHAR(50))")
        await self.db.execute("CREATE TABLE IF NOT EXISTS scoresaber (userid BIGINT PRIMARY KEY,ssid BIGINT)")
        await self.db.execute(
            "CREATE TABLE IF NOT EXISTS economy (userid BIGINT PRIMARY KEY,wallet BIGINT,bank BIGINT)")

    # https://github.com/InterStella0/stella_bot/blob/4636627b2f99b7f58260869f020e5adebb62e27d/main.py
    async def process_commands(self, message):
        """Override process_commands to call typing every invoke"""
        if message.author.bot:
            return
            
        ctx = await self.get_context(message)
        if ctx.valid:
            await ctx.trigger_typing()
        await self.invoke(ctx)

    async def close(self):
        await self.alex.close()
        self.session.close()
        await super().close()

    async def get_context(self, message: discord.Message, *, cls=None):
        """Method to override "ctx" """
        return await super().get_context(message, cls=cls or CustomContext)

    async def on_message(self, message: discord.Message):
        """Checking if someone pings the bot"""
        if message.author.bot:
            return
        if re.fullmatch(f"^(<@!?{self.user.id}>)\s*", message.content):
            try:
                server_prefix = bot.prefixes[message.guild.id]
            except KeyError:
                prefix = await bot.db.fetchval("SELECT prefix FROM prefixes WHERE serverid = $1", message.guild.id)
                if prefix:
                    server_prefix = prefix
                else:
                    server_prefix = bot.default_prefix
            await message.channel.send("My prefix on `{}` is `{}`".format(message.guild.name, server_prefix))
        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        """Check on command edit so that you don't have to retype your command"""
        if before.author.id in self.owner_ids and not before.embeds and not after.embeds:
            await self.process_commands(after)


bot = SYSTEM32()
bot.loop.create_task(bot.create_tables())

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"


@bot.event
async def on_ready():
    """Lets you know that the bot has run"""
    print(
        f'{bot.user} has connected to Discord!\nGuilds: {len(bot.guilds)}\nMembers: {str(sum([guild.member_count for guild in bot.guilds]))}')


if __name__ == "__main__":
    bot.starter()
