# credit here goes to DeltaWing#0700 its kinda cool

import discord
from discord.ext import commands
import asyncpg
from prettytable import PrettyTable
from utils.default import qembed


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def sql(self, ctx, *, command):
        res = await self.bot.db.fetch(command)
        if len(res) == 0:
            return await ctx.message.add_reaction('✅')
        headers = list(res[0].keys())
        table = PrettyTable()
        table.field_names = headers
        for record in res:
            lst = list(record)
            table.add_row(lst)
        msg = table.get_string()
        await ctx.send(f"```\n{msg}\n```")

    @sql.error
    async def sql_error_handling(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            if isinstance(error, asyncpg.exceptions.UndefinedTableError):
                return await qembed(ctx, "This table does not exist.")
            elif isinstance(error, asyncpg.exceptions.PostgresSyntaxError):
                return await qembed(ctx, f"There was a syntax error:```\n {error} ```")
            else:
                await ctx.send(error)
        else:
            await ctx.send(error)


def setup(bot):
    bot.add_cog(Owner(bot))
