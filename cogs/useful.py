import aiohttp
import asyncio
import datetime
import discord
import humanize
import json
import pathlib
import platform
import psutil
import random
import re
import time
from collections import Counter
from discord.ext import commands, menus

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
            reaction, _ = await self.bot.wait_for('reaction_add',
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
                                    timeout=120,
                                    check=lambda r, u: u.id == self.author.id and r.message.id == m.id and str(
                                        r.emoji) == str("❌"))
            await m.delete()
        except asyncio.TimeoutError:
            pass

    def embed(self, **kwargs):
        color = kwargs.pop("color", self.bot.embed_color)
        embed = discord.Embed(**kwargs, color=color)
        embed.timestamp = self.message.created_at
        embed.set_footer(text=f"Requested by {self.author}", icon_url=self.author.avatar_url)
        return embed

    def escape(self, text: str):
        mark = [
            '`',
            '_',
            '*'
        ]
        for item in mark:
            text = text.replace(item, f'\u200b{item}')
        return text

    # https://github.com/InterStella0/stella_bot/blob/master/utils/useful.py#L199-L205
    def plural(self, text, size):
        logic = size == 1
        target = (("(s)", ("s", "")), ("(is/are)", ("are", "is")))
        for x, y in target:
            text = text.replace(x, y[logic])
        return text
    
    @property
    def clean_prefix(self):
        return re.sub(f"<@!?{self.bot.user.id}>", f"@{self.bot.user.name}", self.prefix)


class TodoSource(menus.ListPageSource):
    def __init__(self, todos):
        discord_match = re.compile(r"https?:\/\/(?:(?:ptb|canary)\.)?discord(?:app)?\.com\/channels\/(?:[0-9]{15,19})\/(?:[0-9]{15,19})\/(?:[0-9]{15,19})\/?")
        url_match = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        tod=[]
        for todo in todos:
            text = todo['todo']
            for match in url_match.findall(text):
                if not discord_match.findall(match):
                    url = match.replace(match, match.split("/")[2])
                    text = text.replace(match, f"[`[{url}]`]({match})")
            for match in discord_match.findall(text):
                text = text.replace(match, f"[`[jump link]`]({match})")

            tod.append(f"`[{todo['row_number']}]` {text}")
        super().__init__(tod, per_page=10)

    async def format_page(self, menu, todos):
        ctx = menu.ctx
        count = await ctx.bot.db.fetchval("SELECT COUNT(*) FROM TODOS WHERE user_id = $1", ctx.author.id)
        cur_page = f"Page {menu.current_page + 1}/{self.get_max_pages()}"
        return ctx.embed(
            title=f"{menu.ctx.author.name}'s todo list | {count} total entries | {cur_page}",
            description="\n".join(todos),
        )


class TodoPages(menus.MenuPages):

    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=menus.Last(2))
    async def end_menu(self, _):
        self.stop()


