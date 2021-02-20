import discord
from discord.ext import commands
from io import BytesIO


class Fun(commands.cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='Sends a cat for every error code', aliases=['httpcat', 'http_cat'])
    async def http(self, ctx, code=404):
        async with self.bot.session.get(
                f"https://http.cat/{code}") as resp:
            buffer = await resp.read()
        await ctx.send(
            file=discord.File(BytesIO(buffer), filename=f"{code}.png"))


def setup(bot):
    bot.add_cog(Fun(bot))
