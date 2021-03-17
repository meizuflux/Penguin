import discord
from discord.ext import commands
from cogs.polaroid_manipulation import get_image_url
import typing

NEKOBOT_URL = 'https://nekobot.xyz/api'

class Images(commands.Cog):
    """Some fun image commands."""
    def __init__(self, bot):
        self.bot = bot

    async def do_alex_image(self, ctx, method, args: list = [], kwargs: dict = {}):
        alex = getattr(self.bot.alex, method)
        m = await alex(*args, **kwargs)
        file = discord.File(await m.read(), filename=f"{method}.png")
        embed = ctx.embed()
        embed.set_image(url=f"attachment://{method}.png")
        await ctx.send(embed=embed, file=file)

    async def do_neko_image(self, ctx, endpoint, key='message'):
        async with self.bot.session.get(NEKOBOT_URL + endpoint) as resp:
            data = await resp.json()
        embed = ctx.embed().set_image(url=data[key])
        await ctx.send(embed=embed)

    @commands.command()
    async def amiajoke(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member, discord.User, str] = None):
        """Creates a "Am I a joke?" meme."""
        await self.do_alex_image(ctx, method="amiajoke", args=[await get_image_url(ctx, image)])

    @commands.command()
    async def animeface(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member, discord.User, str] = None):
        """Detects the anime faces in an image.
        Best to provide one, avatars don't really work great."""
        await self.do_neko_image(ctx, endpoint="/imagegen?type=animeface&image=%s" % await get_image_url(ctx, image))

    @commands.command()
    async def trumptweet(self, ctx, *, text: str):
        """Generates a tweet from the one and only."""
        await self.do_neko_image(ctx, endpoint="/imagegen?type=trumptweet&text=%s" % text)

    @commands.command()
    async def baguette(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member, discord.User, str] = None):
        """Generates a tweet from the one and only."""
        await self.do_neko_image(ctx, endpoint="/imagegen?type=baguette&url=%s" % await get_image_url(ctx, image))

    @commands.command()
    async def clyde(self, ctx, *, text):
        """Generates a message from clyde."""
        await self.do_neko_image(ctx, endpoint="/imagegen?type=clyde&text=%s" % text)


def setup(bot):
    bot.add_cog(Images(bot))