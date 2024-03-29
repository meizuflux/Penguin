"""
Copyright (C) 2021 ppotatoo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import discord

"""komodo stop stealing"""

import difflib

from discord.ext import commands, menus
import utils


def get_sig(ctx, command):
    """Method to return a entry name and signature."""
    sig = command.usage or command.signature
    if not sig and not command.parent:
        return f"`{ctx.clean_prefix}{command.name}`"
    if not command.parent:
        return f"`{ctx.clean_prefix}{command.name}` `{sig}`"
    if not sig:
        return f"`{ctx.clean_prefix}{command.parent}` `{command.name}`"
    return f"`{ctx.clean_prefix}{command.parent}` `{command.name}` `{sig}`"


def add_formatting(ctx, command):
    fmt = "{0} \N{EN DASH} {1}" if command.short_doc else "{0}"
    return fmt.format(get_sig(ctx, command), command.short_doc)


class HelpSource(utils.HelpGroup):
    def __init__(self, ctx, data):

        cmds = []
        for cog in data:
            _commands = list(cog.get_commands())
            for command in _commands:
                if not command.hidden:
                    cmds.append(command)

        super().__init__(cmds, per_page=20)

    async def format_page(self, menu, entry):
        ctx = menu.ctx
        current_page = f"{menu.current_page + 1}/{self.get_max_pages()}"
        embed = menu.ctx.embed(title=f"{entry.key} | Page {current_page}")

        if menu.current_page == 0:
            description = (
                "`<argument>` means the argument is required\n"
                "`[argument]` means the argument is optional\n\n"
                f"Type `{ctx.clean_prefix}help` `[command]` for more info on a command.\n"
                f"You can also type `{ctx.clean_prefix}help` `[category]` for more info on a category.\n"
            )
            embed.description = description
            embed.add_field(
                name="About", value=f"```yaml\n{ctx.bot.description}```", inline=False
            )

            embed.add_field(
                name="Useful Links",
                value=f"[Invite Link]({ctx.bot.invite})\n"
                f"[Support Server Invite]({ctx.bot.support_invite})",
            )
        else:
            embed.description = "\n".join(
                add_formatting(ctx, command) for command in entry.items
            )

        return embed


class CogSource(menus.ListPageSource):
    def __init__(self, cog):
        _commands = list(cog.get_commands())
        cmds = sorted(
            [command for command in _commands if not command.hidden],
            key=lambda c: c.qualified_name,
        )
        super().__init__(cmds, per_page=20)

    async def format_page(self, menu, cmds):
        ctx = menu.ctx
        embed = ctx.embed(
            title=f"{cmds[0].cog_name} | Page {menu.current_page + 1}/{self.get_max_pages()}",
            description="\n".join(
                add_formatting(menu.ctx, command) for command in cmds
            ),
        )
        if menu.current_page == 0:
            cog = ctx.bot.get_cog(cmds[0].cog_name)
            embed.description = cog.description + "\n\n" + embed.description
        return embed


class HelpPages(menus.MenuPages):
    @menus.button("\N{BLACK SQUARE FOR STOP}\ufe0f", position=menus.Last(2))
    async def end_menu(self, _):
        await self.message.delete()
        self.stop()


class HelpCommand(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        """Method to return a entry name and signature."""
        sig = command.usage or command.signature
        if not sig and not command.parent:
            return f"`{self.clean_prefix}{command.name}`"
        if not command.parent:
            return f"`{self.clean_prefix}{command.name}` `{sig}`"
        if not sig:
            return f"`{self.clean_prefix}{command.parent}` `{command.name}`"
        return f"`{self.clean_prefix}{command.parent}` `{command.name}` `{sig}`"

    async def send_error_message(self, error):
        ctx = self.context
        destination = self.get_destination()
        embed = ctx.embed(description=error)
        await destination.send(embed=embed)

    def get_opening_note(self):
        return "`<arg>`  means the argument is required\n`[arg]`  means the argument is optional"

    def add_bot_commands_formatting(self, commands, heading):
        if commands:
            joined = "`,\u2002`".join(c.name for c in commands)
            emoji_dict = {
                "economy": "💵",
                "fun": "<:hahayes:739613910180692020>",
                "polaroid": "📸",
                "prefixes": "<:shrug:747680403778699304>",
                "useful": "<:bruhkitty:739613862302711840>",
                "utilities": "⚙️",
                "music": "<:bruhkitty:739613862302711840>",
                "jishaku": "<:verycool:739613733474795520>",
                "stocks": "<:stonks:817178220213567509>",
                "animepics": "<:prettythumbsup:806390638044119050>",
            }
            emoji = emoji_dict[heading.lower()]
            self.paginator.add_line(f'{emoji if emoji else ""}  **{heading}**')

            self.paginator.add_line(f"> `{joined}`")

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
        fmt = (
            "{0} \N{EN DASH} {1}"
            if command.short_doc
            else "{0} \N{EN DASH} This command is not documented"
        )
        self.paginator.add_line(
            fmt.format(self.get_command_signature(command), command.short_doc)
        )

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await self.send_error_message(await self.command_not_found(error))

        if isinstance(error, commands.CheckFailure):
            if ctx.bot.maintenance:
                return await ctx.send(
                    embed=ctx.embed(title="⚠️ Maintenence mode is active.")
                )
            if ctx.author.id in ctx.bot.blacklist:
                reason = ctx.bot.blacklist.get(
                    ctx.author.id, "No reason, you probably did something dumb."
                )
                embed = ctx.embed(
                    title="⚠️ You are blacklisted from using this bot globally.",
                    description=(
                        f"**Blacklisted For:** {reason}"
                        f"\n\nYou can join the support server [here]({ctx.bot.support_invite}) "
                        f"if you feel this is a mistake."
                    ),
                )
                try:
                    await ctx.author.send(embed=embed)
                except discord.Forbidden:
                    await ctx.send(embed=embed)
                finally:
                    return

        await ctx.send(str(error))

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        nono = ["jishaku", "owner", "commanderrorhandler", "helpful"]
        data = [
            cog for cog in bot.cogs.values() if cog.qualified_name.lower() not in nono
        ]
        data = sorted(data, key=lambda c: c.qualified_name)
        pages = HelpPages(source=HelpSource(ctx, data))

        await pages.start(ctx)

    def get_help(self, command, brief=True):
        ctx = self.context
        real_help = command.help or "This command is not documented."
        help = real_help if not brief else command.short_doc or real_help
        return real_help.format(support=ctx.bot.support_invite, prefix=ctx.clean_prefix)

    async def send_cog_help(self, cog):
        if cog.qualified_name == "AAAAAA":
            return await self.send_error_message(
                await self.command_not_found(cog.qualified_name)
            )
        ctx = self.context

        pages = HelpPages(source=CogSource(cog))

        await pages.start(ctx)

    def get_command_help(self, command):
        ctx = self.context
        embed = ctx.embed(
            title=self.get_command_signature(command),
            description=self.get_help(command, brief=False),
        )
        if alias := command.aliases:
            embed.add_field(
                name="Aliases", value=f"```{', '.join(alias)}```", inline=False
            )
        if isinstance(command, commands.Group):
            subcommand = command.commands
            value = "\n".join(
                f'{self.get_command_signature(c)} \N{EN DASH} {c.short_doc if c.short_doc else "This command is not documented"}'
                for c in subcommand
            )
            if len(value) > 1024:
                value = "\n".join(
                    f"{self.get_command_signature(c)}" for c in subcommand
                )
            embed.add_field(
                name=ctx.plural("Subcommand(s)", len(subcommand)), value=value
            )

        return embed

    async def handle_help(self, command):
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


def setup(bot):
    bot.help_command = HelpCommand(command_attrs=dict(hidden=True, aliases=["h"]))


def teardown(bot):
    bot.help_command = commands.MinimalHelpCommand()
