import discord
from discord.ext import commands


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def create_message(self, ctx, subreddit: str, min: int = 1):
        async with self.bot.session.get(f'https://reddit.com/r/{subreddit}.json') as resp:
            res = await resp.json()
        data = res['data']['children'][random.randint(min, 26)]['data']
        embed = ctx.embed(title=data['title'], url=f"https://reddit.com{data['permalink']}")
        embed.set_image(url=data['url_overridden_by_dest'])
        await ctx.send(embed=embed)

    @commands.command()
    async def chonkers(self, ctx):
        await self.create_message(ctx, 'chonkers')


def setup(bot):
    bot.add_cog(Reddit(bot))
