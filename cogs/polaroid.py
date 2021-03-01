import discord
from discord.ext import commands
from jishaku.functools import executor_function
import polaroid
import typing
from io import BytesIO


class Polaroid(commands.Cog, command_attrs=dict(hidden=False)):
    def __init__(self, bot):
        self.bot = bot

    async def get_image(self, ctx, image):
        if ctx.message.attachments:
            img = polaroid.Image(await ctx.message.attachments[0].read())
        elif isinstance(image, discord.PartialEmoji):
            img = polaroid.Image(await image.url.read())
        else:
            img = image or ctx.author
            img = polaroid.Image(await img.avatar_url_as(format="png").read())
        return img

    @executor_function
    def image_manip(self, ctx, img: polaroid.Image, method: str, args: list = None, kwargs: dict = None):
        img.resize(500, 500, 1)
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        method = getattr(img, method)
        method(*args, **kwargs)
        return img

    async def send_manip(self, ctx, image, method: str, *args, **kwargs):
        await ctx.trigger_typing()
        image = await self.get_image(ctx, image)
        img = await self.image_manip(ctx, image, method, *args, **kwargs)
        file = discord.File(BytesIO(img.save_bytes()),
                            filename=f"{method}.png")

        embed = discord.Embed(colour=self.bot.embed_color,
                              timestamp=ctx.message.created_at)
        embed.set_image(url=f"attachment://{method}.png")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed, file=file)

    @commands.command(help='Makes an image rainbowey')
    async def rainbow(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='apply_gradient')

    @commands.command(help='like putin')
    async def wide(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='resize', args=(2000, 900, 1))

    @commands.command(help='Inverts an image')
    async def invert(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='invert')

    @commands.command(help='It\'s like looking in a mirror')
    async def flip(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='fliph')

    @commands.command(help='Blurs an image? Duh')
    async def blur(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='box_blur')

    @commands.command(help='cursed')
    async def sobelh(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='sobel_horizontal')

    @commands.command(help='cursed')
    async def sobelv(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='sobel_vertical')

    @commands.command(help='Decomposes the image')
    async def decompose(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='decompose_max')

    @commands.command(help='Turns an image black and white')
    async def grayscale(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='grayscale')

    @commands.command(help='Solarizes an image')
    async def solarize(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='solarize')

    @commands.command(help='Rotates an image sideways')
    async def sideways(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='rotate90')

    @commands.command(help='Rotates an image upsidedown')
    async def upsidedown(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='rotate180')

    @commands.command(help='Makes an image monochrome.')
    async def monochrome(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='monochrome')

    @commands.command(help='Applies an emboss effect to an image.')
    async def emboss(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='emboss')

    @commands.group(help='Some commands that apply simple filters.')
    async def filter(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @filter.command(help='Applies a rose filter on an image.')
    async def rose(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='filter', args=["rosetint"])

    @filter.command(help='Applies a pink filter to the image.')
    async def pink(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='filter', args=["pastel_pink"])

    @filter.command(help='Applies a liquid filter to the image.')
    async def liquid(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.send_manip(ctx, image, method='filter', args=["liquid"])



def setup(bot):
    bot.add_cog(Polaroid(bot))
