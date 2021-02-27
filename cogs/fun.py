import discord
from discord.ext import commands, flags
from io import BytesIO
from utils.default import qembed
from utils.bottom import from_bottom, to_bottom
import random
import time
import re
import json
import asyncio

mystbin_url = re.compile(
    r"(?:(?:https?://)?mystb\.in/)?(?P<ID>[a-zA-Z]+)(?:\.(?P<syntax>[a-zA-Z0-9]+))?"
)  # Thanks to Umbra's mystbin wrapper repo for this.


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
    @commands.command(usage='"supreme" [--dark|--light]', cls=flags.FlagCommand)
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

    @commands.command(help='Checks your speed.')
    async def react(self, ctx, seconds: int = None):
        if seconds and seconds > 31:
            return await qembed(ctx, 'You cannot specify more than 30 seconds. Sorry.')
        emg = str(random.choice(self.bot.emojis))
        if not seconds:
            seconds = 5
        embed = discord.Embed(description=f'React to this message with {emg} in {seconds} seconds.',
                              timestamp=ctx.message.created_at, color=self.bot.embed_color).set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction(emg)
        start = time.perf_counter()

        def gcheck(reaction, user):
            return user == ctx.author and str(reaction.emoji) == emg

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=seconds * 1.5, check=gcheck)
        except asyncio.TimeoutError:
            embed = discord.Embed(description='You did not react in time', timestamp=ctx.message.created_at,
                                  color=self.bot.embed_color).set_footer(text=f"Requested by {ctx.author}",
                                                                         icon_url=ctx.author.avatar_url)
            await msg.edit(embed=embed)
        else:
            end = time.perf_counter()
            tim = end - start
            embed = discord.Embed(description=f'You reacted in **{tim:.2f}** seconds, **{seconds - tim:.2f}** off.',
                                  timestamp=ctx.message.created_at, color=self.bot.embed_color).set_footer(
                text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
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
                          color=self.bot.embed_color, timestamp=ctx.message.created_at).set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=joke['icon_url'])
        await ctx.send(embed=e)

    @staticmethod
    def bottoms(mode, text):
        if mode == "to_bottom":
            return to_bottom(text)
        else:
            return from_bottom(text)

    async def check_mystbin(self, text):
        if match := mystbin_url.match(text):
            paste_id = match.group("ID")
            async with self.bot.session.get(f"https://mystb.in/api/pastes/{paste_id}") as resp:
                if resp.status != 200:
                    return text
                data = await resp.json()
                return data["data"]
        else:
            return text

    @commands.command(aliases=['bottom_decode', 'decode'])
    async def bottomdecode(self, ctx, *, text):
        text = await self.check_mystbin(text)
        bottoms = self.bottoms("from_bottom", text)

        if len(bottoms) > 500:
            return await qembed(ctx, str(await ctx.mystbin(bottoms)))
        await qembed(ctx, bottoms)

    @commands.command(aliases=['bottom_encode', 'encode'])
    async def bottomencode(self, ctx, *, text):
        text = await self.check_mystbin(text)
        bottoms = self.bottoms("to_bottom", text)

        if len(bottoms) > 500:
            return await qembed(ctx, str(await ctx.mystbin(bottoms)))
        await qembed(ctx, bottoms)

    @commands.command()
    async def spoiler(self, ctx, *, text):
        await ctx.send(''.join(char.replace(char, f'||{char}||') for char in text))

    @commands.command()
    async def partyfrog(self, ctx, *, text):
        await ctx.send(text.replace(" ", " <:a:partyfrog:815283360465289316> "))

    @commands.command()
    async def buildup(self, ctx, text):
        x = text
        await ctx.send('\n'.join(x[:+y] for y in range(len(x))) + '\n' + x + '\n'.join(x[:-y] for y in range(len(x))))


def setup(bot):
    bot.add_cog(Fun(bot))
