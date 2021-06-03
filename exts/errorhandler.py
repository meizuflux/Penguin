import asyncio
import traceback

import discord
import humanize
import prettify_exceptions
from discord.ext import commands

from utils.eco import NotRegistered


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        owner_errors = (
            commands.MissingAnyRole,
            commands.MissingPermissions,
            commands.MissingRole,
            commands.CommandOnCooldown,
            commands.DisabledCommand,
        )
        if await self.bot.is_owner(ctx.author) and isinstance(error, owner_errors):
            return await ctx.reinvoke()

        if not isinstance(
            error, (commands.CommandNotFound, commands.CommandOnCooldown)
        ):
            ctx.command.reset_cooldown(ctx)

        if isinstance(error, NotRegistered):
            return await ctx.send(str(error))

        if hasattr(ctx.command, "on_error"):
            return

        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error):
            return

        ignored = (commands.CommandNotFound,)

        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        command = ctx.command.qualified_name

        if isinstance(error, commands.CheckFailure):
            if self.bot.maintenance:
                return await ctx.send(
                    embed=ctx.embed(title="⚠️ Maintenence mode is active.")
                )
            if ctx.author.id in self.bot.blacklist:
                reason = self.bot.blacklist.get(
                    ctx.author.id, "No reason, you probably did something dumb."
                )
                embed = ctx.embed(
                    title="⚠️ You are blacklisted from using this bot globally.",
                    description=(
                        f"**Blacklisted For:** {reason}"
                        f"\n\nYou can join the support server [here]({self.bot.support_invite}) "
                        f"if you feel this is a mistake."
                    ),
                )
                try:
                    await ctx.author.send(embed=embed)
                except discord.Forbidden:
                    await ctx.send(embed=embed)
                finally:
                    return

            return await ctx.send(embed=ctx.embed(description=str(error)))

        if isinstance(error, discord.Forbidden):
            return await ctx.send(
                embed=ctx.embed(
                    description=f"I do not have the correct permissions for `{command}`"
                )
            )

        if isinstance(error, commands.CommandOnCooldown):
            retry = humanize.precisedelta(error.retry_after, minimum_unit="seconds")
            cd = error.cooldown
            embed = ctx.embed(
                description=(
                    f"<a:countdown:827916388659363870> **{command}** is on cooldown. Try again in {retry}.\n"
                    f"You can use this command **{cd.rate} {ctx.plural('time(s)', cd.rate)} every {humanize.precisedelta(cd.per, minimum_unit='seconds')}.\n"
                    f"Type: {cd.type.name}"
                )
            )

            return await ctx.send(embed=embed)

        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(
                    embed=ctx.embed(
                        description=f"{ctx.invoked_with} cannot be used in DM's"
                    )
                )
            except discord.HTTPException:
                pass

        if isinstance(error, commands.MissingRequiredArgument):
            errors = str(error).split(" ", maxsplit=1)
            return await ctx.send(
                embed=ctx.embed(
                    description=(
                        f"`{errors[0]}` {errors[1]}\n"
                        f"You can view the help for this command with `{ctx.clean_prefix}help` `{command}`"
                    )
                )
            )

        if isinstance(error, commands.DisabledCommand):
            return await ctx.send(
                embed=ctx.embed(description=f"`{command}` has been disabled.")
            )

        if isinstance(error, commands.BadArgument):
            return await ctx.send(embed=ctx.embed(title=str(error)))

        if isinstance(error, asyncio.TimeoutError):
            return await ctx.send(embed=ctx.embed(description=f"{command} timed out."))

        formatted = traceback.format_exception(type(error), error, error.__traceback__)
        pretty_traceback = "".join(
            prettify_exceptions.DefaultFormatter().format_exception(
                type(error), error, error.__traceback__
            )
        )

        desc = (
            f"Command: {ctx.invoked_with}\n"
            f"Full content: {ctx.escape(ctx.message.content)}\n"
            f"Guild: {ctx.guild.name} ({ctx.guild.id})\n"
            f"Channel: {ctx.channel.name} ({ctx.channel.id})\n"
            f"User: {ctx.author.name} ({ctx.author.id})\n"
            f"Jump URL: {ctx.message.jump_url}"
        )
        embed = ctx.embed(
            title="AN ERROR OCCURED",
            url=await ctx.mystbin(pretty_traceback) + ".py",
            description=desc,
        )
        await self.bot.error_webhook.send(
            f"```py\n{''.join(formatted)}```", embed=embed
        )

        await ctx.send(
            f"Oops, an error occured. Here's some info on it:" f"```py\n{error}\n```"
        )


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
