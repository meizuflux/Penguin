import discord
from discord.ext import commands

BASE_URL = 'https://waifu.pics/api/sfw/'

class AnimePics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_waifu(self, ctx, category):
        async with self.bot.session.get(BASE_URL + category) as resp:
            waifu = await resp.json()
        await ctx.send(embed=ctx.embed().set_image(url=waifu.get('url')))

    @commands.command()
    async def waifu(self, ctx):
        await self.send_waifu(ctx, "waifu")

    @commands.command()
    async def neko(self, ctx):
        await self.send_waifu(ctx, "neko")

    @commands.command()
    async def shinobu(self, ctx):
        await self.send_waifu(ctx, "shinobu")

    @commands.command()
    async def megumin(self, ctx):
        await self.send_waifu(ctx, "megumin")

    @commands.command()
    async def bully(self, ctx):
        await self.send_waifu(ctx, "bully")

    @commands.command()
    async def cuddle(self, ctx):
        await self.send_waifu(ctx, "cuddle")

    @commands.command()
    async def cry(self, ctx):
        await self.send_waifu(ctx, "cry")


def setup(bot):
    bot.add_cog(AnimePics(bot))
    cog = bot.get_cog('AnimePics')
    for command in cog.get_commands():
        command.help = f"Sends a {command.qualified_name}"
