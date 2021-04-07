"""
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

import discord
from discord.ext import commands, tasks

import utils

logger = utils.create_logger("Events")


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activity_type = 1
        self.change_presence.start()
        self.top_gg.start()

    def cog_unload(self):
        self.change_presence.cancel()
        self.top_gg.cancel()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.usage_counter += 1
        self.bot.command_usage[ctx.command.qualified_name] += 1

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.db.execute("DELETE FROM guilds WHERE guild_id = $1", guild.id)
        del self.bot.prefixes[guild.id]

        stats = (
            f"Name: {guild.name}\n"
            f"Owner: {guild.owner}\n"
            f"Boosts: {guild.premium_subscription_count}\n"
            f"Members: {len(tuple(i for i in guild.members if not i.bot))}\n"
            f"Bots: {len(tuple(i for i in guild.members if i.bot))}"
        )

        message = (
            "I got kicked from a server:\n"
            f"```yaml\n{stats}```"
        )
        await self.bot.guild_webhook.send(message)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.db.execute("INSERT INTO guilds (guild_id) VALUES ($1)", guild.id)
        await self.bot.db.execute("INSERT INTO prefixes VALUES($1,$2)", guild.id, self.bot.default_prefix)
        self.bot.prefixes[guild.id].append(self.bot.default_prefix)

        stats = (
            f"Name: {guild.name}\n"
            f"Owner: {guild.owner}\n"
            f"Boosts: {guild.premium_subscription_count}\n"
            f"Members: {len(tuple(i for i in guild.members if not i.bot))}\n"
            f"Bots: {len(tuple(i for i in guild.members if i.bot))}"
        )

        message = (
            "I joined a new server:\n"
            f"```yaml\n{stats}```"
        )
        await self.bot.guild_webhook.send(message)

    @tasks.loop(minutes=5)
    async def change_presence(self):
        await self.bot.wait_until_ready()
        if self.activity_type == 1:
            name = f"{len(self.bot.guilds)} servers | {len(self.bot.users)} users"
            activity = discord.Activity(type=discord.ActivityType.watching, name=name)
            await self.bot.change_presence(activity=activity)

            self.activity_type = 0
            logger.info(f"Set presence to Watching")

            return  # need to return otherwise it just triggers the next if statement

        if self.activity_type == 0:
            name = f"@{self.bot.user.name}"
            activity = discord.Activity(type=discord.ActivityType.listening, name=name)
            await self.bot.change_presence(activity=activity)

            self.activity_type = 1
            logger.info(f"Set presence to Listening")

            return

    @tasks.loop(minutes=10)
    async def top_gg(self):
        await self.bot.wait_until_ready()
        try:
            payload = {
                'server_count': len(self.bot.guilds)
            }

            headers = {
                'Authorization': self.bot.settings['keys']['top_gg']
            }

            url = "https://top.gg/api/bots/810570659968057384/stats"
            await self.bot.session.post(url=url, headers=headers, data=payload)
            logger.info("Posted stats to top.gg")
        except Exception as err:
            logger.error(f"Error when posting guild count: {err}")


def setup(bot):
    bot.add_cog(Events(bot))


def teardown(bot):
    logger = None

