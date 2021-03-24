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


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_message(self, ctx, subreddit: str, minimum: int = 1):
        async with self.bot.session.get(f'https://reddit.com/r/{subreddit}.json') as resp:
            res = await resp.json()
        data = res['data']['children'][random.randint(minimum, 26)]['data']
        embed = ctx.embed(title=data['title'], url=f"https://reddit.com{data['permalink']}")
        url = data['url_overridden_by_dest']
        if data['url'].startswith('https://imgur.com/'):
            url = data['url']
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @commands.command()
    async def chonkers(self, ctx):
        """Sends a random post from the subreddit "Chonkers"."""
        await self.create_message(ctx, 'chonkers')

    @commands.command()
    async def me_irl(self, ctx):
        """Sends a random post from the subreddit "me_irl"."""
        await self.create_message(ctx, 'me_irl', minimum=2)

    @commands.command()
    async def dankmeme(self, ctx):
        """Sends a dank meme. 😎"""
        await self.create_message(ctx, 'dankmemes')

    @commands.command()
    async def meme(self, ctx):
        """Sends a meme. Worse version of dankmeme"""
        await self.create_message(ctx, 'memes')

    @commands.command()
    async def programming(self, ctx):
        """Sends a meme. Worse version of dankmeme"""
        await self.create_message(ctx, 'programmerhumor')


def setup(bot):
    bot.add_cog(Reddit(bot))
