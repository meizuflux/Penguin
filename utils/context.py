import discord
from discord.ext import commands


class CustomContext(commands.Context):
    @property
    def secret(self):
        return 'my secret here'
