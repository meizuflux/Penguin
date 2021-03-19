import asyncio
import asyncio
import base64
import discord
import json
import os
import random
import re
import string
import textwrap
import time
import timeit
import typing
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
from discord.ext import commands, flags
from discord.ext.commands.cooldowns import BucketType
from io import BytesIO
from jishaku.functools import executor_function

from cogs.polaroid_manipulation import get_image_url
from utils.bottom import from_bottom, to_bottom
from utils.default import qembed

mystbin_url = re.compile(
    r"(?:(?:https?://)?mystb\.in/)?(?P<ID>[a-zA-Z]+)(?:\.(?P<syntax>[a-zA-Z0-9]+))?"
)  # Thanks to Umbra's mystbin wrapper repo for this.

morse_dict = {
    # Letters
    "a": ".-",
    "b": "-...",
    "c": "-.-.",
    "d": "-..",
    "e": ".",
    "f": "..-.",
    "g": "--.",
    "h": "....",
    "i": "..",
    "j": ".---",
    "k": "-.-",
    "l": ".-..",
    "m": "--",
    "n": "-.",
    "o": "---",
    "p": ".--.",
    "q": "--.-",
    "r": ".-.",
    "s": "...",
    "t": "-",
    "u": "..-",
    "v": "...-",
    "w": ".--",
    "x": "-..-",
    "y": "-.--",
    "z": "--..",
    # Numbers
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    # Punctuation
    "&": ".-...",
    "'": ".----.",
    "@": ".--.-.",
    ")": "-.--.-",
    "(": "-.--.",
    ":": "---...",
    ",": "--..--",
    "=": "-...-",
    "!": "-.-.--",
    ".": ".-.-.-",
    "-": "-....-",
    "+": ".-.-.",
    '"': ".-..-.",
    "?": "..--..",
    "/": "-..-.",
}


