import discord
from discord.ext import commands
import datetime
from utils.default import qembed

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
        try:
            if index > len(self.bot._deleted__messages_[channel_id]):
                return None
        except KeyError:
            return None

        readable_order = self.bot._deleted__messages_[channel_id]
        readable_order.reverse
        try:
            result = readable_order[index-1]
        except KeyError:
            return None
        else:
            return result

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        await message.channel.send('lmao')
        try:
            self.bot._deleted__messages_[message.channel.id].append(DeletedMessage(message))
        except KeyError:
            self.bot._deleted__messages_[message.channel.id] = []
            self.bot._deleted__messages_[message.channel.id].append(DeletedMessage(message))
    
    @commands.group(invoke_without_subcommand=True)
    async def snipe(self, ctx, index: int=1, channel: discord.TextChannel=None):
        if not channel:
            channel = ctx.channel
        msg = self.deleted_message_for(index, channel.id) 
        if not msg:
            return await qembed(ctx, 'Nothing to snipe!')
        snipe = discord.Embed(title='Content:', description=f'```{msg.content}```', color=self.bot.embed_color, timestamp=ctx.message.created_at)
        snipe.add_field(name='Message Stats', value=f'**Created At:** {msg.created_at}\n**Deleted At:** {msg.deleted_at}\n**Index:** {index} / {len(self.bot._deleted__messages_[channel.id])}')
        snipe.set_author(name=f'{str(msg.author)} said in #{channel.name}:', icon_url=str(msg.author.avatar_url))
        snipe.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=snipe)


def setup(bot):
    bot.add_cog(Utilites(bot))