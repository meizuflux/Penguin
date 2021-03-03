import asyncio
import datetime
import difflib
import io
import itertools
import os
import pathlib
import platform
import re
import time
import zlib
from io import BytesIO

import aiohttp
import discord
import humanize
import psutil
from discord.ext import commands

from utils.default import plural, qembed


class ChuckContext(commands.Context):

    @property
    def secret(self):
        return 'my secret here'

    async def confirm(self, text: str = 'Are you sure you want to do this?'):
        message = await self.send(text)
        await message.add_reaction('✅')
        await message.add_reaction('❌')

        def terms(reaction, user):
            return user == self.author and str(reaction.emoji) == '✅' or user == self.author and str(
                reaction.emoji) == '❌'

        try:
            reaction, user = await self.bot.wait_for('reaction_add',
                                                     timeout=15,
                                                     check=terms)
        except asyncio.TimeoutError:
            await qembed(self, 'You did not react in time.')
        else:
            if reaction.emoji == '✅':
                return True, message
            if reaction.emoji == '❌':
                return False, message

    async def mystbin(self, data):
        data = bytes(data, 'utf-8')
        async with aiohttp.ClientSession() as cs:
            async with cs.post('https://mystb.in/documents', data=data) as r:
                res = await r.json()
                key = res["key"]
                return f"https://mystb.in/{key}"


class Help(commands.MinimalHelpCommand):
    def get_command_signature(self, command, ctx=None):
        """Method to return a commands name and signature"""
        sig = command.usage or command.signature
        if not sig and not command.parent:
            return f'`{self.clean_prefix}{command.name}`'
        if not command.parent:
            return f'`{self.clean_prefix}{command.name}` `{sig}`'
        if not sig:
            return f'`{self.clean_prefix}{command.parent}` `{command.name}`'
        else:
            return f'`{self.clean_prefix}{command.parent}` `{command.name}` `{sig}`'

    async def send_error_message(self, error):
        ctx = self.context
        destination = self.get_destination()
        embed = discord.Embed(description=error, color=ctx.bot.embed_color,
                              timestamp=ctx.message.created_at).set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await destination.send(embed=embed)

    def get_opening_note(self):
        return "`<arg>`  means the argument is required\n`[arg]`  means the argument is optional"

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            joined = '`,\u2002`'.join(c.name for c in commands)
            emoji_dict = {
                'economy': "💵",
                'fun': "<:hahayes:739613910180692020>",
                'polaroid': "📸",
                'prefixes': "<:shrug:747680403778699304>",
                'useful': "<:bruhkitty:739613862302711840>",
                'utilities': "⚙️",
                "music": "<:bruhkitty:739613862302711840>"
            }
            self.paginator.add_line(f'{emoji_dict[heading.lower()]}  **{heading}**')
            self.paginator.add_line(f'> `{joined}`')
            # self.paginator.add_line()

    def get_ending_note(self):
        command_name = self.invoked_with
        return (
            "Type `{0}{1} [command]` for more info on a command.\n"
            "You can also type `{0}{1} [category]` for more info on a category.".format(
                self.clean_prefix, command_name
            )
        )

    async def send_pages(self):
        ctx = self.context
        destination = self.get_destination()
        for page in self.paginator.pages:
            embed = discord.Embed(description=page, color=0x9c5cb4, timestamp=ctx.message.created_at).set_footer(
                text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
            await destination.send(embed=embed)

    def add_subcommand_formatting(self, command):
        fmt = '{0} \N{EN DASH} {1}' if command.short_doc else '{0} \N{EN DASH} This command is not documented'
        self.paginator.add_line(fmt.format(self.get_command_signature(command), command.short_doc))

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Error", description=str(error))
            await ctx.send(embed=embed)
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(title="Error", description=str(error))
            await ctx.send(embed=embed)
        else:
            raise error

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        no_category = '\u200b{0.no_category}'.format(self)

        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(f'**{commands}**')
            self.add_bot_commands_formatting(commands, category)

        self.paginator.add_line()
        self.paginator.add_line(self.get_ending_note())

        await self.send_pages()

    @staticmethod
    def get_help(command, brief=True):
        real_help = command.help or "This command is not documented."
        return real_help if not brief else command.short_doc or real_help

    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s %s**' % (cog.qualified_name, self.commands_heading))
            if cog.description:
                self.paginator.add_line(cog.description, empty=True)
            for command in filtered:
                self.add_subcommand_formatting(command)

        await self.send_pages()

    def get_command_help(self, command):
        ctx = self.context
        embed = discord.Embed(title=self.get_command_signature(command),
                              description=f'```{self.get_help(command, brief=False)}```', color=0x9c5cb4,
                              timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}",
                                                                           icon_url=ctx.author.avatar_url)
        if alias := command.aliases:
            embed.add_field(name="Aliases", value=f"```{', '.join(alias)}```", inline=False)
        if isinstance(command, commands.Group):
            subcommand = command.commands
            value = "\n".join(f'{self.get_command_signature(c)} \N{EN DASH} {c.short_doc}' for c in subcommand)
            if len(value) > 1024:
                value = "\n".join(f'{self.get_command_signature(c)}' for c in subcommand)
            embed.add_field(name=plural("Subcommand(s)", len(subcommand)), value=value)

        return embed

    async def handle_help(self, command):
        if not await command.can_run(self.context):
            return await qembed(self.context, f'You don\'t have enough permissions to see the help for `{command}`')
        return await self.context.send(embed=self.get_command_help(command))

    async def send_group_help(self, group):
        await self.handle_help(group)

    async def send_command_help(self, command):
        await self.handle_help(command)

    # from pb https://github.com/PB4162/PB-Bot/blob/master/cogs/Help.py#L11-L102
    async def command_not_found(self, string: str):
        matches = difflib.get_close_matches(string, self.context.bot.command_list)
        if not matches:
            return f"No command called `{string}` found."
        match = "\n".join(matches[:1])
        return f"No command called `{string}` found. Did you mean `{match}`?"


