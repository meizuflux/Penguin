from discord.ext import commands
from utils.blackjack import Blackjack


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def blackjack(self, ctx):
        """Play a game of blackjack."""
        bj = Blackjack(ctx)
        await bj.start()


def setup(bot):
    bot.add_cog(Casino(bot))
