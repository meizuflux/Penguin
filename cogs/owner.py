# credit here goes to DeltaWing#0700 for the sql command its kinda cool
import subprocess

import asyncpg
from discord.ext import commands
from prettytable import PrettyTable
import discord
import os
import inspect
from jishaku.paginators import PaginatorInterface, WrappedPaginator

from utils.default import qembed, traceback_maker


class Owner(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.id == self.bot.author_id

    @commands.group(help='Some developer commands')
    async def dev(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @dev.command()
    async def sql(self, ctx, *, query):
        res = await self.bot.db.fetch(query)
        if len(res) == 0:
            return await ctx.message.add_reaction('✅')
        headers = list(res[0].keys())
        table = PrettyTable()
        table.field_names = headers
        for record in res:
            lst = list(record)
            table.add_row(lst)
        msg = table.get_string()
        await ctx.send(f"```\n{msg}\n```")

    @sql.error
    async def sql_error_handling(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, asyncpg.exceptions.UndefinedTableError):
                return await qembed(ctx, "This table does not exist.")
            elif isinstance(error, asyncpg.exceptions.PostgresSyntaxError):
                return await qembed(ctx, f"There was a syntax error:```\n {error} ```")
            else:
                await ctx.send(error)
        else:
            await ctx.send(error)

    @dev.command(help='Syncs with GitHub and reloads all cogs')
    async def sync(self, ctx):
        await ctx.trigger_typing()
        out = subprocess.check_output("git pull", shell=True)
        embed = discord.Embed(title="Pulling from GitHub",
                              description=f"```\nroot@SYSTEM32# git pull\n{out.decode('utf-8')}\n```",
                              color=self.bot.embed_color,
                              timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}",
                                                                           icon_url=ctx.author.avatar_url)
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                except Exception as e:
                    error_collection.append(
                        [file, traceback_maker(e, advance=False)]
                    )

        if error_collection:
            output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
            embed.add_field(name='Cog Reloading', value=f"Attempted to reload all extensions, was able to reload, "
                                                        f"however the following failed...\n\n{output}")
        else:
            if len(out.decode('utf-8')) == 20:
                pass
            else:
                embed.add_field(name='Cog Reloading', value='```\nAll cogs were loaded successfully```')
        await ctx.send(embed=embed)

    @dev.command()
    async def reboot(self, ctx):
        """Calls bot.close() and lets the systems service handler restart it."""
        await qembed(ctx, "Goodbye. I'll be back soon.")
        await self.bot.close()

    @dev.command(name="source", aliases=["src"])
    async def jsk_source(self, ctx, *, command_name: str):
        """
        Displays the source code for a command.
        """

        command = self.bot.get_command(command_name)
        if not command:
            return await ctx.send(f"Couldn't find command `{command_name}`.")

        try:
            source_lines, _ = inspect.getsourcelines(command.callback)
        except (TypeError, OSError):
            return await ctx.send(f"Was unable to retrieve the source for `{command}` for some reason.")

        # getsourcelines for some reason returns WITH line endings
        source_lines = ''.join(source_lines).split('\n')

        paginator = WrappedPaginator(prefix='```py', suffix='```', max_size=1985)
        for line in source_lines:
            paginator.add_line(line.replace("`", "\u200b`"))

        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        await interface.send_to(ctx)

def setup(bot):
    bot.add_cog(Owner(bot))
