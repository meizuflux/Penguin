import sys
import traceback

import discord
import humanize
import re
from discord.ext import commands

from utils.fuzzy import finder
from utils.default import qembed


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        global match
        if hasattr(ctx.command, 'on_error'):
            return

        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
            return

        ignored = ()

        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.CommandNotFound):
            failed_command = re.match(rf"^({ctx.prefix})\s*(.*)", ctx.message.content, flags=re.IGNORECASE).group(2)

            matches = finder(failed_command, self.bot.command_list, lazy=False)
            if not matches:
                return

            match = None

            for command in matches:
                cmd = self.bot.get_command(command)
                if not await cmd.can_run(ctx):
                    return
                match = command
                break

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
            retry_after = humanize.precisedelta(error.retry_after, minimum_unit='seconds')
            return await qembed(ctx, f"This command is on cooldown.\nTry again in {retry_after}")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                e = discord.Embed(description=f'`{ctx.command}` can not be used in Private Messages.',color=self.bot.embed_color)
                return await ctx.author.send(embed=e)
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.MissingRequiredArgument):
            return await qembed(ctx, f'{error}')

        elif isinstance(error, commands.DisabledCommand):
            return await qembed(ctx, f'`{ctx.command}` has been disabled.')

        elif isinstance(error, commands.BadArgument):

            print(f'Ignoring exception in command {ctx.invoked_with}:', file=sys.stderr)

            traceback.print_exception(type(error),
                                      error,
                                      error.__traceback__,
                                      file=sys.stderr)

            formatted = traceback.format_exception(type(error), error, error.__traceback__)
            await ctx.send(f"Something has gone wrong while executing `{ctx.invoked_with}`:\n"
                            f"```py\n{''.join(formatted)}\n```")


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
