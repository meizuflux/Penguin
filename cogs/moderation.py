import discord
from discord.ext import commands
import contextlib


class Target(commands.Converter):
    async def convert(self, ctx, argument) -> discord.Member:
        user = await commands.MemberConverter().convert(ctx, argument)

        if ctx.author == ctx.guild.owner:
            return user

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

class Reason(commands.Converter):
    async def convert(self, ctx, argument):

        default = f"{str(ctx.author)}: {argument}"

        if len(default) > 500:
            raise commands.BadArgument("The provided reason is too long")
        
        return default


class Moderation(commands.Cog):
    def __init(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: Target, reason: Reason="No reason"):
        with contextlib.suppress((discord.Forbidden, discord.HTTPException)):
            await member.send(f"You have been kicked from {ctx.guild.name}.\n{reason}")
        await ctx.guild.kick(member, reason=reason)
        await ctx.send
        
        
def setup(bot):
    bot.add_cog(Moderation(bot))
