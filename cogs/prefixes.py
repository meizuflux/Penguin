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

from discord.ext import commands

from utils.permissions import mng_gld


class Prefixes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def prefix(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @prefix.command()
    @mng_gld()
    async def add(self, ctx, prefix):
        if prefix in self.bot.prefixes[ctx.guild.id]:
            return await ctx.send(embed=ctx.embed(description="This is already a prefix."))

        sql = (
            "INSERT INTO prefixes(guild_id,prefix) "
            "VALUES($1,$2) "
            "ON CONFLICT (guild_id, prefix) DO NOTHING"
        )

        await self.bot.db.execute(sql, ctx.guild.id, prefix)
        self.bot.prefixes[ctx.guild.id].append(prefix)
        await ctx.send(embed=ctx.embed(description=f"Added prefix `{prefix}`"))

    @prefix.command()
    @mng_gld()
    async def remove(self, ctx, prefix):
        if prefix not in self.bot.prefixes[ctx.guild.id]:
            return await ctx.send(embed=ctx.embed(description="Invalid prefix provided."))
        sql = (
            "DELETE FROM prefixes "
            "WHERE guild_id = $1 AND prefix = $2"
        )
        await self.bot.db.execute(sql, ctx.guild.id, prefix)
        self.bot.prefixes[ctx.guild.id].remove(prefix)
        await ctx.send(embed=ctx.embed(description=f"Removed `{prefix}`"))

    @prefix.command()
    @mng_gld()
    async def edit(self, ctx, prefix):
        """Edits the prefix being used to invoke the command."""
        if str(ctx.prefix).strip().replace('!', '') == self.bot.user.mention:
            return await ctx.send(embed=ctx.embed(description="You can't edit this. You can add a new prefix, but you can't delete the mention as a prefix."))
        insertion_sql = (
            "INSERT INTO prefixes (guild_id, prefix) "
            "VALUES ($1, $2) ON CONFLICT (guild_id, prefix) DO UPDATE SET prefix = $2"
        )
        await self.bot.db.execute(insertion_sql, ctx.guild.id, prefix)
        self.bot.prefixes[ctx.guild.id].remove(ctx.prefix)
        self.bot.prefixes[ctx.guild.id].append(prefix)
        await ctx.send(embed=ctx.embed(description=f"Edited `{ctx.prefix}` to `{prefix}`"))

    @prefix.command()
    async def all(self, ctx):
        """View the prefixes on this server."""
        prefixes = '"\n"'.join(self.bot.prefixes[ctx.guild.id])
        embed = ctx.embed(title=f"{ctx.plural('Prefix(s)', len(self.bot.prefixes[ctx.guild.id]))} on {ctx.guild.name}",
                          description=f'```yaml\n"{prefixes}"```')
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Prefixes(bot))
