import time
import traceback
from io import BytesIO

import discord
import timeago as timesince
from discord.ext import commands


def escape(text: str):
    mark = [
        '`',
        '_',
        '*'
    ]
    text = text
    for item in mark:
        text = text.replace(item, f'\u200b{item}')
    return text


def traceback_maker(err, advance: bool = True):
    """ A way to debug your code anywhere """
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = '```py\n{1}{0}: {2}\n```'.format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"


def timetext(name):
    """ Timestamp, but in text form """
    return f"{name}_{int(time.time())}.txt"


async def qembed(ctx, text):
    bot = ctx.bot
    embed = discord.Embed(description=text[:2048], color=bot.embed_color, timestamp=ctx.message.created_at).set_footer(
        text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)


def timeago(target):
    """ Timeago in easier way """
    return timesince.format(target)


def date(target, clock=True):
    """ Clock format using datetime.strftime() """
    if not clock:
        return target.strftime("%d %B %Y")
    return target.strftime("%d %B %Y, %H:%M")


def plural(text, size):
    logic = size == 1
    target = (("(s)", ("s", "")), ("(is/are)", ("are", "is")))
    for x, y in target:
        text = text.replace(x, y[logic])
    return text


def responsible(target, reason):
    """ Default responsible maker targeted to find user in AuditLogs """
    creator = f"[ {target} ]"
    if not reason:
        return f"{creator} no reason given..."
    return f"{creator} {reason}"


def actionmessage(case, mass=False):
    """ Default way to present action confirmation in chat """
    output = f"**{case}** the user"

    if mass:
        output = f"**{case}** the IDs/Users"

    return f"✅ Successfully {output}"


async def prettyresults(ctx, filename: str = "Results", resultmsg: str = "Here's the results:", loop=None):
    """ A prettier way to show loop results """
    if not loop:
        return await ctx.send("The result was empty...")

    pretty = "\r\n".join(
        f"[{str(num).zfill(2)}] {data}"
        for num, data in enumerate(loop, start=1)
    )

    if len(loop) < 15:
        return await ctx.send(f"{resultmsg}```ini\n{pretty}```")

    data = BytesIO(pretty.encode('utf-8'))
    await ctx.send(
        content=resultmsg,
        file=discord.File(data, filename=timetext(filename.title()))
    )


class CantRun(commands.CommandError):
    def __init__(self, message, *arg):
        super().__init__(message=message, *arg)
