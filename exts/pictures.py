"""
Copyright (C) 2021 ppotatoo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import random

from discord.ext import commands

WAIFU_URL = 'https://waifu.pics/api/sfw/'
PURRBOT_URL = "https://purrbot.site/api"


class Pictures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_waifu(self, ctx, category):
        async with self.bot.session.get(WAIFU_URL + category) as resp:
            waifu = await resp.json()
        await ctx.send(embed=ctx.embed().set_image(url=waifu.get('url')))

    async def send_purr(self, ctx, endpoint):
        async with self.bot.session.get(PURRBOT_URL + endpoint) as resp:
            purr = await resp.json()
        await ctx.send(embed=ctx.embed().set_image(url=purr.get('link')))

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

    @commands.command()
    async def eevee(self, ctx):
        """Sends a random picture of Eevee."""
        types = ['gif', 'img']
        await self.send_purr(ctx, f"/img/sfw/eevee/{random.choice(types)}")

    @commands.command()
    async def feed(self, ctx):
        """Sends a random feeding gif."""
        await self.send_purr(ctx, "/img/sfw/feed/gif")

    @commands.command()
    async def holo(self, ctx):
        """Sends a random Image of Holo (Spice & Wolf)."""
        await self.send_purr(ctx, "/img/sfw/holo/img")

    @commands.command()
    async def icon(self, ctx):
        """Sends a random welcome icon."""
        await self.send_purr(ctx, "/img/sfw/icon/img")

    @commands.command()
    async def kitsune(self, ctx):
        """Sends a random Image of a Kitsune (Fox girl)."""
        await self.send_purr(ctx, "/img/sfw/kitsune/img")

    @commands.command()
    async def nekogif(self, ctx):
        """Sends a random neko gif."""
        await self.send_purr(ctx, "/img/sfw/neko/gif")

    @commands.command()
    async def senko(self, ctx):
        """Sends a rrandom Image of Senko-San"""
        await self.send_purr(ctx, "/img/sfw/senko/img")

    @commands.command()
    async def tickle(self, ctx):
        """Sends a rrandom tickle gif."""
        await self.send_purr(ctx, "/img/sfw/tickle/gif")


def setup(bot):
    bot.add_cog(Pictures(bot))
    cog = bot.get_cog('Pictures')
    for command in cog.get_commands():
        if not command.help:
            command.help = f"Sends a {command.qualified_name}."