class Fun(commands.Cog):
    """For the fun commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def morse(self, ctx):
        """Translate to and from morse code!"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @morse.command(aliases=['encode'])
    async def code(self, ctx, *, text):
        if text == "":
            raise commands.BadArgument('You must provide a string of text to translate.')
        if "    " in text:
            raise commands.BadArgument('Unable to translate morse code. Found 4 spaces in morse code string.')
        translation = ""

        words = text.split(" ")

        for word in words:
            w = [morse_dict[char.lower()] for char in word if char.lower() in morse_dict]
            translation += " ".join(w)
            translation += "   "

        output = translation.rstrip()
        if len(output) > 2000: output = "Output was too long so I put it here -> " + await ctx.mystbin(output)
        await ctx.send(output)

    @morse.command(name='decode', usage='<morse>')
    async def morse_decode(self, ctx, *, morse='.. -.. -.-'):
        """Decodes a Morse Code string."""
        if morse == "":
            raise commands.BadArgument('You must provide a string of text to translate.')
        translation = ""

        words = morse.split("   ")

        for morse_word in words:
            chars = morse_word.split(" ")
            for char in chars:
                for k, v in morse_dict.items():
                    if char == v:
                        translation += k
            translation += " "
        await ctx.send(translation.rstrip(), allowed_mentions=discord.AllowedMentions().none())

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
    @commands.command(usage='[--text "supreme"] [--dark|--light]', cls=flags.FlagCommand)
    async def supreme(self, ctx, **flags):
        """
        Makes a custom supreme logo
        example: supreme --text "hey guys" --dark
        """
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
        await qembed(ctx, text[::-1])

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
            _, _ = await self.bot.wait_for('reaction_add', timeout=seconds * 1.5, check=gcheck)
        except asyncio.TimeoutError:
            embed = ctx.embed(description='You did not react in time')
            await msg.edit(embed=embed)
        else:
            end = time.perf_counter()
            tim = end - start
            embed = discord.Embed(description=f'You reacted in **{tim:.2f}** seconds, **{seconds - tim:.2f}** off.')
            await msg.edit(embed=embed)

    @commands.command(name='chucknorris', aliases=['norris', 'chucknorrisjoke'])
    async def norris(self, ctx):
        """Tells a random Chuck Norris joke."""
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

    @commands.command(aliases=['bottom_decode'])
    async def bottomdecode(self, ctx, *, text):
        text = await self.check_mystbin(text)
        bottoms = self.bottoms("from_bottom", text)

        if len(bottoms) > 500:
            return await qembed(ctx, str(await ctx.mystbin(bottoms)))
        await qembed(ctx, bottoms)

    @commands.command(aliases=['bottom_encode'])
    async def bottomencode(self, ctx, *, text):
        text = await self.check_mystbin(text)
        bottoms = self.bottoms("to_bottom", text)

        if len(bottoms) > 500:
            return await qembed(ctx, str(await ctx.mystbin(bottoms)))
        await qembed(ctx, bottoms)

    @commands.command()
    async def spoiler(self, ctx, *, text):
        await ctx.send(''.join(char.replace(char, f'||{char}||') for char in text),
                       allowed_mentions=discord.AllowedMentions().none())

    @commands.command()
    async def partyfrog(self, ctx, *, text):
        await ctx.send(text.replace(" ", " <a:partyfrog:815283360465289316> "),
                       allowed_mentions=discord.AllowedMentions().none())

    @commands.command()
    async def clap(self, ctx, *, text):

        await ctx.send(text.replace(" ", " :clap: "), allowed_mentions=discord.AllowedMentions().none())

    @commands.command()
    async def buildup(self, ctx, text):
        await ctx.send('\n'.join(text[:+char] for char in range(len(text))) + '\n' + text + '\n'.join(
            text[:-char] for char in range(len(text))),
                       allowed_mentions=discord.AllowedMentions().none())

    @commands.command()
    async def ship(self, ctx, user_1: discord.Member, user_2: discord.Member = None):
        if not user_2:
            user_2 = ctx.author
        random.seed(int(user_1.id) + int(user_2.id))
        love = random.randint(1, 100)
        await qembed(ctx,
                     f'I calculate that the love between {user_1.mention} and {user_2.mention} is {str(love)[:2]}%')

    @commands.command(aliases=['ppsize'])
    async def pp(self, ctx, user: discord.Member = None):  # [p]pp
        if not user:
            user = ctx.author
        random.seed(int(user.id))
        await qembed(ctx, f'8{"=" * random.randint(1, 25)}D')

    @commands.command()
    async def roo(self, ctx):
        """Roo.
        Sends a random "roo" emoji.
        """
        await ctx.send(random.choice([str(i) for i in self.bot.emojis if i.name.startswith("roo")]))

    @commands.group(help='Some functions with base64', aliases=['b64'])
    async def base64(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(str(ctx.command))

    @base64.command()
    async def decode(self, ctx, *, string):
        """Decodes a base64 string."""
        decoded_string = base64.b64decode(string)
        decoded = decoded_string.decode('utf-8')
        await qembed(ctx, decoded)

    @base64.command()
    async def encode(self, ctx, *, string):
        """Encodes a base64 string."""
        encoded_encoded_string = base64.b64encode(string.encode('utf-8'))
        decoded = encoded_encoded_string.decode('utf-8')
        await qembed(ctx, decoded)

    @executor_function
    def do_typerace(self, text):
        img = Image.open('assets/black.jpeg')
        width, height = img.size
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('assets/Montserrat-Regular.ttf', 125)
        wrapped = textwrap.wrap(text, width=24)
        w, h = draw.textsize(text)
        draw.text((40, 40), '\n'.join(wrapped), (255, 255, 255), font=font)
        byte = BytesIO()
        img.save(byte, 'PNG')
        byte.seek(0)
        return byte

    @commands.max_concurrency(1, per=BucketType.channel, wait=False)
    @commands.cooldown(1, 30, BucketType.user)
    @commands.command(aliases=["tr"])
    async def typeracer(self, ctx):
        """Who's the fastest typer?"""
        async with self.bot.session.get("https://api.quotable.io/random") as f:
            data = await f.json()
        text = data["content"]

        embed = ctx.embed(title='You have 60 seconds to type this:')
        embed.set_image(url="attachment://typeracer.png")

        msg = await ctx.send(embed=embed, file=discord.File(await self.do_typerace(text), "typeracer.png"))
        start = time.perf_counter()

        try:
            message = await self.bot.wait_for("message", timeout=60,
                                              check=lambda m: m.content == text and m.channel == ctx.channel)
        except asyncio.TimeoutError:
            await msg.reply("Nobody got it.")
        else:
            winn = ctx.embed(
                description=f"**{message.author}** got it in **{time.perf_counter() - start:.2f}** seconds!")
            await msg.reply(embed=winn)

    @typeracer.error
    async def concur(self, ctx, error):
        if isinstance(error, commands.MaxConcurrencyReached):
            return await ctx.send("There is already an ongoing session of typeracer in this channel.")

    @executor_function
    def do_ahb(self, text):
        img = Image.open('assets/ahb.jpeg')

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('assets/Helvetica Bold.ttf', 17)

        wrapped = textwrap.wrap(text, width=20)

        down = 90
        for text in wrapped:
            width, height = draw.textsize(text, font=font)
            draw.text(((img.width - width) / 2, down), text, font=font)
            down += height + 10

        byte = BytesIO()
        img.save(byte, 'PNG')
        byte.seek(0)
        return byte

    @commands.cooldown(1, 10, BucketType.user)
    @commands.command(aliases=['alwayshasbeen', 'ahb'], usage='[text]')
    async def always_has_been(self, ctx, *, text='Wait, it\'s all Ohio?'):
        """Wait, it's all Ohio?"""
        if len(text) > 100:
            return await ctx.send("Sorry, please keep the text under 100 characters.")
        embed = ctx.embed().set_image(url="attachment://always_has_been.jpeg")
        await ctx.send(embed=embed, file=discord.File(await self.do_ahb(text), "always_has_been.jpeg"))

    @commands.command()
    async def sadcat(self, ctx):
        """Sends a sadcat."""
        embed = ctx.embed(title=random.choice(["<:Sadge:789590510225457152>", "<:sad:790608581615288320>"]))
        embed.set_image(url=await self.bot.alex.sadcat())
        await ctx.send(embed=embed)

    @commands.command(aliases=['ach'])
    async def achievement(self, ctx, *, text):
        """Sends a Minecraft Achievement."""
        embed = ctx.embed()
        embed.set_image(url='attachment://achievement.png')
        image = discord.File(await (await self.bot.alex.achievement(text=text)).read(), "achievement.png")
        await ctx.send(embed=embed, file=image)

    @commands.command()
    async def mock(self, ctx, *, text: str = None):
        content = None
        if isinstance(text, discord.Message):
            content = text.content
        elif text:
            content = text
        if ctx.message.reference:
            content = ctx.message.reference.resolved.content
        if not content and not text:
            content = ctx.author.nick or ctx.author.name
        await ctx.send(
            "".join(
                i.upper() if num % 2 == 0 else i.lower()
                for num, i in enumerate(content)
            )
        )

    @commands.command()
    async def caption(self, ctx, *,
                      image: typing.Union[discord.PartialEmoji, discord.Member, discord.User, str] = None):
        image = await get_image_url(ctx, image)
        data = {
            "Content": str(image),
            "Type": "CaptionRequest",
        }
        headers = {"Content-Type": "application/json; charset=utf-8"}
        caption_url = "https://captionbot.azurewebsites.net/api/messages"
        async with self.bot.session.post(caption_url, data=json.dumps(data), headers=headers) as resp:
            caption = await resp.text()
        await ctx.send(embed=ctx.embed(title=caption).set_image(url=image))

    @commands.command()
    async def pepe(self, ctx):
        frog = ":frog:"
        circle = ":red_circle:"
        pepe = (
            frog * 7,
            frog * 10,
            frog * 12,
            frog * 13,
            f"{frog * 2}⚪️⚫️⚫️⚪️{frog * 3}⚪️⚫️⚫️⚪️",
            ":frog:⚪️⚫️⚫️⚪️⚫️⚪️:frog:⚪️⚫️⚫️⚪️⚫️⚪️",
            ":frog:⚪️⚫️⚪️⚫️⚫️⚪️:frog:⚪️⚫️⚪️⚫️⚫️⚪️",
            ":frog::frog:⚪️⚫️⚪️⚪️:frog::frog::frog:⚪️⚫️⚪️⚪️",
            frog * 13,
            f"{circle * 2}{frog * 11}",
            ":frog::red_circle::red_circle::frog::frog::frog::frog::frog::frog::frog::frog::frog:",
            f"{frog * 2}{circle * 10}",
            f"{frog * 3}{circle * 8}",
            frog * 10,
            frog * 9,
            frog * 8
        )
        await ctx.send("\n".join(pepe))

    @commands.command()
    async def animequote(self, ctx):
        async with self.bot.session.get("https://some-random-api.ml/animu/quote") as f:
            data = await f.json()
        embed = ctx.embed(title=f'{data.get("characther")} said in{data.get("anime")}',
                          description=data.get("sentence"))
        await ctx.send(embed=embed)

    @commands.command(aliases=['trumpquote', 'trump_quote'])
    async def trump(self, ctx):
        async with self.bot.session.get("https://www.tronalddump.io/random/quote") as f:
            data = await f.json()
        link = data["_links"]["self"]["href"]
        embed = ctx.embed(title='Donald Trump once said...', description=data.get("value"), url=link)
        await ctx.send(embed=embed)

    @commands.command()
    async def dadjoke(self, ctx):
        headers = {
            'Accept': 'application/json'
        }
        async with self.bot.session.get("https://icanhazdadjoke.com/", headers=headers) as f:
            dad = await f.json()
        await ctx.send(embed=ctx.embed(description=dad.get("joke")))

    @commands.command(aliases=['bt'])
    async def bigtext(self, ctx, *, text):
        """Makes the specified text bigger."""
        if len(text) > 50: return await ctx.send("Less than 50 characters please!")
        output = ""
        special = {"<": ":arrow_left:", ">": ":arrow_right:", "!": ":exclamation:", "?": ":question:"}
        for char in text:
            char = char.lower()
            if char != ' ' and char in string.ascii_lowercase:
                output += f":regional_indicator_{char}:"
            if char == ' ':
                output.append(f"  ")
            if char in string.digits:
                output += f"{char}\N{combining enclosing keycap}"
            for arrow, emoji in special.items():
                if arrow in char:
                    output += emoji
        if not output: output = "Output came out empty."
        await ctx.send(output)

    @commands.command(aliases=['point'])
    async def pepepoint(self, ctx):
        """Reacts to the next message.
        Emoji is "PepePoint". If no message is sent in 60 seconds it times out."""
        try:
            message = await self.bot.wait_for("message", timeout=60, check=lambda m: m.channel == ctx.channel)
        except asyncio.TimeoutError:
            return
        else:
            await message.add_reaction('<:PepePoint:759934591590203423>')

    @commands.command()
    async def whyarentyoucoding(self, ctx):
        """Grabs the latest "Why aren't you coding?" comic.
        New comic every weekday according to their site. 
        Give them some love at https://whyarentyoucoding.com"""
        url = 'https://whyarentyoucoding.com'
        async with self.bot.session.get(url) as f:
            data = await f.text()
        soup = BeautifulSoup(data, 'lxml')
        img = url + soup.find_all('img')[1]['src']
        await ctx.send(
            embed=ctx.embed(title=str(soup.title.string), url=soup.find_all("link")[1]['href']).set_image(url=img))

    @commands.command()
    async def cat(self, ctx):
        """Random cat."""
        path = '/home/ppotatoo/images/cats'
        r = random.choice(os.listdir(path))
        f = discord.File(path + "/" + r, filename=r)
        e = ctx.embed().set_image(url=f"attachment://{r}")
        await ctx.send(file=f, embed=e)

    @commands.command()
    async def dog(self, ctx):
        """Random dog."""
        path = '/home/ppotatoo/images/dogs'
        r = random.choice(os.listdir(path))
        f = discord.File(path + "/" + r, filename=r)
        e = ctx.embed().set_image(url=f"attachment://{r}")
        await ctx.send(file=f, embed=e)

    @commands.command()
    async def dutch(self, ctx):
        await message.send('uwu')

def setup(bot):
    bot.add_cog(Fun(bot))
