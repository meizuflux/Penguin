import discord
from discord.ext import commands

def mng_msg():
    def predicate(ctx):
        if ctx.author.id == 777893499471265802:
            return True
        if ctx.guild:
            if ctx.author.guild_permissions.manage_messages == True:
                return True
        else:
            return False

    return commands.check(predicate)

def mng_gld():
    def predicate(ctx):
        if ctx.author.id == ctx.bot.author_id:
            return True
        if ctx.author.guild_permissions.manage_guild == True:
            return True
        else: 
            return False
    return commands.check(predicate)