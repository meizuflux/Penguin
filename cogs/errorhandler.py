import sys
import traceback

import discord
import humanize
import re
import difflib
from discord.ext import commands

from utils.fuzzy import finder
from utils.default import qembed


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        #ignored = (commands.CommandNotFound,)  # if you want to not send error messages
        ignored = ()

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandNotFound):
            failed_command = re.match(rf"^({ctx.prefix})\s*(.*)", ctx.message.content, flags=re.IGNORECASE).group(2)
            matches = finder(failed_command, self.bot.command_list)
            if not matches:
                return
            match = "\n".join(matches[:1])
            cmd = self.bot.get_command(match)
            if not await cmd.can_run(ctx):
                return
            return await qembed(ctx, f"No command called `{ctx.invoked_with}` found. Did you mean `{match}`?")

        elif isinstance(error, commands.CheckFailure):
            return await qembed(
                ctx,
                f'You do not have the correct permissions for `{ctx.invoked_with}`')

        if isinstance(error, discord.Forbidden):
            return await qembed(
                ctx,
                f'I do not have the correct permissions for `{ctx.command}`')

        elif isinstance(error, commands.CommandOnCooldown):
            return await qembed(
                ctx,
                f"This command is on cooldown.\nTry again in {humanize.precisedelta(error.retry_after, minimum_unit='seconds')}"
            )

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                e = discord.Embed(
                    description=f'`{ctx.command}` can not be used in Private Messages.',
                    color=self.bot.embed_color)
                return await ctx.author.send(embed=e)
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            return await qembed(ctx, f'{error}')

        elif isinstance(error, commands.DisabledCommand):
            return await qembed(ctx, f'`{ctx.command}` has been disabled.')

        # For this error example we check to see where it came from...
        elif isinstance(error, commands.BadArgument):
            if ctx.command.qualified_name == 'tag list':  # Check if the command being invoked is 'tag list'
                return await qembed(ctx,
                             'I could not find that member. Please try again.')

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(ctx.command),
                  file=sys.stderr)
            traceback.print_exception(type(error),
                                      error,
                                      error.__traceback__,
                                      file=sys.stderr)
            formatted = traceback.format_exception(type(error), error, error.__traceback__)
            await ctx.send(f"Something has gone wrong while executing `{ctx.invoked_with}`:\n"
                            f"```py\n{''.join(formatted)}\n```")


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
