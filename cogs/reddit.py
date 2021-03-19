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
        await self.create_message(ctx, 'me_irl', min=2)

    @commands.command()
    async def dankmeme(self, ctx):
        """Sends a dank meme. 😎"""
        await self.create_message(ctx, 'dankmemes', min=1)

    @commands.command()
    async def meme(self, ctx):
        """Sends a meme. Worse version of dankmeme"""
        await self.create_message(ctx, 'memes', min=1)

    @commands.command()
    async def programming(self, ctx):
        """Sends a meme. Worse version of dankmeme"""
        await self.create_message(ctx, 'programmerhumor', min=1)


def setup(bot):
    bot.add_cog(Reddit(bot))
