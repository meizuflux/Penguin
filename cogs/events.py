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

import json

import discord
from discord.ext import commands, tasks


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
        self.bot.prefixes.pop(guild.id, None)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.db.execute("INSERT INTO guilds (guild_id) VALUES ($1)", guild.id)
        await self.bot.db.execute(
            "INSERT INTO prefixes(guild_id,prefix) VALUES($1,$2)",
            guild.id, self.bot.default_prefix)
        self.bot.prefixes[guild.id].append(self.bot.default_prefix)

    @tasks.loop(minutes=5)
    async def change_presence(self):
        await self.bot.wait_until_ready()
        if self.activity_type == 1:
            name = f"{len(self.bot.guilds)} servers | {len(self.bot.users)} users"

            activity = discord.Activity(type=discord.ActivityType.watching, name=name)
            await self.bot.change_presence(activity=activity)
            self.activity_type = 0
            return

        if self.activity_type == 0:
            name = f"@{self.bot.user.name}"
            activity = discord.Activity(type=discord.ActivityType.listening, name=name)

            await self.bot.change_presence(activity=activity)
            self.activity_type = 1
            return

    @tasks.loop(minutes=10)
    async def top_gg(self):
        await self.bot.wait_until_ready()
        payload = {
            'server_count': len(self.bot.guilds)
        }

        headers = {
            'User-Agent': f"Walrus Discord Bot ({self.bot.user.id})",
            'Content-Type': 'application/json',
            'Authorization': self.bot.settings['keys']['top_gg']
        }

        api_url = "https://top.gg/api"

        async with self.bot.session.post(api_url + "/bots/stats", json=json.dumps(payload, ensure_ascii=True), headers=headers):
            return


def setup(bot):
    bot.add_cog(Events(bot))
