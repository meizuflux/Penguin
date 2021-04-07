"""
Creates cache, and sets up all the variables and runs the bot.
Copyright (C) 2021 ppotatoo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import collections
import datetime
import os
import re

import aiohttp
import alexflipnote
import asyncpg
import discord
import toml
from discord.ext import commands

from utils import create_logger
from utils.default import Blacklisted, Maintenance

logger = create_logger("Walrus")

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def get_prefix(bot, message):
    """Function for getting the command prefix."""
    if not message.guild:
        return commands.when_mentioned_or(bot.default_prefix)(bot, message)

    if bot.prefixes[message.guild.id]:
        return commands.when_mentioned_or(*bot.prefixes[message.guild.id])(bot, message)

    bot.prefixes[message.guild.id].append(bot.default_prefix)
    return commands.when_mentioned_or(*bot.prefixes[message.guild.id])(bot, message)


class Walrus(commands.Bot):
    """Custom bot."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()

        # Base variables for core functionality
        with open("config.toml") as f:
            self.settings = toml.loads(f.read())
        self.session = aiohttp.ClientSession()
        self.embed_color = 0x89CFF0

        self.support_invite = self.settings['misc']['support_server_invite']
        self.invite = self.settings['misc']['invite']

        # Cache so I don't have to use DB
        self.prefixes = collections.defaultdict(list)
        self.default_prefix = "p!"
        self.command_list = []
        self.afk = {}
        self.highlights = {}
        self.blacklist = {}
        self.usage_counter = 0
        self.command_usage = collections.Counter()

        # Webhooks
        self.error_webhook = discord.Webhook.from_url(
            self.settings["misc"]["error_webhook"],
            adapter=discord.AsyncWebhookAdapter(self.session)
        )
        self.guild_webhook = discord.Webhook.from_url(
            self.settings["misc"]["guild_webhook"],
            adapter=discord.AsyncWebhookAdapter(self.session)
        )

        # API stuff
        self.alex = alexflipnote.Client(self.settings['keys']['alexflipnote'])
        self.perspective = self.settings['keys']['perspective']

        # Bot management
        self.maintenance = False
        self.context = commands.Context

    async def try_user(self, user_id: int) -> discord.User:
        """Method to try and fetch a user from cache then fetch from API."""
        user = self.get_user(user_id)
        if not user:
            user = await self.fetch_user(user_id)
        return user

    def embed(self, ctx, **kwargs):
        color = kwargs.pop("color", self.embed_color)
        embed = discord.Embed(**kwargs, color=color)
        embed.timestamp = ctx.message.created_at
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        return embed

    def run(self, *args, **kwargs):
        """Runs the bot."""
        try:
            pool_pg = self.loop.run_until_complete(asyncpg.create_pool(dsn=self.settings['tokens']['dsn']))
            logger.info("Connected to database")
        except Exception as e:
            logger.error("Could not connect to database: %s", e)
        else:
            self.db = pool_pg

            for file in os.listdir("exts"):
                if not file.startswith("_"):
                    self.load_extension(f'exts.{file[:-3]}')
            self.load_extension("jishaku")
            logger.info("Loaded extensions")

            self.create_command_list()

            self.start_time = datetime.datetime.utcnow()
            super().run(*args, **kwargs)

    async def prep(self):
        await self.wait_until_ready()
        with open("schema.sql") as f:
            await self.db.execute(f.read())

        self.mention_match = re.compile(fr"^(<@!?{self.user.id}>)\s*")

        for guild in self.guilds:
            await self.db.execute("INSERT INTO guilds VALUES ($1) ON CONFLICT (guild_id) DO NOTHING", guild.id)

        for guild in await self.db.fetch("SELECT guild_id, prefix FROM prefixes"):
            self.prefixes[guild['guild_id']].append(guild['prefix'])

        self.blacklist = dict(await self.db.fetch('SELECT user_id, reason FROM blacklist'))

        logger.info("Created cache")

    def create_command_list(self):
        for command in self.commands:
            self.command_list.append(str(command))
            self.command_list.extend(list(command.aliases))
            if isinstance(command, commands.Group):
                self.command_list.extend(self.get_subcommands(command))

    def get_subcommands(self, command):
        gotten_subcommands = []
        for command in command.commands:
            gotten_subcommands.append(str(command))
            gotten_subcommands.extend([f"{command} {alias}" for alias in command.aliases])
            if isinstance(command, commands.Group):
                gotten_subcommands.extend(self.get_subcommands(command))
        return gotten_subcommands

    async def close(self):
        await self.alex.close()
        await self.session.close()
        await self.db.close()
        await super().close()

    async def get_context(self, message: discord.Message, *, cls=None):
        """Method to override "ctx"."""
        return await super().get_context(message, cls=cls or self.context)

    # https://github.com/InterStella0/stella_bot/blob/4636627b2f99b7f58260869f020e5adebb62e27d/main.py
    async def process_commands(self, message):
        """Override process_commands to call typing every invoke"""
        if message.author.bot:
            return

        ctx = await self.get_context(message)
        if ctx.valid:
            await ctx.trigger_typing()
        await self.invoke(ctx)

    async def on_message(self, message: discord.Message):
        """Checking if someone pings the bot."""
        perms = message.channel.permissions_for(message.guild.me).send_messages + message.channel.permissions_for(
            message.guild.me).embed_links if message.guild else 2
        if message.author.bot or not self.is_ready() or perms != 2:
            return
        if self.mention_match.fullmatch(message.content):
            ctx = await self.get_context(message)
            prefix_command = self.get_command("prefix all")

            await prefix_command(ctx)

        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        """Check on command edit so that you don't have to retype your command."""
        if before.author.id in self.owner_ids and before.content != after.content:
            await self.process_commands(after)

    async def on_ready(self):
        logger.info(f"Connected to Discord -> {str(self.user)}")
        logger.info(f"Guilds -> {len(self.guilds)}")
        logger.info(f"Commands -> {len(set(self.walk_commands()))}")


intents = discord.Intents.default()
intents.members = True
intents.integrations = False
intents.webhooks = False
intents.invites = False
intents.voice_states = False
intents.typing = False

flags = discord.MemberCacheFlags.from_intents(intents)

bot = Walrus(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    member_cache_flags=flags,
    max_messages=250,
    owner_ids={809587169520910346},
    description="Walrus is a simple and easy-to-use Discord bot"
)
bot.loop.create_task(bot.prep())

os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'
os.environ['JISHAKU_HIDE'] = 'True'
os.environ["NO_COLOR"] = 'True'


@bot.check
async def is_maintenance(ctx):
    if bot.maintenance and not await ctx.bot.is_owner(ctx.author):
        raise Maintenance()
    return True


@bot.check
async def is_blacklisted(ctx):
    if ctx.author.id in bot.blacklist:
        raise Blacklisted()
    return True

if __name__ == "__main__":
    bot.run(bot.settings['tokens']['bot'])
