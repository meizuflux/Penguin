import discord
from discord.ext import commands
from cogs.polaroid_manipulation import get_image_url
import typing


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def do_alex_image(self, ctx, method, args: list = [], kwargs: dict = {}):
        alex = getattr(self.bot.alex, method)
        m = await alex(*args, **kwargs)
        file = discord.File(m, filename=f"{method}.png")
        embed = ctx.embed()
        embed.set_image(url=f"attachment://{method}.png")
        await ctx.send(embed=embed, file=file)

    @commands.command()
    async def amiajoke(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member, discord.User, str] = None):
        await self.do_alex_image(ctx, method="amiajoke", args=[await get_image_url(ctx, image)])
    

def setup(bot):
    bot.add_cog(Images(bot))