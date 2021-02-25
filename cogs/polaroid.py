import discord
from discord.ext import commands
from jishaku.functools import executor_function
import polaroid
import typing


class Polaroid(commands.Cog, command_attrs=dict(hidden=False)):
    def __init__(self, bot):
        self.bot = bot

    @executor_function
    async def image_manip(self, ctx, image,*, method: str, *args: list = None, **kwargs):
        async with ctx.typing():
            if ctx.message.attachments:
                img = polaroid.Image(await ctx.message.attachments[0].read())
            elif isinstance(image, discord.PartialEmoji):
                img = polaroid.Image(await image.url.read())
            else:
                img = image or ctx.author
                img = polaroid.Image(await
                                     img.avatar_url_as(format="png").read())

            img.resize(500, 500, 1)
            method = getattr(img, method)
            method(*args, **kwargs)
            file = discord.File(BytesIO(img.save_bytes()),
                                filename=f"{method}.png")

            embed = discord.Embed(description=text,
                                  colour=self.bot.embed_color,
                                  timestamp=ctx.message.created_at)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            embed.set_image(url=f"attachment://{method}.png")
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed, file=file)

    @commands.command(help='Makes an image rainbowey')
    async def rainbow(self, ctx, *, image: typing.Union[discord.PartialEmoji, discord.Member] = None):
        await self.manip(ctx, image, method='apply_gradient')

def setup(bot):
    bot.add_cog(Polaroid(bot))