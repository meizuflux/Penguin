"""
Copyright (C) 2021 ppotatoo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
import inspect
import os

import aiohttp
import asyncpg
import discord
import traceback
import tabulate
from discord.ext import commands
from jishaku.paginators import PaginatorInterface, WrappedPaginator

from utils.default import qembed


# from prettytable import PrettyTable


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
        """Execute SQL commands."""
        response = await self.bot.db.fetch(query)
        if len(response) == 0:
            return await ctx.message.add_reaction('✅')
        table = tabulate.tabulate((dict(item) for item in response),
                                  headers="keys",
                                  tablefmt="github")
        if len(table) > 2000: table = await ctx.mystbin(table)
        await ctx.send(embed=ctx.embed(description=f'```py\n{table}```'))

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
        proc = await asyncio.create_subprocess_shell("git pull", stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()

        if stdout:
            shell = f'[stdout]\n{stdout.decode()}'
        if stderr:
            shell = f'[stderr]\n{stderr.decode()}'

        embed = discord.Embed(title="Pulling from GitHub",
                              description=f"```\nppotatoo@36vp:~/SYSTEM32$ git pull\n{shell}\n```",
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
                    _traceback = ''.join(traceback.format_tb(e.__traceback__))
                    error = '{1}{0}: {2}\n'.format(type(e).__name__, _traceback, e)
                    error_collection.append(
                        [file, error]
                    )

        if error_collection:
            output = "\n".join(
                f"**{g[0]}** ```yaml\n{g[1]}```" for g in error_collection
            )
            if len(output) > 1024: output = await ctx.mystbin(output.replace("`", "").replace("*", ""))

            embed.add_field(name='Cog Reloading', value=f"Attempted to reload all extensions, was able to reload, "
                                                        f"however the following failed...\n\n{output}")
        else:
            embed.add_field(name='Cog Reloading', value='```\nAll cogs were loaded successfully```')

        await ctx.remove(embed=embed)

    @dev.command()
    async def reboot(self, ctx):
        """Calls bot.close() and lets the systems service handler restart it."""
        this = await ctx.confirm('Click to confirm.')
        if this[0] is not True:
            return await this[1].edit(content='Cancelled.')

        await this[1].edit(content='Shutting down.')
        await self.bot.close()

    @dev.command(aliases=['del'])
    async def delete(self, ctx, message: discord.Message = None):
        """Deletes the given message."""
        if ctx.message.reference:
            message = ctx.message.reference
            message = await ctx.fetch_message(message.message_id)
        try:
            await message.delete()
            await ctx.message.add_reaction("✅")
        except:
            await ctx.message.add_reaction("❌")

    @dev.command(aliases=["src"])
    async def source(self, ctx, *, command_name: str):
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
        for num, line in enumerate(source_lines, start=1):
            paginator.add_line(f"{str(num)} {ctx.escape(line)}")

        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        await interface.send_to(ctx)

    @commands.group()
    @commands.is_owner()
    async def change(self, ctx):
        """Change things about the bot without the developer portal."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @change.command(name="username")
    @commands.is_owner()
    async def change_username(self, ctx, *, name: str):
        """ Change username."""
        try:
            await self.bot.user.edit(username=name)
            await qembed(ctx, f"Successfully changed username to **{name}**")
        except discord.HTTPException as err:
            await qembed(ctx, err)

    @change.command(name="nickname")
    @commands.is_owner()
    async def change_nickname(self, ctx, *, name: str = None):
        """Change nickname."""
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await qembed(ctx, f"Successfully changed nickname to **{name}**")
            else:
                await qembed(ctx, "Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)

    @change.command(name="avatar")
    @commands.is_owner()
    async def change_avatar(self, ctx, url: str = None):
        """Changes the bot's avatar."""
        cs = aiohttp.ClientSession()
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip('<>') if url else None

        try:
            bio = await cs.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            await qembed(ctx, f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            await qembed(ctx, "The URL is invalid...")
        except discord.InvalidArgument:
            await qembed(ctx, "This URL does not contain a useable image")
        except discord.HTTPException as err:
            await qembed(ctx, err)
        except TypeError:
            await qembed(ctx, "You need to either provide an image URL or upload one with the command")


def setup(bot):
    bot.add_cog(Owner(bot))
