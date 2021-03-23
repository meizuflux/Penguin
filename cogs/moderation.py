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

def get_reason(ctx, argument):
    if not argument: argument = "No reason."
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
    @commands.guild_only()
    async def kick(self, ctx, member: Target, *, reason=None):
        reason = get_reason(ctx, reason)
        with contextlib.suppress((discord.Forbidden, discord.HTTPException)):
            await member.send(f"You have been kicked from **{ctx.guild.name}**.\n**{reason}**")
        await ctx.guild.kick(member, reason=reason)
        await ctx.message.add_reaction("<:check:314349398811475968>")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, member: Target, *, reason=None):
        reason = get_reason(ctx, reason)
        with contextlib.suppress((discord.Forbidden, discord.HTTPException)):
            await member.send(f"You have been banned from **{ctx.guild.name}**.\n**{reason}**")
        await ctx.guild.ban(member, reason=reason)
        await ctx.message.add_reaction("<:check:314349398811475968>")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def softban(self, ctx, member: Target, *, reason=None):
        reason = get_reason(ctx, reason)
        with contextlib.suppress((discord.Forbidden, discord.HTTPException)):
            await member.send(f"You have been soft banned from **{ctx.guild.name}**.\n**{reason}**")
        await ctx.guild.ban(member, reason=reason)
        await ctx.guild.unban(member, reason=f"Softban by {ctx.author}")
        await ctx.message.add_reaction("<:check:314349398811475968>")


    @commands.group(name="remove")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _remove(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    async def do_remove(self, ctx, limit, check):
        if limit > 2000:
            raise commands.BadArgument("Limit must be under 2000.")

        try:
            deleted = await ctx.channel.purge(limit=limit, check=check)
        except discord.HTTPException as e:
            return await ctx.send(embed=ctx.embed(title='Looks like Discord is having some issues.', description=e))
        await ctx.send(embed=ctx.embed(title=f"Successfully deleted {len(deleted)} messages"))

    @_remove.command()
    async def messages(self, ctx, limit=100):
        await self.do_remove(ctx, limit, lambda p: True)

    @_remove.command(aliases=['member'])
    async def user(self, user: discord.Member, limit=100):
        await self.do_remove(ctx, limit, lambda m: m.author == user)

    
        

def setup(bot):
    bot.add_cog(Moderation(bot))
