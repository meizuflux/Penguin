import discord
from discord.ext import commands
from cogs.polaroid_manipulation import get_image_url
import typing


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def amiajoke(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member, discord.User, str] = None):
        embed = ctx.embed()
        embed.set_image(url='attachment://yes_you_are.png')
        image = discord.File(await (await self.bot.alex.amiajoke(await get_image_url(ctx, image))).read(), "yes_you_are.png")
        await ctx.send(embed=embed, file=image)
    

def setup(bot):
    bot.add_cog(Images(bot))