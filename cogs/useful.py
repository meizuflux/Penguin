import asyncio
import datetime
import json
import pathlib
import platform
import random
import time
from collections import Counter
from io import BytesIO

import aiohttp
import discord
import humanize
import psutil
from discord.ext import commands

from utils.default import qembed


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
            return False, message
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

    async def remove(self, *args, **kwargs):
        m = await self.send(*args, **kwargs)
        await m.add_reaction("❌")
        try:
            await self.bot.wait_for('reaction_add',
                                    check=lambda r, u: u.id == self.author.id and r.message.id == m.id and str(
                                        r.emoji) == str("❌"))
            await m.delete()
        except asyncio.TimeoutError:
            pass

    def embed(self, *args, **kwargs):
        color = kwargs.pop("color", self.bot.embed_color)
        embed = discord.Embed(*args, **kwargs, color=color)
        embed.timestamp = self.message.created_at
        embed.set_footer(text=f"Requested by {self.author}", icon_url=self.author.avatar_url)
        return embed


class Useful(commands.Cog, command_attrs=dict(hidden=False)):
    def __init__(self, bot):
        self.bot = bot

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
        duration = (time.perf_counter() - start) * 1000
        poststart = time.perf_counter()
        await self.bot.db.fetch("SELECT 1")
        postduration = (time.perf_counter() - poststart) * 1000
        pong = discord.Embed(title='Ping', color=self.bot.embed_color, timestamp=ctx.message.created_at).set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        pong.add_field(name='Typing Latency',
                       value=f'```python\n{round(duration)} ms```', inline=False)
        pong.add_field(
            name='Websocket Latency',
            value=f'```python\n{round(self.bot.latency * 1000)} ms```', inline=False)
        pong.add_field(name='SQL Latency',
                       value=f'```python\n{round(postduration)} ms```', inline=False)
        await message.edit(content=None, embed=pong)

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
                return await ctx.send(embed=ctx.embed(description='Package not found.'))
            package = await f.json()
        data = package.get("info", "test")
        embed = ctx.embed(title=f"{data.get('name', 'None provided')} {data.get('version', 'None provided')}",
                              url=data.get('project_url', 'None provided'),
                              description=data.get('summary', 'None provided'))
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/381963689470984203/814267252437942272/pypi.png')
        embed.add_field(name='Author Info:', value=f'**Author Name**: `{data.get("author", "None provided")}`\n'
                                                   f'**Author Email**: `{data.get("author_email", "None provided")}`')
        urls = data.get("project_urls", "None provided")
        embed.add_field(name='Package Info:',
                        value=f'**Documentation URL**: `{urls.get("Documentation", "None provided")}`\n'
                              f'**Home Page**: `{urls.get("Homepage", "None provided")}`\n'
                              f'**Keywords**: `{data.get("keywords", "None provided")}`\n'
                              f'**License**: `{data.get("license", "None provided")}`\n',
                        inline=False)
        await ctx.send(embed=embed)

    @commands.command(help='Checks if your message is toxic or not.')
    async def toxic(self, ctx, *, text):
        url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={self.bot.perspective}"

        headers = {'Content-Type': 'application/json', }

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
        embed = discord.Embed(description="\n".join(
            f"[`{commit['sha'][:6]}`]({commit['html_url']}) {commit['commit']['message']}" for commit in resp[:5]),
            color=self.bot.embed_color)
        await ctx.send(embed=embed)

    @commands.command(help='Pretty-Prints some JSON')
    async def pprint(self, ctx, hmm: json.loads):
        hmm.replace("'", '"')
        await ctx.send(json.dumps(hmm, indent=4))

    @commands.command(help='Chooses the best choice.')
    async def choose(self, ctx, choice_1, choice_2):
        choice = Counter(random.choice([choice_1, choice_2]) for _ in range(1500))
        answer = max(choice[choice_1], choice[choice_2])
        result = sorted(choice, key=lambda e: e == answer)
        await ctx.send(f'{result[0]} won with {answer} votes and {answer / 1500:.2f}% of the votes')


def setup(bot):
    bot.add_cog(Useful(bot))
