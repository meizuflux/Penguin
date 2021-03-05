from discord.ext import commands

from utils.default import qembed
from utils.permissions import mng_gld


class Prefixes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self.bot.db.execute("DELETE FROM prefixes WHERE serverid = $1", guild.id)
        self.bot.prefixes[guild.id] = self.bot.default_prefix

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self.bot.db.execute(
            "INSERT INTO prefixes(serverid,prefix) VALUES($1,$2) ON CONFLICT (serverid) DO UPDATE SET prefix = $2",
            guild.id, self.bot.default_prefix)
        self.bot.prefixes.pop(guild.id, None)

    @commands.command(aliases=['changeprefix', 'setprefix'])
    @mng_gld()
    async def prefix(self, ctx, prefix):
        await self.bot.db.execute(
            "INSERT INTO prefixes(serverid,prefix) VALUES($1,$2) ON CONFLICT (serverid) DO UPDATE SET prefix = $2",
            ctx.guild.id, prefix)
        self.bot.prefixes[ctx.guild.id] = prefix
        await qembed(ctx, f"Changed prefix to `{prefix}`")


def setup(bot):
    bot.add_cog(Prefixes(bot))
