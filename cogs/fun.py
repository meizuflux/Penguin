import discord
from discord.ext import commands, flags
from io import BytesIO
from utils.default import qembed


class Fun(commands.Cog):
    """For the fun commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help='Sends a cat for every error code', aliases=['httpcat', 'http_cat'])
    async def http(self, ctx, code=404):
        async with self.bot.session.get(
                f"https://http.cat/{code}") as resp:
            buffer = await resp.read()
        embed = discord.Embed(colour=self.bot.embed_color, timestamp=ctx.message.created_at)
        embed.set_image(url=f"attachment://{code}.png")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed, file=discord.File(BytesIO(buffer), filename=f"{code}.png"))

    @flags.add_flag("--dark", action='store_true', default=False)
    @flags.add_flag("--light", action='store_true', default=False)
    @flags.add_flag("--text", default="supreme")
    @flags.command(usage='"supreme" [--dark|--light]')
    async def supreme(self, ctx, **flags):
        """Makes a custom supreme logo
        example: supreme --text "hey guys" --dark"""
        if flags["dark"] and flags["light"]:
            return await qembed(ctx, "You can't have both dark and light, sorry.")
        image = await self.bot.alex.supreme(text=flags["text"],
                                            dark=flags["dark"],
                                            light=flags["light"])
        image_bytes = await image.read()
        file = discord.File(image_bytes, "supreme.png")
        embed = discord.Embed(colour=self.bot.embed_color,
                              timestamp=ctx.message.created_at).set_footer(
                                                                            text=f"Requested by {ctx.author}",
                                                                            icon_url=ctx.author.avatar_url)
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_image(url="attachment://supreme.png")

        await ctx.send(embed=embed, file=file)

    @commands.command(help='Replaces the spaces in a string with a character')
    async def replacespace(self, ctx, char, *, text):
        await qembed(ctx, text.replace(' ', f' {char} '))

    @commands.command(help='Reverses some text')
    async def reverse(self, ctx, *, text):
        await qembed(ctx, text.replace(' ', ''.join(reversed(text))))


from discord.ext import commands
import discord
import os
import aiohttp
import onetimepad
import asyncio
import random
from owotext import OwO
import random
from iso639 import languages
import async_google_trans_new
import datetime
import time
import lyricsgenius
import utils.embed as qembed
geniustoken = os.environ['genius']
genius = lyricsgenius.Genius(geniustoken)
flipnotetoken = os.environ['tflipnote']
nasakey = os.environ['nasakey']


class fun(commands.Cog):
    """For the fun commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='smolpp',
                      hidden=True,
                      help='Tells someone that they have a smol pp')
    async def smolpp(self, ctx, *, thing):
        message = thing.capitalize()
        if message == ('You', 'I', 'They'):
            await qembed.send(ctx, f'{message} have a smol pp')
        else:
            await qembed.send(ctx, f'{message} has a smol pp')

    @commands.command(name='garsh', hidden=True)
    async def garsh(self, ctx):
        await qembed.send(
            ctx,
            'ASTRELLA OUTDATED <:Pog:790609728782073876> CERRET OVERRATED <:Pog:790609728782073876> GARSH ACTIVATED'
        )

    @commands.command(name='copypasta', hidden=True)
    async def copypasta(self, ctx):
        await ctx.send(
            'https://media.discordapp.net/attachments/788422986717200444/790627982813036580/Screenshot_2020-12-21_at_11.10.48_AM.png'
        )
        await ctx.send(
            'https://media.discordapp.net/attachments/788422986717200444/790627978774183936/Screenshot_2020-12-21_at_11.13.03_AM.png'
        )
        await ctx.send(
            'https://media.discordapp.net/attachments/788422986717200444/790627980681543730/Screenshot_2020-12-21_at_11.11.47_AM.png'
        )

    @commands.command(name='astrelladies',
                      help='The gif astrella used as he was losing the match')
    async def fakeembed(self, ctx):
        embed = discord.Embed(title='he ded',
                              description='can we get an f in the chat',
                              color=self.bot.embed_color, timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        embed.set_image(
            url=
            'https://media.tenor.com/images/b5e65cd0e7a8c8fef19af759a29d1acd/tenor.gif'
        )

        await ctx.send(embed=embed)


    @commands.command(
        name='translate',
        help='Translates text into another language with Google Translate')
    async def gtr(self, ctx, language, *, text: str):
        language = language.capitalize()
        try:
            try:
                lang = languages.get(name=language)
                g = async_google_trans_new.google_translator()
                gemb = discord.Embed(title='Google Translation',
                                    color=self.bot.embed_color, timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
                gemb.add_field(name='Input:', value=f'```\n{text}\n```')
                gemb.add_field(
                    name=f'Output in {language}:',
                    value=f'```\n{await g.translate(text, lang.alpha2)}\n```',
                    inline=False)
                await ctx.send(embed=gemb)
            except KeyError:
                await qembed.send(ctx, 'Language not found.')
        except TypeError:
            await qembed.send(ctx, 'This is different from other translate commands. In this, you actually say the language. `en` becomes `english`.')

    @commands.command(help='Finds the PPSIZE of a user')
    async def ppsize(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author.name
        else:
            user = user.name
        async with self.bot.session.get(
                'https://www.potatoapi.ml/ppsize') as f:
            f = await f.json()
            e = discord.Embed(title=f'{user}\'s ppsize:',
                              description=f['size'],
                              color=self.bot.embed_color, timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
            await ctx.send(embed=e)

    @commands.command(name='multiply', help='Multiplies a saying.')
    async def multiply(self, ctx, times: int, *, message=None):
        if ctx.author.id != self.bot.owner_id and times > 10:
            await qembed.send(ctx, 'No more than 10 times.')
        else:
            await qembed.send(ctx, f'{message} ' * times)

    @commands.command(help='Rascal MVP?')
    async def rascal(self, ctx):
        await qembed.send(
            ctx,
            'I cannot believe it. I can NOT fucking believe it. I simply REFUSE to believe the absolute imcompetent, negligence, of actually not, for ANY of these categories whatsoever, not picking up FUCKING Rascal. This guy doesn\'t get props by anyone, on no one\'s social media radar whatsoever. Everyone\'s talking about like "oh Smurf, ya know, Smurf he\'s-- poor Smurf!" think about Rascal! He literally came into the league at the start of the year, was the BEST Mei. He revolutionized the way you play Echo, and set the guidelines for everyone else in the league for MONTHS! Or pretty much like half the season! And then he comes into the Countdown Cup and plays the Genji, that actually turns the SanFranciscoShockaroundandtheywintheseriesagainstthePhiladelphiaFusion! How is NO ONE, on this PLANET talking about Rascal as one of the most underrated players of the year! It\'s absolutely... HURTING MY SOUL!'
        )

    @commands.command(name='lyrics', help='WIP', hidden=True)
    async def lyric(self, ctx, *, songname):
        cs = aiohttp.ClientSession()
        song = await cs.get('')

    @commands.command(help='Checks your speed.')
    async def react(self, ctx, seconds: int=None):
        if seconds and seconds > 31:
            return await qembed.send(ctx, 'You cannot specify more than 30 seconds. Sorry.')
        emg = str(random.choice(self.bot.emojis))
        if not seconds:
            seconds = 5
        embed = discord.Embed(description=f'React to this message with {emg} in {seconds} seconds.', timestamp=ctx.message.created_at, color=self.bot.embed_color).set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction(emg)
        start = time.perf_counter()
        def gcheck(reaction, user):
            return user == ctx.author and str(reaction.emoji) == emg
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=seconds * 1.5, check=gcheck)
        except asyncio.TimeoutError:
            embed = discord.Embed(description='You did not react in time', timestamp=ctx.message.created_at, color=self.bot.embed_color).set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
            await msg.edit(embed=embed)
        else:
            end = time.perf_counter()
            tim = end - start
            embed = discord.Embed(description=f'You reacted in **{tim:.2f}** seconds, **{seconds - tim:.2f}** off.', timestamp=ctx.message.created_at, color=self.bot.embed_color).set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
            await msg.edit(embed=embed)
                

    @commands.command(name='chucknorris',
                      aliases=['norris', 'chucknorrisjoke'],
                      help='Gets a random Chuck Norris Joke')
    async def norris(self, ctx):
        data = await self.bot.session.get(
            'https://api.chucknorris.io/jokes/random')
        joke = await data.json()
        e = discord.Embed(title='Chuck Norris Joke',
                          url=joke['url'],
                          description=joke['value'],
						  color=self.bot.embed_color, timestamp=ctx.message.created_at).set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=joke['icon_url'])
        await ctx.send(embed=e


def setup(bot):
    bot.add_cog(Fun(bot))
