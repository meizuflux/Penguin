import discord
from discord.ext import commands

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.bot.usage_counter += 1
        self.bot.command_usage[ctx.command.qualified_name] += 1



def setup(bot):
    bot.add_cog(Listeners(bot))