"""
Couple of useful functions.
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
from discord.ext import commands


async def qembed(ctx, text):
    bot = ctx.bot
    embed = discord.Embed(description=text[:2048], color=bot.embed_color, timestamp=ctx.message.created_at).set_footer(
        text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)


class Maintenance(commands.CheckFailure):
    pass


class Blacklisted(commands.CheckFailure):
    pass
