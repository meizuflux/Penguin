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

    @commands.command()
    async def hug(self, ctx):
        await self.send_waifu(ctx, "hug")

    @commands.command()
    async def awoo(self, ctx):
        await self.send_waifu(ctx, "awoo")

    @commands.command()
    async def kiss(self, ctx):
        await self.send_waifu(ctx, "kiss")

    @commands.command()
    async def lick(self, ctx):
        await self.send_waifu(ctx, "lick")

    @commands.command()
    async def pat(self, ctx):
        await self.send_waifu(ctx, "pat")

    @commands.command()
    async def smug(self, ctx):
        await self.send_waifu(ctx, "smug")

    @commands.command()
    async def bonk(self, ctx):
        await self.send_waifu(ctx, "bonk")

    @commands.command()
    async def yeet(self, ctx):
        await self.send_waifu(ctx, "yeet")

    @commands.command()
    async def blush(self, ctx):
        await self.send_waifu(ctx, "blush")

    @commands.command()
    async def smile(self, ctx):
        await self.send_waifu(ctx, "smile")

    @commands.command()
    async def wave(self, ctx):
        await self.send_waifu(ctx, "wave")

    @commands.command()
    async def highfive(self, ctx):
        await self.send_waifu(ctx, "highfive")

    @commands.command()
    async def handhold(self, ctx):
        await self.send_waifu(ctx, "handhold")

    @commands.command()
    async def nom(self, ctx):
        await self.send_waifu(ctx, "nom")

    @commands.command()
    async def bite(self, ctx):
        await self.send_waifu(ctx, "bite")

    @commands.command()
    async def glomp(self, ctx):
        await self.send_waifu(ctx, "glomp")

    @commands.command()
    async def kill(self, ctx):
        await self.send_waifu(ctx, "kill")

    @commands.command()
    async def slap(self, ctx):
        await self.send_waifu(ctx, "slap")

    @commands.command()
    async def happy(self, ctx):
        await self.send_waifu(ctx, "happy")

    @commands.command()
    async def wink(self, ctx):
        await self.send_waifu(ctx, "wink")

    @commands.command()
    async def poke(self, ctx):
        await self.send_waifu(ctx, "poke")

    @commands.command()
    async def dance(self, ctx):
        await self.send_waifu(ctx, "dance")

    @commands.command()
    async def cringe(self, ctx):
        await self.send_waifu(ctx, "cringe")

def setup(bot):
    bot.add_cog(AnimePics(bot))
    cog = bot.get_cog('AnimePics')
    for command in cog.get_commands():
        command.help = f"Sends a {command.qualified_name}"
