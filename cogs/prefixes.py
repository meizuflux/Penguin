from discord.ext import commands

from utils.default import qembed
from utils.permissions import mng_gld


class Prefixes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        self.bot.prefixes[guild.id] = self.bot.default_prefix

    @commands.group()
    async def prefix(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @prefix.command()
    @mng_gld()
    async def add(self, ctx, prefix):
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
        if ctx.prefix == f"<@{self.bot.user.id}>":
            return await ctx.send(embed=ctx.embed(description="Nice try."))

def setup(bot):
    bot.add_cog(Prefixes(bot))
