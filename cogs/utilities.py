import discord
from discord.ext import commands
import datetime
from utils.default import qembed
import humanize


class DeletedMessage:
    __slots__ = ('author', 'content', 'channel', 'guild', 'created_at', 'deleted_at', 'embed')

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


class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def deleted_message_for(self, index: int, channel_id: int):
        try:
            if index > len(self.bot.deleted_messages[channel_id]):
                return None
        except KeyError:
            return None

        readable_order = list(reversed(self.bot.deleted_messages[channel_id]))
        try:
            result = readable_order[index]
        except KeyError:
            return None
        else:
            return result

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        try:
            self.bot.deleted_messages[message.channel.id].append(DeletedMessage(message))
        except KeyError:
            self.bot.deleted_messages[message.channel.id] = []
            self.bot.deleted_messages[message.channel.id].append(DeletedMessage(message))
        if message.embeds:
            self.bot.last_embed = message.embeds[0]
            await message.channel.send('someone deleted an embed OOP')

    @commands.group(invoke_without_subcommand=True)
    async def snipe(self, ctx, index: int = 1, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel
        msg = self.deleted_message_for(index - 1, channel.id)
        if not msg:
            return await qembed(ctx, 'Nothing to snipe!')
        snipe = discord.Embed(title='Content:', description=msg.content, color=self.bot.embed_color,
                              timestamp=ctx.message.created_at)
        snipe.add_field(name='Message Stats', value=
                        f"""**Created At:** {humanize.naturaldelta(msg.created_at - datetime.datetime.utcnow())} ago
                        **Deleted At:** {humanize.naturaldelta(msg.deleted_at - datetime.datetime.utcnow())} ago
                        **Index:** {index} / {len(self.bot.deleted_messages[channel.id])}""")
        snipe.set_author(name=f'{str(msg.author)} said in #{channel.name}:', icon_url=str(msg.author.avatar_url))
        snipe.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=snipe)


def setup(bot):
    bot.add_cog(Utilities(bot))