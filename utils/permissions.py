"""
Custom permissions.
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

from discord.ext import commands


def mng_msg():
    def predicate(ctx):
        if ctx.author.id in ctx.bot.owner_ids:
            return True
        if ctx.guild:
            if ctx.author.guild_permissions.manage_messages:
                return True
        else:
            return False

    return commands.check(predicate)


def mng_gld():
    def predicate(ctx):
        if ctx.author.id in ctx.bot.owner_ids:
            return True
        return bool(ctx.author.guild_permissions.manage_guild)

    return commands.check(predicate)