class Useful(commands.Cog, command_attrs=dict(hidden=False)):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = Help(command_attrs=dict(hidden=False, aliases=['halp', 'h', 'help_command'],
                                                   help='Literally shows this message. Jesus, do you really need this?'))
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @commands.command(aliases=['information', 'botinfo'],
                      help='Gets info about the bot')
    async def info(self, ctx):
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
                for line in of.readlines():
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

    @commands.command(name='ping', help='only for cool kids')
    async def ping(self, ctx):
        start = time.perf_counter()
        message = await ctx.send("Pinging ...")
        end = time.perf_counter()
        await message.delete()
        duration = (end - start) * 1000
        poststart = time.perf_counter()
        await self.bot.db.fetch("SELECT 1")
        postend = time.perf_counter()
        postduration = (postend - poststart) * 1000
        pong = discord.Embed(title='Ping', color=self.bot.embed_color, timestamp=ctx.message.created_at).set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        pong.add_field(name='Typing Latency',
                       value=f'```python\n{round(duration)} ms```', inline=False)
        pong.add_field(
            name='Websocket Latency',
            value=f'```python\n{round(self.bot.latency * 1000)} ms```', inline=False)
        pong.add_field(name='SQL Latency',
                       value=f'```python\n{round(postduration)} ms```', inline=False)
        await ctx.send(content=None, embed=pong)

    @commands.command(help='Shows how long the bot has been online for')
    async def uptime(self, ctx):
        await ctx.send(embed=discord.Embed(
            description=f"I've been up for {humanize.precisedelta(self.bot.uptime - datetime.datetime.utcnow(), format='%0.0f')}",
            color=self.bot.embed_color,
            timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}",
                                                         icon_url=ctx.author.avatar_url))

    @commands.command(help='Shows the avatar of a user', aliases=['pfp'])
    async def avatar(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author
        ext = 'gif' if user.is_avatar_animated() else 'png'
        ava = discord.Embed(title=f'{user.name}\'s avatar:',
                            color=self.bot.embed_color,
                            timestamp=ctx.message.created_at)
        ava.set_image(url=f"attachment://{user.id}.{ext}")
        ava.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=ava, file=discord.File(BytesIO(await user.avatar_url.read()), f"{user.id}.{ext}"))

    @commands.command(help='Searches PyPI for a Python Package')
    async def pypi(self, ctx, package: str):
        async with self.bot.session.get(f'https://pypi.org/pypi/{package}/json') as f:
            if f.status == 404:
                return await qembed(ctx, 'Package not found.')
            package = await f.json()
        embed = discord.Embed(title=f"{package['info']['name']} {package['info']['version']}",
                              url=package['info']['project_url'],
                              description=package['info']['summary'],
                              color=self.bot.embed_color,
                              timestamp=ctx.message.created_at)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/381963689470984203/814267252437942272/pypi.png')
        email = package["info"]["author_email"] or "None provided"
        embed.add_field(name='Author Info:', value=f'**Author Name**: {package["info"]["author"]}\n'
                                                   f'**Author Email**: {email}')
        docs = package["info"]["project_urls"]['Homepage'] or "None provided"
        try:
            home_page = package["info"]["project_urls"]['Documentation'] or "None provided"
        except KeyError:
            home_page = "None provided"
        keywords = package["info"]['keywords'] or "None provided"
        embed.add_field(name='Package Info:',
                        value=f'**Documentation URL**: {docs}\n'
                              f'**Home Page**: {home_page}\n'
                              f'**Keywords**: {keywords}\n'
                              f'**License**: {package["info"]["license"]}\n',
                        inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(help='Checks if your message is toxic or not.')
    async def toxic(self, ctx, *, text):
        url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={self.bot.perspective}"

        headers = {'Content-Type': 'application/json',}

        data = f'{{comment: {{text: "{text}"}}, ' \
               'languages: ["en"], ' \
               'requestedAttributes: {TOXICITY:{}} }'

        res = await self.bot.session.post(url, headers=headers, data=data)
        js = await res.json()

        level = js["attributeScores"]["TOXICITY"]["summaryScore"]["value"] * 100
        await ctx.send(f"`{text}` is `{level:.2f}%` likely to be toxic.")

    @commands.command(help='Invites the bot to your server')
    async def invite(self, ctx):
        await ctx.send(f"https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8")

    @commands.command(help='Sends the 5 most recent commits to the bot.')
    async def recent_commits(self, ctx):
        async with self.bot.session.get('https://api.github.com/repos/ppotatoo/SYSTEM32/commits') as f:
            resp = await f.json()
        embed = discord.Embed(description="\n".join(f"[`{commit['sha'][:6]}`]({commit['html_url']}) {commit['commit']['message']}" for commit in resp[:5]), color=self.bot.embed_color)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Useful(bot))
