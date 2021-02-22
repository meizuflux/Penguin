import discord
from discord.ext import commands
import datetime

class DeletedMessage:
    __slots__ = ('author', 'content', 'channel', 'guild', 'created_at', 'deleted_at')
    def __init__(self, message):
        self.author = message.author
        self.content = message.content
        self.guild = message.guild
        self.created_at = message.created_at
        self.deleted_at = datetime.datetime.utcnow()

class EditedMessage:
    __slots__ = ('author', 'content', 'channel', 'guild', 'created_at', 'deleted_at')
    def __init__(self, message):
        self.author = message.author
        self.content = message.content
        self.guild = message.guild
        self.created_at = message.created_at
        self.deleted_at = datetime.datetime.utcnow()

class Utilites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot._deleted__messages_ = {}

    def deleted_message_for(self, index: int, channel_id: int):
        if index > len(self.bot._deleted__messages_[channel_id]):
            return None

        readable_order = reversed(self.bot._deleted__messages_[channel_id])
        try:
            result = readable_order[index]
        except KeyError:
            return None
        else:
            return result

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        await message.channel.send('lmao')
        if not self.bot._deleted__messages_[message.channel.id]:
            self.bot._deleted__messages_[message.channel.id] = []
        self.bot._deleted__messages_[message.channel.id].append(DeletedMessage(message))
    
    @commands.group(invoke_without_subcommand=True)
    async def snipe(self, ctx, index: int, channel: discord.TextChannel=None):
        if not channel:
            channel = ctx.channel
        msg = self.deleted_message_for(index, channel.id) 
        if not msg:
            return await ctx.send('hehe')
        await ctx.send(msg)



def setup(bot):
    bot.add_cog(Utilites(bot))