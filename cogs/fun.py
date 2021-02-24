import discord
from discord.ext import commands, flags
from io import BytesIO
from utils.default import qembed


class Fun(commands.Cog):
    """For the fun commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='Sends a cat for every error code', aliases=['httpcat', 'http_cat'])
    async def http(self, ctx, code=404):
        async with self.bot.session.get(
                f"https://http.cat/{code}") as resp:
            buffer = await resp.read()
        embed = discord.Embed(colour=self.bot.embed_color, timestamp=ctx.message.created_at)
        embed.set_image(url=f"attachment://{code}.png")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed, file=discord.File(BytesIO(buffer), filename=f"{code}.png"))

    @flags.add_flag("--dark", action='store_true', default=False)
    @flags.add_flag("--light", action='store_true', default=False)
    @flags.command(usage='"supreme" [--dark|--light]')
    async def supreme(self, ctx, text="supreme", **flags):
        """Makes a custom supreme logo
        example: supreme --text "hey guys" --dark"""
        if flags["dark"] and flags["light"]:
            return await qembed(ctx, "You can't have both dark and light, sorry.")
        image = await self.bot.alex.supreme(text=text,
                                            dark=flags["dark"],
                                            light=flags["light"])
        image_bytes = await image.read()
        file = discord.File(image_bytes, "supreme.png")
        embed = discord.Embed(colour=self.bot.embed_color,
                              timestamp=ctx.message.created_at).set_footer(
                                                                            text=f"Requested by {ctx.author}",
                                                                            icon_url=ctx.author.avatar_url)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_image(url="attachment://supreme.png")

        await ctx.send(embed=embed, file=file)

    @commands.command(help='Replaces the spaces in a string with a character')
    async def replacespace(self, ctx, char, *, text):
        await qembed(ctx, text.replace(' ', f' {char} '))

    @commands.command(help='Reverses some text')
    async def reverse(self, ctx, *, text):
        await qembed(ctx, text.replace(' ', ''.join(reversed(text))))


def setup(bot):
    bot.add_cog(Fun(bot))
