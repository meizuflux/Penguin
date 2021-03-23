import discord
from discord.ext import commands


class TargetUser(commands.Converter):
    async def convert(self, ctx, argument) -> discord.Member:
        user = await commands.MemberConverter().convert(ctx, argument)

        if user.top_role >= ctx.me.top_role:
            raise commands.BadArgument("This members top role is higher than or equal to my top role.")

        if user.top_role >= ctx.author.top_role:
            raise commands.BadArgument("This members top role is higher than or equal to your top role.")

        if user == ctx.author:
            raise commands.BadArgument(f"You can't {ctx.invoked_with} yourself.")

        if user == ctx.me:
            raise commands.BadArgument("The bot can't take action against itself.")

        if user == ctx.guild.owner:
            raise commands.BadArgument(f"You can't {ctx.invoked_with} the server owner.")
        return user

class ModReason(commands.Converter):
    async def convert(self, ctx, argument) -> str:
        if arguemnt is none: raise commands.BadArgument("test")

class Moderation(commands.Cog):
    def __init(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, idk: ModReason=None):
        await ctx.send(idk)
        
def setup(bot):
    bot.add_cog(Moderation(bot))
