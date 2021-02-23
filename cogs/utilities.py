import discord
from discord.ext import commands
import datetime
from utils.default import qembed
import humanize


class DeletedMessage:
    __slots__ = ('author', 'content', 'channel', 'guild', 'created_at', 'deleted_at', 'del_embed', 'attachment')

    def __init__(self, message):
        self.author = message.author
        self.content = message.content
        self.guild = message.guild
        self.created_at = message.created_at
        self.deleted_at = datetime.datetime.utcnow()
        if message.embeds:
            self.del_embed = message.embeds[0]
        if message.attachments:
            self.attachment = message.attachments[0].url


class EditedMessage:
    __slots__ = ('author', 'before', 'channel', 'guild', 'created_at', 'edited_at', 'id')

    def __init__(self, message):
        self.author = message.author
        self.before = message.content
        #self.after = message.content
        self.guild = message.guild
        self.created_at = message.created_at
        self.edited_at = datetime.datetime.utcnow()
        self.id = message.id


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def deleted_message_for(self, index: int, channel_id: int):
        try:
            if index > len(self.bot.deleted_messages[channel_id]):
                return None
        except KeyError:
            return None
        
        if len(self.bot.deleted_messages[channel_id]) > 100:
            del self.bot.deleted_messages[channel_id][0]

        readable_order = list(reversed(self.bot.deleted_messages[channel_id]))
        try:
            result = readable_order[index]
        except KeyError:
            return None
        else:
            return result

    def edited_message_for(self, index: int, channel_id: int):
        try:
            if index > len(self.bot.edits[channel_id]):
                return None
        except KeyError:
            return None
        
        if len(self.bot.edits[channel_id]) > 100:
            del self.bot.edits[channel_id][0]

        readable_order = list(reversed(self.bot.edits[channel_id]))
        try:
            result = readable_order[index]
        except KeyError:
            return None
        else:
            return result

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        self.bot.deleted_messages[message.channel.id].append(DeletedMessage(message))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        self.bot.edits[before.channel.id].append(EditedMessage(before))

    @commands.group(invoke_without_subcommand=True)
    async def snipe(self, ctx, index: int = 1, channel: discord.TextChannel = None):
        if channel and channel.is_nsfw():
            return await qembed(ctx, 'no sorry')
        if not channel:
            channel = ctx.channel
        try:
            msg = self.deleted_message_for(index - 1, channel.id)
            try:
                await ctx.send(embed=msg.del_embed)
                content = 'User deleted an embed which is above.'
            except AttributeError:
                pass
                content = msg.content
        except IndexError:
            return await qembed(ctx, 'Nothing to snipe!')
        snipe = discord.Embed(title='Content:', description=content, color=self.bot.embed_color,
                              timestamp=ctx.message.created_at)
        if msg.attachment:
            snipe.add_field(name='Attachment', value=msg.attachment)
        snipe.add_field(name='Message Stats:', value=
                            f"**Created At:** {humanize.naturaldelta(msg.created_at - datetime.datetime.utcnow())} ago\n"
                            f"**Deleted At:** {humanize.naturaldelta(msg.deleted_at - datetime.datetime.utcnow())} ago\n"
                            f"**Index:** {index} / {len(self.bot.deleted_messages[channel.id])}")
        snipe.set_author(name=f'{str(msg.author)} said in #{channel.name}:', icon_url=str(msg.author.avatar_url))
        snipe.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=snipe)

    @snipe.command(help='yeah')
    async def edit(self, ctx, index: int = 1, channel: discord.TextChannel = None):
        if channel and channel.is_nsfw():
            return await qembed(ctx, 'no sorry')
        if not channel:
            channel = ctx.channel
        try:
            msg = self.edited_message_for(index - 1, channel.id)
        except IndexError:
            return await qembed(ctx, 'Nothing to snipe!')
        snipe = discord.Embed(title='Content:', description=msg.before, color=self.bot.embed_color,
                              timestamp=ctx.message.created_at)
        if msg.attachment:
            snipe.add_field(name='Attachment', value=msg.attachment)
        snipe.add_field(name='Message Stats:', value=
                            f"**Created At:** {humanize.naturaldelta(msg.created_at - datetime.datetime.utcnow())} ago\n"
                            f"**Edited At:** {humanize.naturaldelta(msg.edited_at - datetime.datetime.utcnow())} ago\n"
                            f"**Index:** {index} / {len(self.bot.deleted_messages[channel.id])}")
        snipe.set_author(name=f'{str(msg.author)} said in #{channel.name}:', icon_url=str(msg.author.avatar_url))
        snipe.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=snipe)


def setup(bot):
    bot.add_cog(Utilities(bot))
