import difflib
import itertools

import discord
from discord.ext import commands

from utils.default import plural, qembed


class CustomHelp(commands.MinimalHelpCommand):
    def get_command_signature(self, command, ctx=None):
        """Method to return a commands name and signature."""
        sig = command.usage or command.signature
        if not sig and not command.parent:
            return f'`{self.clean_prefix}{command.name}`'
        if not command.parent:
            return f'`{self.clean_prefix}{command.name}` `{sig}`'
        if not sig:
            return f'`{self.clean_prefix}{command.parent}` `{command.name}`'
        else:
            return f'`{self.clean_prefix}{command.parent}` `{command.name}` `{sig}`'

    async def send_error_message(self, error):
        ctx = self.context
        destination = self.get_destination()
        embed = discord.Embed(description=error, color=ctx.bot.embed_color,
                              timestamp=ctx.message.created_at).set_footer(
            text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await destination.send(embed=embed)

    def get_opening_note(self):
        return "`<arg>`  means the argument is required\n`[arg]`  means the argument is optional"

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            joined = '`,\u2002`'.join(c.name for c in commands)
            emoji_dict = {
                'economy': "💵",
                'fun': "<:hahayes:739613910180692020>",
                'polaroid': "📸",
                'prefixes': "<:shrug:747680403778699304>",
                'useful': "<:bruhkitty:739613862302711840>",
                'utilities': "⚙️",
                "music": "<:bruhkitty:739613862302711840>",
                "jishaku": "<:verycool:739613733474795520>",
                "stocks": "<:stonks:817178220213567509>",
                "animepics": "<:prettythumbsup:806390638044119050>"
            }
            emoji = emoji_dict[heading.lower()]
            self.paginator.add_line(f'{emoji if emoji else None}  **{heading}**')

            self.paginator.add_line(f'> `{joined}`')
            # self.paginator.add_line()

    def get_ending_note(self):
        command_name = self.invoked_with
        return (
            "Type `{0}{1}` `[command]` for more info on a command.\n"
            "You can also type `{0}{1}` `[category]` for more info on a category.".format(
                self.clean_prefix, command_name
            )
        )

    async def send_pages(self):
        ctx = self.context
        destination = self.get_destination()
        for page in self.paginator.pages:
            await destination.send(await ctx.remove(embed=ctx.embed(description=page)))

    def add_subcommand_formatting(self, command):
        fmt = '{0} \N{EN DASH} {1}' if command.short_doc else '{0} \N{EN DASH} This command is not documented'
        self.paginator.add_line(fmt.format(self.get_command_signature(command), command.short_doc))

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(title="Error", description=str(error))
            await ctx.send(embed=embed)
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(title="Error", description=str(error))
            await ctx.send(embed=embed)
        else:
            raise error

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        no_category = '\u200bNo Category'

        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        for category, actual_commands in to_iterate:
            self.add_bot_commands_formatting(list(actual_commands), category)

        self.paginator.add_line()
        self.paginator.add_line(self.get_ending_note())

        await self.send_pages()

    @staticmethod
    def get_help(command, brief=True):
        real_help = command.help or "This command is not documented."
        return real_help if not brief else command.short_doc or real_help

    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description)

        note = self.get_opening_note()
        if note:
            self.paginator.add_line(note, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=False)
        if filtered:
            self.paginator.add_line('**%s %s**' % (cog.qualified_name, self.commands_heading))
            if cog.description:
                self.paginator.add_line(cog.description, empty=True)
            for command in filtered:
                self.add_subcommand_formatting(command)

        await self.send_pages()

    def get_command_help(self, command):
        ctx = self.context
        embed = ctx.embed(title=self.get_command_signature(command),
                              description=f'```{self.get_help(command, brief=False)}```')
        if alias := command.aliases:
            embed.add_field(name="Aliases", value=f"```{', '.join(alias)}```", inline=False)
        if isinstance(command, commands.Group):
            subcommand = command.commands
            value = "\n".join(f'{self.get_command_signature(c)} \N{EN DASH} {c.short_doc}' for c in subcommand)
            if len(value) > 1024:
                value = "\n".join(f'{self.get_command_signature(c)}' for c in subcommand)
            embed.add_field(name=plural("Subcommand(s)", len(subcommand)), value=value)

        return embed

    async def handle_help(self, command):
        if not await command.can_run(self.context):
            return await qembed(self.context, f'You don\'t have enough permissions to see the help for `{command}`')
        return await self.context.send(embed=self.get_command_help(command))

    async def send_group_help(self, group):
        await self.handle_help(group)

    async def send_command_help(self, command):
        await self.handle_help(command)

    # from pb https://github.com/PB4162/PB-Bot/blob/master/cogs/Help.py#L11-L102
    async def command_not_found(self, string: str):
        matches = difflib.get_close_matches(string, self.context.bot.command_list)
        if not matches:
            return f"No command called `{string}` found."
        match = "\n".join(matches[:1])
        return f"No command called `{string}` found. Did you mean `{match}`?"


class Helpful(commands.Cog, command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelp(command_attrs=dict(hidden=True, aliases=['halp', 'h', 'help_command'],
                                                         help='Literally shows this message. Jesus, do you really need this?'))
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(Helpful(bot))
