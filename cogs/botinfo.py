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

import datetime
import pathlib
import platform

import discord
import humanize
import psutil
from discord.ext import commands, menus

from cogs.useful import TodoPages


class CommandSource(menus.ListPageSource):
    def __init__(self, cmds):
        super().__init__(cmds, per_page=10)

    async def format_page(self, menu, cmds):
        ctx = menu.ctx
        yee = "".join(cmds)
        cur_page = f"Command Usage | Page {menu.current_page + 1}/{self.get_max_pages()}"
        return ctx.embed(
            title=cur_page,
            description=f"`Total usage since restart => {ctx.bot.usage_counter}`{yee}",
        )


class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['cmdus'])
    async def command_usage(self, ctx):
        """Returns command usage for the bot.
        Paginated menu in order of most used.

        Arguments:
            This command takes no arguments."""
        cmds = [f"\n`{c:<29}{i}`" for c, i in self.bot.command_usage.most_common()]
        pages = TodoPages(source=CommandSource(cmds))
        await pages.start(ctx)

    @commands.command()
    async def suggest(self, ctx, *, suggestion):
        """Lets you suggest something to the developer.
        Suggestion can be anything you want. Please don't spam, I don't want to have to blacklist you."""
        support = self.bot.get_channel(818246475867488316)
        await support.send(embed=ctx.embed(title='New Suggestion:',
                                           description=f"```\n{ctx.escape(suggestion)}```\n[**JUMP URL**]({ctx.message.jump_url})"))
        await ctx.send(embed=ctx.embed(description='Your suggestion has been sent! '))

    @commands.command()
    async def invite(self, ctx):
        """Returns the link to invite the bot.
        Also gives the invite to the support server."""
        invite = ctx.embed(title='Invite me to your server:', description=self.bot.invite)
        invite.add_field(name='You can also join the support server:', value=self.bot.support_invite)
        await ctx.send(embed=invite)

    @commands.command()
    async def support(self, ctx):
        """Returns an invite to the support server."""
        await ctx.send(embed=ctx.embed(title='Support server invite:', description='https://discord.gg/NTNgvHkjSp'))

    @commands.command()
    async def uptime(self, ctx):
        """Returns the uptime of the bot."""
        uptime = humanize.precisedelta(self.bot.uptime - datetime.datetime.utcnow(), format='%0.0f')
        await ctx.send(embed=ctx.embed(description=f"I've been up for {uptime}"))

    @commands.command(aliases=['codestats'])
    async def code_stats(self, ctx):
        """Returns code statistics for the bot.
        Items:
            Files,
            Lines,
            Characters,
            Classes,
            Functions,
            Coroutines,
            Comments."""
        p = pathlib.Path('./')
        cm = cr = fn = cl = ls = fc = ch = 0
        for f in p.rglob('*.py'):
            if str(f).startswith("venv"):
                continue
            fc += 1
            with f.open() as of:
                lines = of.readlines()
                ls += len(lines)
                for l in lines:
                    l = l.strip()
                    ch += len(l)
                    if l.startswith('class'):
                        cl += 1
                    if l.startswith('def'):
                        fn += 1
                    if l.startswith('async def'):
                        cr += 1
                    if '#' in l:
                        cm += 1
        text = (
            f"```yaml\n"
            f"Files: {fc}\n"
            f"Lines: {ls:,}\n"
            f"Characters: {ch}\n"
            f"Classes: {cl}\n"
            f"Functions: {fn}\n"
            f"Coroutines: {cr}\n"
            f"Comments: {cm:,} ```"
        )
        await ctx.send(text)

    @commands.command(aliases=['information', 'botinfo'])
    async def info(self, ctx):
        """Returns info about the bot.
        This also contains stats about things like Memory usage."""
        msg = await ctx.send('Getting bot information ...')
        average_members = sum([guild.member_count
                               for guild in self.bot.guilds]) / len(self.bot.guilds)
        cpu_usage = psutil.cpu_percent()
        cpu_freq = psutil.cpu_freq().current
        ram_usage = humanize.naturalsize(psutil.Process().memory_full_info().uss)
        hosting = platform.platform()

        p = pathlib.Path('./')
        ls = 0
        for f in p.rglob('*.py'):
            if str(f).startswith("venv"):
                continue
            with f.open() as of:
                for _ in of.readlines():
                    ls += 1

        emb = discord.Embed(description=self.bot.description, colour=self.bot.embed_color,
                            timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}",
                                                                         icon_url=ctx.author.avatar_url)
        emb.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        emb.add_field(name='Developer', value=f'```ppotatoo#9688 ({self.bot.author_id})```', inline=False)
        emb.add_field(name='Line Count', value=f'```{ls:,} lines```', inline=True)
        emb.add_field(name='Command Count', value=f'```{len(set(self.bot.walk_commands())) - 31} commands```',
                      inline=True)
        emb.add_field(name='Guild Count', value=f'```{str(len(self.bot.guilds))} guilds```', inline=True)
        emb.add_field(name='CPU Usage', value=f'```{cpu_usage:.2f}%```', inline=True)
        emb.add_field(name='CPU Frequency', value=f'```{cpu_freq} MHZ```', inline=True)
        emb.add_field(name='Memory Usage', value=f'```{ram_usage}```', inline=True)
        emb.add_field(name='Hosting', value=f'```{hosting}```', inline=False)
        emb.add_field(name='Member Count',
                      value=f'```{str(sum([guild.member_count for guild in self.bot.guilds]))} members```', inline=True)
        emb.add_field(name='Average Member Count', value=f'```{average_members:.0f} members per guild```')

        await msg.edit(content=None, embed=emb)

    @commands.command()
    async def vote(self, ctx):
        await ctx.send(embed=ctx.embed(description=f"Vote for {self.bot.user.name} [here](https://top.gg/bot/810570659968057384/vote)!"))


def setup(bot):
    bot.add_cog(BotInfo(bot))
