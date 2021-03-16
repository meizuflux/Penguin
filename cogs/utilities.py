import datetime
import json
import re
import string
import secrets

import discord
import humanize
import numpy as np
import io
from discord.ext import commands, tasks, flags
from jishaku.functools import executor_function
from jishaku.paginators import PaginatorInterface, WrappedPaginator

from utils.default import qembed
from utils.fuzzy import finder


class DeletedMessage:
    __slots__ = ('author', 'content', 'channel', 'guild', 'created_at', 'deleted_at', 'del_embed', 'attachment')

    def __init__(self, message):
        self.author = message.author
        self.content = message.content
        self.guild = message.guild
        self.created_at = message.created_at
        self.deleted_at = datetime.datetime.utcnow()
        if message.embeds:
            self.del_embed = message.embeds[0]
        if message.attachments:
            self.attachment = message.attachments[0].proxy_url
        else:
            self.attachment = None


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.match = re.compile(r"(?P<name>(?<=;{1})[\w]+)")
        self.clear_message.start()

    def cog_unload(self):
        self.clear_message.cancel()

    @tasks.loop(hours=1)
    async def clear_message(self):
        for channel_id in self.bot.deleted_messages:
            if len(self.bot.deleted_messages[channel_id]) > 250:
                dele = len(self.bot.deleted_messages[channel_id]) - 250
                for number in range(dele):
                    del self.bot.deleted_messages[channel_id][number]

    def deleted_message_for(self, index: int, channel_id: int):
        try:
            if index > len(self.bot.deleted_messages[channel_id]):
                return None
        except KeyError:
            return None

        readable_order = list(reversed(self.bot.deleted_messages[channel_id]))
        try:
            result = readable_order[index]
        except KeyError:
            return None
        else:
            return result

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        b = [479359598730674186]
        if message.author.id in b:
            return
        self.bot.deleted_messages[message.channel.id].append(DeletedMessage(message))

    @commands.Cog.listener()
    async def on_message(self, message):
        not_owner = not await self.bot.is_owner(message.author)
        if not_owner or message.author.bot:
            return

        matches = self.match.findall(message.content)
        if not matches:
            return
        emoji = []
        for match in matches:
            e = finder(match, self.bot.emojis, key=lambda emoji: emoji.name, lazy=False)
            if e == []:
                continue
            e = e[0]
            if e is None:
                return
            if e.is_usable():
                emoji.append(str(e))
        await message.channel.send(" ".join(emoji))



    @commands.command(help='Sends a list of the emojis that the bot can see.')
    async def emojis(self, ctx, search=None):
        emojis = []
        if search:
            result = finder(text=search, collection=self.bot.emojis, key=lambda emoji: emoji.name, lazy=False)
            if result == []:
                return await ctx.send("Nothing found for your query.")
            for emoji in result:
                emojis.append(f"{str(emoji)} `{emoji.name}`")
            paginator = WrappedPaginator(prefix='', suffix='', max_size=500)
        else:
            for emoji in self.bot.emojis:
                emojis.append(f"{str(emoji)} `{emoji.name}`")
            paginator = WrappedPaginator(prefix='', suffix='', max_size=1000)
        paginator.add_line('\n'.join(emojis))
        interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
        await interface.send_to(ctx)

    @executor_function
    def levenshtein_match_calc(self, s, t):
        rows = len(s) + 1
        cols = len(t) + 1
        distance = np.zeros((rows, cols), dtype=int)

        for i in range(1, rows):
            for k in range(1, cols):
                distance[i][0] = i
                distance[0][k] = k

        for col in range(1, cols):
            for row in range(1, rows):
                cost = 0 if s[row - 1] == t[col - 1] else 2
                distance[row][col] = min(distance[row - 1][col] + 1,  # Cost of deletions
                                         distance[row][col - 1] + 1,  # Cost of insertions
                                         distance[row - 1][col - 1] + cost)  # Cost of substitutions
        Ratio = ((len(s) + len(t)) - distance[row][col]) / (len(s) + len(t))
        return int(Ratio * 100)

    @commands.command(help='Compares the similarity of two strings')
    async def fuzzy(self, ctx, string1, string2):
        result = await self.levenshtein_match_calc(string1, string2)
        await qembed(ctx, f'`{string1}` and `{string2}` are `{result}%` similar.')

    @fuzzy.error
    async def fuzzy_error(self, ctx, error):
        await qembed(ctx, "Invalid string provided.")

    @commands.guild_only()
    @commands.is_owner()
    @commands.command(help='Views up to the last 500 deleted messages')
    async def snipe(self, ctx, index: int = 1, channel: discord.TextChannel = None):
        if channel and channel.is_nsfw():
            return await qembed(ctx, 'no sorry')
        if not channel:
            channel = ctx.channel
        try:
            msg = self.deleted_message_for(index - 1, channel.id)
            try:
                await ctx.send(embed=msg.del_embed)
                content = 'Bot deleted an embed which was sent above.' if not msg.content else msg.content
            except AttributeError:
                content = msg.content
        except IndexError:
            return await qembed(ctx, 'Nothing to snipe!')
        snipe = discord.Embed(title='Content:', description=content, color=self.bot.embed_color,
                              timestamp=ctx.message.created_at)
        if msg.attachment:
            snipe.add_field(name='Attachment', value=msg.attachment, inline=False)
        snipe.add_field(name='Message Stats:', value=
        f"**Created At:** {humanize.naturaldelta(msg.created_at - datetime.datetime.utcnow())} ago\n"
        f"**Deleted At:** {humanize.naturaldelta(msg.deleted_at - datetime.datetime.utcnow())} ago\n"
        f"**Index:** {index} / {len(self.bot.deleted_messages[channel.id])}", inline=False)
        snipe.set_author(name=f'{str(msg.author)} said in #{channel.name}:', icon_url=str(msg.author.avatar_url))
        snipe.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=snipe)

    @commands.command(help='Posts text to https://mystb.in', aliases=['paste'])
    async def mystbin(self, ctx, *, text=None):
        filenames = (".txt", ".py", ".json", ".html", ".csv")
        if ctx.message.reference:
            ref = ctx.message.reference
            if ref.cached_message:
                attachment = ref.cached_message.attachments[0]
                if (ref.cached_message.attachments and attachment.filename.endswith(filenames)):
                    syntax = attachment.filename.split(".")[1]
                    message = await attachment.read()
                    decoded_message = message.decode("utf-8")
                    text = f'{await ctx.mystbin(decoded_message)}.{syntax}'

            else:
                message = await self.bot.get_channel(ctx.message.reference.channel_id).fetch_message(ref.message_id)
                if message.attachments and message.attachments.filename.endswith(filenames):
                    syntax = message.attachments[0].filename.split(".")[1]
                    message_ = await message.attachments[0].read()
                    decoded_message = message_.decode("utf-8")
                    text = f'{await ctx.mystbin(decoded_message)}.{syntax}'

        if text is None:
            try:
                attachment = ctx.message.attachments[0]
            except IndexError:
                return await ctx.send('You need to provide text or an attachment.')
            if attachment:
                syntax = attachment.filename.split(".")[1]
                if attachment.filename.endswith(filenames):
                    message = await message.read()
                    decoded_message = message.decode("utf-8")
                    text = f'{await ctx.mystbin(decoded_message)}.{syntax}'

        await qembed(ctx, text)

    # from pb https://github.com/PB4162/PB-Bot
    @commands.command(aliases=["rawmessage", "rawmsg"])
    async def raw_message(self, ctx, *, message: discord.Message = None):
        """
        Get the raw info for a message.
        """
        if ctx.message.reference:
            message = ctx.message.reference
            message = await ctx.fetch_message(message.message_id)

        message = message or ctx.message

        try:
            msg = await self.bot.http.get_message(ctx.channel.id, message.id)
        except discord.NotFound:
            return await qembed(ctx, "Sorry, I couldn't find that message.")

        raw = json.dumps(msg, indent=4)
        if len(raw) > 1989:
            return await qembed(ctx, f'{await ctx.mystbin(raw)}.json')
        await qembed(ctx, f"```json\n{ctx.escape(raw)}```")

    @commands.command(help='Randomly generates a password', aliases=['pw', 'pwd'])
    async def password(self, ctx, length=16):
        if length > 94:
            return await qembed(ctx, 'Sorry, 94 characters is the limit.')
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        num = string.digits
        symbols = string.punctuation

        total = lower + upper + num + symbols

        password = ''.join(secrets.choice(total) for i in range(length))
        embed = ctx.embed(description=f'{length} digit random password:```\n{ctx.escape(password)}```')
        await ctx.author.send(embed=embed)
        await qembed(ctx, f'Messaged you with the password, {ctx.author.mention}')

    @commands.command(help='Checks where a URL redirects. WARNING NOT 100% ACCURATE',
                      aliases=['redirectchecker', 'redirectcheck', 'redirect_check'])
    async def redirect_checker(self, ctx, url):
        url_regex = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        match = url_regex.match(url)
        if not match:
            raise commands.BadArgument('Invalid URL provided.')
        async with self.bot.session.get(url) as redirect:
            await qembed(ctx, f'`{str(redirect.real_url)}`')

    @commands.command(aliases=['ip', 'iplookup'])
    async def ipcheck(self, ctx, ip):
        async with self.bot.session.get(f'http://ip-api.com/json/{ip}?fields=16969727') as resp:
            ip = await resp.json()
        if ip["status"] == 'fail':
            return await ctx.send(f'Invalid IP. Error message:\n`{ip["message"]}`')
        await ctx.send(f'```json\n{json.dumps(ip, indent=4)}```')

    @commands.command()
    async def percentage(self, ctx, percentage: str, number: int):
        percentage = int(str(percentage.split("%")[0]))
        result = (percentage * number) / 100
        await ctx.send(f"`{percentage}%` of `{number}` is `{result}`")

    @flags.add_flag("--ext", default="txt")
    @commands.command(cls=flags.FlagCommand, usage='<text> [--ext ".py"]')
    async def text(self, ctx, text, **flags):
        """Writes text to a file."""
        ext = flags['ext'] if flags['ext'].startswith(".") else "." + flags['ext']
        buffer = io.BytesIO(text.encode("utf8"))

        await ctx.send(file=discord.File(fp=buffer, filename=f"{ctx.author.name}{ext}"))

    @commands.command()
    async def shorten(self, ctx, url: str):
        url_regex = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        match = url_regex.match(url)
        if not match:
            raise commands.BadArgument('Invalid URL provided.')
        if match:
            async with self.bot.session.get('https://clck.ru/--?url='+match[0]) as f:
                await ctx.send(await f.text())


def setup(bot):
    bot.add_cog(Utilities(bot))