class Useful(commands.Cog, command_attrs=dict(hidden=False)):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['codestats'])
    async def code_stats(self, ctx):
        p = pathlib.Path('./')
        cm = cr = fn = cl = ls = fc = 0
        for f in p.rglob('*.py'):
            if str(f).startswith("venv"):
                continue
            fc += 1
            with f.open() as of:
                for l in of.readlines():
                    l = l.strip()
                    if l.startswith('class'):
                        cl += 1
                    if l.startswith('def'):
                        fn += 1
                    if l.startswith('async def'):
                        cr += 1
                    if '#' in l:
                        cm += 1
                    ls += 1
        text = (
            f"```yaml\n"
            f"Files: {fc}\n"
            f"Lines: {ls:,}\n"
            f"Classes: {cl}\n"
            f"Functions: {fn}\n"
            f"Coroutines: {cr}\n"
            f"Comments: {cm:,} ```"
        )
        await ctx.send(text)

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
        uptime = humanize.precisedelta(self.bot.uptime - datetime.datetime.utcnow(), format='%0.0f')
        await ctx.send(embed=ctx.embed(description=f"I've been up for {uptime}"))

    @commands.command(aliases=['a', 'pfp'])
    async def avatar(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author
        ava = ctx.embed(title=f'{user.name}\'s avatar:')
        types = [
            f"[{type}]({str(user.avatar_url_as(format=type))})"
            for type in ["webp", "png", "jpeg", "jpg"]
        ]

        if user.is_avatar_animated():
            types.append(f"[gif]({str(user.avatar_url_as(format='gif'))})")
        ava.description = " | ".join(types)
        ava.set_image(url=user.avatar_url)
        await ctx.send(embed=ava)

    @commands.command(help='Searches PyPI for a Python Package')
    async def pypi(self, ctx, package: str):
        async with self.bot.session.get(f'https://pypi.org/pypi/{package}/json') as f:
            if not f or f.status != 200:
                return await ctx.send(embed=ctx.embed(description='Package not found.'))
            package = await f.json()
        data = package.get("info")
        embed = ctx.embed(title=f"{data.get('name')} {data['version'] or ''}",
                          url=data.get('project_url', 'None provided'),
                          description=data["summary"] or "None provided")
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/381963689470984203/814267252437942272/pypi.png')
        embed.add_field(name='Author Info:', value=f'**Author Name**: `{data["author"] or "None provided"}`\n'
                                                   f'**Author Email**: `{data["author_email"] or "None provided"}`')
        urls = data.get("project_urls", "None provided")
        embed.add_field(name='Package Info:',
                        value=f'**Documentation**: `{urls.get("Documentation", "None provided")}`\n'
                              f'**Homepage**: `{urls.get("Homepage", "None provided")}`\n'
                              f'**Keywords**: `{data["keywords"] or "None provided"}`\n'
                              f'**License**: `{data["license"] or "None provided"}`',
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

    @commands.command(help='Builds an embed from a dict. You can use https://eb.nadeko.bot/ to get one',
                      brief='Builds an embed', aliases=['make_embed', 'embed_builder'])
    async def embedbuilder(self, ctx, *, embed: json.loads):
        try:
            await ctx.send(embed=discord.Embed().from_dict(embed))
        except:
            await qembed(ctx, 'You clearly don\'t know what this is')

    @commands.command(help='Invites the bot to your server')
    async def invite(self, ctx):
        invite = ctx.embed(title='Invite me to your server:', description=self.bot.invite)
        invite.add_field(name='You can also join the support server:', value=self.bot.support_invite)
        await ctx.send(embed=invite)

    @commands.command(help='An invite link to the bot support server.')
    async def support(self, ctx):
        await ctx.send(embed=ctx.embed(title='Support server invite:', description='https://discord.gg/NTNgvHkjSp'))

    @commands.command(help='Sends the 5 most recent commits to the bot.')
    async def recent_commits(self, ctx):
        async with self.bot.session.get('https://api.github.com/repos/ppotatoo/Penguin/commits') as f:
            resp = await f.json()
        embed = ctx.embed(description="\n".join(
            f"[`{commit['sha'][:6]}`]({commit['html_url']}) {commit['commit']['message']}" for commit in resp[:5])
        )
        await ctx.send(embed=embed)

    @commands.command(help='Suggests a feature to the developers!')
    async def suggest(self, ctx, *, suggestion):
        support = self.bot.get_channel(818246475867488316)
        await support.send(embed=ctx.embed(title='New Suggestion:',
                                           description=f"```\n{ctx.escape(suggestion)}```\n[**JUMP URL**]({ctx.message.jump_url})"))
        await ctx.send(embed=ctx.embed(description='Your suggestion has been sent! '))

    @commands.command(help='Pretty-Prints some JSON')
    async def pprint(self, ctx, *, data: str):
        try:
            data = data.replace("'", '"')
            await ctx.send(f"```json\n{ctx.escape(json.dumps(json.loads(data), indent=4))}```")
        except json.JSONDecodeError:
            await ctx.send('Nice, you provided invalid JSON. Good work.')

    @commands.command(help='Chooses the best choice.')
    async def choose(self, ctx, choice_1, choice_2):
        choice = Counter(random.choice([choice_1, choice_2]) for _ in range(1500))
        answer = max(choice[choice_1], choice[choice_2])
        result = sorted(choice, key=lambda e: e == answer)
        await ctx.send(f'{result[0]} won with {answer} votes and {answer / 1500:.2f}% of the votes')

    @commands.group()
    async def todo(self, ctx):
        """Create a todo list!"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(str(ctx.command))

    @todo.command()
    async def list(self, ctx):
        """View all your todos."""
        sql = (
            "SELECT DISTINCT todo, sort_date, jump_url, "
            "ROW_NUMBER () OVER (ORDER BY sort_date) FROM todos "
            "WHERE user_id = $1 ORDER BY sort_date"
        )
        todos = await self.bot.db.fetch(sql, ctx.author.id)


        pages = TodoPages(source=TodoSource(todos), delete_after=True)

        await pages.start(ctx)

    @todo.command()
    async def add(self, ctx, *, task: str):
        """Insert a task into your todo list.
        Limit of 150 characters."""
        if len(task) > 150: raise commands.BadArgument('Tasks must be under 150 characters.')
        sql = (
            "INSERT INTO TODOS (user_id, todo, sort_date, jump_url, time) "
            "VALUES ($1, $2, $3, $4, $3)"
        )
        await self.bot.db.execute(sql, ctx.author.id, task, datetime.datetime.utcnow(), ctx.message.jump_url)
        await ctx.send(embed=ctx.embed(title="Inserted into your todo list...", description=task))

    @todo.command()
    async def remove(self, ctx, numbers: commands.Greedy[int]):
        """Delete 1 or many tasks.
        Separate todos with a space, EX "1 2 3 4" will delete tasks 1, 2, 3, and 4."""
        sql = (
            "SELECT DISTINCT todo, sort_date, "
            "ROW_NUMBER () OVER (ORDER BY sort_date) FROM todos "
            "WHERE user_id = $1 ORDER BY sort_date"
        )
        todos = await self.bot.db.fetch(sql, ctx.author.id)
        for number in numbers:
            if number > len(todos):
                return await ctx.send("You can't delete a task you don't have.")
        delete = (
            "DELETE FROM todos "
            "WHERE user_id = $1 AND todo = ANY ($2)"
        )
        to_delete = [todos[num - 1]["todo"] for num in numbers]
        await self.bot.db.execute(delete, ctx.author.id, tuple(to_delete))

        desc = "\n".join(f"`{todos[num - 1]['row_number']}` - {todos[num - 1]['todo']}" for num in numbers)
        task = ctx.plural('task(s)', len(numbers))
        embed = ctx.embed(title=f"Removed {humanize.apnumber(len(numbers))} {task}:",
                          description=desc)
        await ctx.send(embed=embed)

    @todo.command(name='info')
    async def todo_info(self, ctx, id: int):
        """
        View info about a certain task.
        You can see the exact time the task was created.
        """
        sql = (
            "SELECT DISTINCT todo, sort_date, time, jump_url, "
            "ROW_NUMBER () OVER (ORDER BY sort_date) FROM todos "
            "WHERE user_id = $1 ORDER BY sort_date"
        )
        todos = await self.bot.db.fetch(sql, ctx.author.id)
        todo = todos[id-1]["todo"]
        pro = humanize.naturaltime(datetime.datetime.utcnow() - todos[id-1]["time"])
        embed = ctx.embed(title=f'Task `{id}`', description=todo)
        embed.add_field(name='Info', value=f"This todo was created **{pro}**.\n[`Jump to the creation message`]({todos[id-1]['jump_url']})")
        await ctx.send(embed=embed)

    @todo.command(usage='<task ID 1> <task ID 2>')
    async def swap(self, ctx, t1: int, t2: int):
        """Swap the places of two tasks."""
        sql = (
            "SELECT DISTINCT sort_date, todo "
            "FROM todos "
            "WHERE user_id = $1 ORDER BY sort_date"
        )
        todos = await self.bot.db.fetch(sql, ctx.author.id)
        task1 = todos[t1 - 1]
        task2 = todos[t2 - 1]
        await self.bot.db.execute("UPDATE todos SET sort_date = $1 WHERE user_id = $2 AND todo = $3", task2['sort_date'], ctx.author.id, task1['todo'])
        await self.bot.db.execute("UPDATE todos SET sort_date = $1 WHERE user_id = $2 AND todo = $3", task1['sort_date'], ctx.author.id, task2['todo'])
        await ctx.send(embed=ctx.embed(description=f"Succesfully swapped places of todo `{t1}` and `{t2}`"))

    @todo.command()
    async def raw(self, ctx, id: int):
        """View the raw todo for a task."""
        sql = (
            "SELECT DISTINCT todo, sort_date, "
            "ROW_NUMBER () OVER (ORDER BY sort_date) FROM todos "
            "WHERE user_id = $1 ORDER BY sort_date"
        )

        todos = await self.bot.db.fetch(sql, ctx.author.id)
        if id > len(todos):
            return await ctx.send(f"You only have {len(todos)} {ctx.plural('task(s)', len(todos))}")
        await ctx.send(todos[id-1]['todo'], allowed_mentions=discord.AllowedMentions().none())

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id in self.bot.afk.keys():
            del self.bot.afk[message.author.id]
            return await message.channel.send(f"Welcome back, {message.author.mention}, I have removed your AFK status.")
        for user_id, data in self.bot.afk.items():
            user = await self.bot.try_user(user_id)
            if user.mentioned_in(message):
                ago = humanize.naturaltime(datetime.datetime.utcnow() - data["time"])
                await message.channel.send(f"<:whenyahomiesaysomewildshit:596577153135673344> Hey, but {user.name} went AFK {ago} for `{data['reason']}`")

    @commands.command()
    async def afk(self, ctx, *, reason: str):
        """
        This marks you as AFK.
        When someone pings you while you are AFK, it will let them know that you are AFK, how long you have been AFK, and your reason.
        """
        self.bot.afk[ctx.author.id] = {"reason": reason, "time": datetime.datetime.utcnow()}
        await ctx.send(f'OK, I have set your AFK status to `{reason}`')

    @commands.command()
    async def command_usage(self, ctx):



class AAAAAA(commands.Cog):
    def init(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def asdfasdfasdfasdfasdfasdfadsfasdf(self, ctx):
        await ctx.send(1 + 2)


def setup(bot):
    bot.add_cog(Useful(bot))
    bot.add_cog(AAAAAA(bot))
