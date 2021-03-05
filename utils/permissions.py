from discord.ext import commands


def mng_msg():
    def predicate(ctx):
        if ctx.author.id in ctx.bot.owner_ids:
            return True
        if ctx.guild:
            if ctx.author.guild_permissions.manage_messages:
                return True
        else:
            return False

    return commands.check(predicate)


def mng_gld():
    def predicate(ctx):
        if ctx.author.id in ctx.bot.owner_ids:
            return True
        return bool(ctx.author.guild_permissions.manage_guild)

    return commands.check(predicate)
