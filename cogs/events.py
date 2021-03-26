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


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activity_type = 1
        self.change_presence.start()
        
    def cog_unload(self):
        self.change_presence.cancel()

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.usage_counter += 1
        self.bot.command_usage[ctx.command.qualified_name] += 1

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

def setup(bot):
    bot.add_cog(Events(bot))
