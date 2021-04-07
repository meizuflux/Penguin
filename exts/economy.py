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

import asyncio
import math
import random
import typing

import discord
import humanize
from asyncpg import UniqueViolationError
from discord.ext import commands

from utils.argparse import Arguments
from utils.eco import get_number, get_stats


class Economy(commands.Cog):
    """
    A unique Economy system. This is per-server specific, so your money will not carry over from server to server.
    Kicking the bot will reset the leaderboard, and all data will be lost.
    
    For all the entry that ask you to provide an amount, there are some different ways you can use it.
    You can call `all` or `max` to provide the max amount possible to use.
    You can say `half`, which is, well half.
    You can give a percentage, like `50%` to provide 50% of the max amount possible.
    Lastly, you can just provide a number.
    
    If any of those methods result in a number that is negative, more than you have, or more than 100 billion, it will raise an error.
    """

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.guild is not None

    @commands.command(help='Registers you into the database')
    async def register(self, ctx):
        query = (
            """
            INSERT INTO economy VALUES ($1, $2)
            """
        )
        try:
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id)
        except UniqueViolationError:
            return await ctx.send("You are already registered!")
        await ctx.send("Registered you into the database.")

    @commands.command()
    async def unregister(self, ctx):
        """Wipes your economy data on this server clean."""
        answer, message = await ctx.confirm("React to confirm before doing this. This action is irreversible.")
        if answer:
            query = (
                """
                DELETE FROM economy WHERE guild_id = $1 AND user_id = $2
                """
            )
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id)
            return await message.edit(content="Successfully unregistered you on this server.")
        await message.edit(content="Cancelling.")

    @commands.command(help='View yours or someone else\'s balance', aliases=['bal'])
    async def balance(self, ctx, user: discord.Member = None):
        auth = True
        if not user:
            user = ctx.author
            auth = False
        cash, bank = await get_stats(ctx, user.id, auth)
        e = ctx.embed(title=f'{user.name}\'s balance',
                      description=
                      f"💸 **Cash:** ${humanize.intcomma(cash)}\n"
                      f"🏦 **Bank:** ${humanize.intcomma(bank)}\n"
                      f"💰 **Total:** ${humanize.intcomma(cash + bank)}")
        e.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=e)

    @commands.command(aliases=("lb", "top", "server-leaderboard", "server-lb"), usage="[page=1] [--cash | --bank]")
    async def leaderboard(self, ctx, page: typing.Optional[int] = 1, item: str = None):
        """
        Sends the economy leaderboard.
        Server specific.
        If the page you provide is higher than the total amount of pages, it defaults to the last page.
        
        Optional Flags:
            `--cash`: Orders by users with the most cash (so you can rob them).
            `--bank`: Orders by users with the most money in the bank.
            
        If no flag is provided, it defaults to ordering by the total amount of money.
        
        Arguments:
            `page`: [Optional] The leaderboard page you would like to see. If not provided, it will send the first page.
        """
        lb_query = (
            """
            SELECT ROW_NUMBER() OVER (ORDER BY cash + bank DESC) AS number, user_id, cash + bank AS total
            FROM economy WHERE guild_id = $1 ORDER BY cash + bank DESC OFFSET $2 LIMIT 10
            """
        )
        count_query = (
            """
            SELECT COUNT(user_id) FROM economy
            WHERE guild_id = $1
            """
        )
        if item:
            parser = Arguments(allow_abbrev=False, add_help=False)
            parser.add_argument("-cash", "--cash", action="store_true", default=False)
            parser.add_argument("-bank", "--bank", action="store_true", default=False)

            try:
                args = parser.parse_args(item.split())
            except RuntimeError as e:
                return await ctx.send(embed=ctx.embed(description=str(e)))

            if args.cash:
                lb_query = (
                    """
                    SELECT ROW_NUMBER() OVER (ORDER BY cash DESC) AS number, user_id, cash AS total
                    FROM economy WHERE guild_id = $1 ORDER BY cash DESC OFFSET $2 LIMIT 10
                    """
                )
                count_query = (
                    """
                    SELECT COUNT(user_id) FROM economy
                    WHERE guild_id = $1 AND cash > 0
                    """
                )
            if args.bank:
                lb_query = (
                    """
                    SELECT ROW_NUMBER() OVER (ORDER BY bank DESC) AS number, user_id, bank AS total
                    FROM economy WHERE guild_id = $1 ORDER BY bank DESC OFFSET $2 LIMIT 10
                    """
                )
                count_query = (
                    """
                    SELECT COUNT(user_id) FROM economy
                    WHERE guild_id = $1 AND bank > 0
                    """
                )

        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                count = await conn.fetchval(count_query, ctx.guild.id)
                # need to check if the page is more than the amount allowed
                max_pages = math.ceil(count / 10)
                page = min(page, max_pages)

                data = await conn.fetch(lb_query, ctx.guild.id, (page * 10) - 10)

        lb = []
        for user in data:
            # Need to escape markdown
            name = discord.utils.escape_markdown(str(await self.bot.try_user(user['user_id'])))
            # Add a rickroll cuz I'm lazy and the formatting makes it look nice
            with_link = f" [{name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ, 'seriously, don\'t click.') "
            item = f"**{user['number']}.**{with_link}» **${humanize.intcomma(user['total'])}**"
            lb.append(item)
        lb.append(f"\nPage {page}/{max_pages}")

        embed = ctx.embed(title=f"{ctx.guild.name} Leaderboard", description="\n".join(lb))
        await ctx.send(embed=embed)

    @commands.command(help='Deposits a set amount into your bank', aliases=['dep'])
    async def deposit(self, ctx, amount: str):
        cash, bank = await get_stats(ctx, ctx.author.id)

        amount = get_number(amount, cash)

        if amount == 0:
            return await ctx.send(embed=ctx.embed(description="You have no cash."))

        query = (
            """
            UPDATE economy SET cash = cash - $1, bank = bank + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, amount, ctx.guild.id, ctx.author.id)

        await ctx.send(embed=ctx.embed(description=f'You deposited **${humanize.intcomma(amount)}** into your bank.'))

    @commands.command(help='Withdraws a set amount from your bank', aliases=['wd', 'with'])
    async def withdraw(self, ctx, amount: str):
        cash, bank = await get_stats(ctx, ctx.author.id)

        amount = get_number(amount, bank)
        if amount == 0:
            return await ctx.send(embed=ctx.embed(description="You have no cash."))

        query = (
            """
            UPDATE economy SET cash = cash + $1, bank = bank - $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, amount, ctx.guild.id, ctx.author.id)
        await ctx.send(embed=ctx.embed(description=f'You withdrew **${humanize.intcomma(amount)}** from your bank.'))

    @commands.command(help='Lets you send money over to another user', aliases=('send', 'pay', 'give'))
    async def transfer(self, ctx, user: discord.Member, amount: str):
        author_cash, _ = await get_stats(ctx, ctx.author.id)
        target_cash, _ = await get_stats(ctx, user.id, True)

        amount = get_number(amount, author_cash)

        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                await self.bot.db.execute("UPDATE economy SET cash = cash - $1 WHERE guild_id = $2 AND user_id = $3",
                                          amount, ctx.guild.id, ctx.author.id)
                await self.bot.db.execute("UPDATE economy SET cash = cash + $1 WHERE guild_id = $2 AND user_id = $3",
                                          amount, ctx.guild.id, user.id)

        await ctx.send(embed=ctx.embed(description=f'You gave {user.mention} **${humanize.intcomma(amount)}**'))

    @commands.command(help='Takes a random amount of $ from someone', alises=['mug', 'steal'])
    async def rob(self, ctx, user: discord.Member):

        if random.randint(1, 2) == 2:
            desc = f"You try to rob {user.mention}, but the police see you and let you go with a warning."
            return await ctx.send(embed=ctx.embed(description=desc))

        target_cash, _ = await get_stats(ctx, user.id, True)

        if target_cash == 0:
            return await ctx.send(
                embed=ctx.embed(description='That user has no cash. Shame on you for trying to rob them.'))

        amount = random.randint(1, target_cash)

        async with self.bot.db.acquire() as conn:
            async with conn.transaction():
                author_query = (
                    """
                    UPDATE economy SET cash = cash + $1
                    WHERE guild_id = $2 AND user_id = $3
                    """
                )
                target_query = (
                    """
                    UPDATE economy SET cash = cash - $1
                    WHERE guild_id = $2 AND user_id = $3
                    """
                )

                await conn.execute(target_query, amount, ctx.guild.id, user.id)
                await conn.execute(author_query, amount, ctx.guild.id, ctx.author.id)

        await ctx.send(embed=ctx.embed(description=f'You stole **${humanize.intcomma(amount)}** from {user.mention}!'))

    @commands.command(help='Work for some $$$')
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def work(self, ctx):
        with open('/usr/share/dict/words') as f:
            words = [word.strip() for word in f]
        word = str(random.choice(words).lower().replace("'", ""))
        correct_word = word[::-1]

        embed = ctx.embed(description=f"In 30 seconds, type this backwards: \n`{word}`\nType `cancel` to cancel.")

        message = await ctx.send(embed=embed)

        try:
            user_msg = await self.bot.wait_for("message", timeout=30,
                                               check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
        except asyncio.TimeoutError:
            embed.description = f"You didn't respond in time, the answer was `{correct_word}`"
            await message.edit(embed=embed)
        else:
            content = user_msg.content.lower()
            if content == correct_word:
                embed.description = "You got it! Transfering money now."
                m = await ctx.send(embed=embed)
                await message.delete()
                await asyncio.sleep(0.75)
            if content == "cancel":
                embed.description = "Cancelled."
                await message.delete()
                return await ctx.send(embed=embed)
            elif content not in (correct_word, "cancel"):
                embed.description = f"That's not the right word! The answer was `{correct_word}`"
                await message.delete()
                return await ctx.send(embed=embed)

        cash = random.randint(100, 500)

        query = (
            """
            UPDATE economy SET cash = cash + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, cash, ctx.guild.id, ctx.author.id)

        embed.description = f"I transfered **${cash}** to you."
        await m.edit(embed=embed)

    @commands.command(help='Daily reward')
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.user)
    async def daily(self, ctx):
        cash = random.randint(500, 1000)

        query = (
            """
            UPDATE economy SET cash = cash + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, cash, ctx.guild.id, ctx.author.id)

        await ctx.send(embed=ctx.embed(description=f'You\'ve collected **${cash}** from the daily gift!'))

    @commands.command(help='Fish in order to get some money.')
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def fish(self, ctx):
        valid_fish = ['🐟', '🐠', '🐡']
        correct_fish = random.choice(valid_fish)
        embed = ctx.embed(description=f"React with {correct_fish} in 10 seconds.")
        message = await ctx.send(embed=embed)
        valid_fish.append("❌")
        for fish in valid_fish:
            await message.add_reaction(fish)

        def terms(reaction, user):
            return user == ctx.author and reaction.message == message and str(reaction.emoji) in valid_fish

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=10, check=terms)
        except asyncio.TimeoutError:
            embed.description = "You did not react in time."
        else:
            emoji = str(reaction.emoji)
            if emoji == correct_fish:
                embed.description = "You got it! Transfering money to your account now."
                m = await ctx.send(embed=embed)
                await message.delete()
                await asyncio.sleep(0.75)
            if emoji == "❌":
                embed.description = "Cancelled."
                await ctx.send(embed=embed)
                return await message.edit(embed=embed)
            if emoji not in valid_fish:
                embed.description = "That's not the fish I told to to react with."
                return await message.edit(embed=embed)
            if emoji in valid_fish and emoji != correct_fish:
                embed.description = f"Wrong fish. The answer was {correct_fish}"
                return await message.edit(embed=embed)

        price = random.randint(20, 35)
        fish = random.randint(5, 20)
        cash = price * fish

        query = (
            """
            UPDATE economy SET cash = cash + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, cash, ctx.guild.id, ctx.author.id)

        embed.description = f'You travel to the local lake and catch **{fish}** fish {correct_fish}.\nThen you sell them to the market at a price of **${price}**, totaling in at **${cash}** for a days work.'

        await m.edit(embed=embed)

    @commands.command(help='Beg in the street')
    @commands.cooldown(rate=1, per=200, type=commands.BucketType.user)
    async def beg(self, ctx):
        """
        Beg in the street.
        33% chance to not get anything.
        """
        if random.randint(1, 3) == 1:
            return await ctx.send('You sit all day on the street, but collect no money.')
        async with self.bot.session.get('https://pipl.ir/v1/getPerson') as f:
            cities = await f.json()

        cash = random.randint(0, 500)

        query = (
            """
            UPDATE economy SET cash = cash + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, cash, ctx.guild.id, ctx.author.id)
        city = cities["person"]["personal"]["city"]
        msg = f'You sit on the streets of {city} and a nice {random.choice(["man", "woman"])} hands you ${cash}.'
        await ctx.send(embed=ctx.embed(description=msg))

    @commands.command(help='Resets a cooldown on one command', aliases=['reset', 'cooldownreset'])
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def resetcooldown(self, ctx, command):
        eco = self.bot.get_cog("Economy")
        if self.bot.get_command(command) not in eco.walk_commands():
            return await ctx.send(embed=ctx.embed(
                description=f'You can only reset the cooldown for entry in this category. You can do `{ctx.clean_prefix}help Economy` to see all the entry.'))
        cash, _ = await get_stats(ctx, ctx.author.id)
        if command == 'daily':
            return await ctx.send(embed=ctx.embed(description=
                                                  'You can\'t reset the daily command, sorry. '
                                                  'The whole point is that, well, it\'s meant to be once a day.'))

        if cash < 400:
            return ctx.send(embed=ctx.embed(description='You need at least 400 dollars.'))

        query = (
            """
            UPDATE economy SET cash = cash - $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        self.bot.get_command(command).reset_cooldown(ctx)
        await self.bot.db.execute(query, 400, ctx.guild.id, ctx.author.id)
        await ctx.send(embed=ctx.embed(
            description=f'Reset the command cooldown for the command `{command}` and subtracted **$400** from your account.'))

    @commands.command(aliases=("bankrob", "bank-rob"))
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def bank_rob(self, ctx):
        """
        Starts an interactive bank robbing session.
        
        This command takes no arguments.
        """
        numbers = ["<:better1:826124826493190175>", "<:better2:826124826456227870>", "<:better3:826124826401177640>",
                   "<:better4:826124826228817950>"]

        result = "".join(random.sample(numbers, 4))

        text = f"React to this in the same order as this: {result}"
        msg = await ctx.send(text, delete_after=30)

        for i in numbers:
            await msg.add_reaction(i)

        def terms(reaction, user):
            return user == ctx.author and reaction.message == msg

        var = ""
        for i in range(4):
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=15, check=terms)
            except asyncio.TimeoutError:
                return await msg.edit(content="You didn't pick fast enough.", delete_after=15)
            else:
                var += str(reaction.emoji)
                await msg.edit(content=f"{text}\n{var}")

        final = await ctx.send("<a:loading:747680523459231834> Attempting to enter the vault...", delete_after=15)
        await asyncio.sleep(1.5)
        if var == result:
            await final.edit(content=f"✅ The key matches! You enter the vault.")

        if var != result:
            return await final.edit(content="❌ The patterns do not match and the vault door stays shut.")

        valid_options = ("leave", "stay")
        choice = None

        amount = 0

        while True:
            message = await ctx.send(
                f"Would you like to stay in the vault and collect more money or would you like to leave? (`stay`/`leave`)\n💰 You currently have **${amount}** in your moneybag.",
                delete_after=15)

            try:
                msg = await self.bot.wait_for("message", timeout=15,
                                              check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            except asyncio.TimeoutError:
                choice = random.choice(valid_options)
                await ctx.send(f"You didn't respond in time, so I picked {choice} for you.", delete_after=15)

            content = msg.content.lower()
            if content in valid_options:
                choice = content

            elif not choice:
                await ctx.send("You need to send either `stay` or `leave`.")
                continue

            if choice == "stay":
                if random.choice((True, False)):
                    return await message.edit(
                        content="You push your luck too far and the cops catch you, leaving you with nothing!")

                grabbed_amount = random.randint(400, 1200)
                amount += grabbed_amount
                await ctx.send(f"💰 You grab another **${grabbed_amount}** to add to your moneybag.", delete_after=15)

            if choice == "leave":
                if amount == 0:
                    return await ctx.send(":( You have no money in your moneybag, I guess that's sad.")
                break

        query = (
            """
            UPDATE economy SET cash = cash + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        await self.bot.db.execute(query, amount, ctx.guild.id, ctx.author.id)

        await ctx.send(f"💰 You make off with a total of **${amount}** in your bag.")

    @commands.is_owner()
    @commands.group(name='set', hidden=True)
    async def _set(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @commands.command()
    async def cooldowns(self, ctx):
        eco_commands = {"rob": None, "daily": None, "bank_rob": None, "resetcooldown": None, "work": None, "beg": None,
                        "fish": None}
        for command in eco_commands:
            cmd = self.bot.get_command(command).is_on_cooldown(ctx)
            eco_commands[command] = "❌" if cmd else "✅"

        desc = "\n".join(f"{name}: {on_cooldown}" for name, on_cooldown in eco_commands.items())
        await ctx.send(embed=ctx.embed(title="Cooldowns", description=desc))

    @_set.command()
    async def cash(self, ctx, user: discord.User, amount: str):
        amount = amount.replace(",", "")
        if not amount.isdigit():
            raise commands.BadArgument("Amount must be a number.")
        amount = int(amount)
        query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        await self.bot.db.execute(query, amount, ctx.guild.id, user.id)
        await ctx.send(f"Set {user.name}'s cash to **{amount}**")

    @_set.command()
    async def bank(self, ctx, user: discord.User, amount: str):
        amount = amount.replace(",", "")
        if not amount.isdigit():
            raise commands.BadArgument("Amount must be a number.")
        amount = int(amount)
        query = (
            """
            UPDATE economy SET bank = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        await self.bot.db.execute(query, amount, ctx.guild.id, user.id)
        await ctx.send(f"Set {user.name}'s bank to **{amount}**")


def setup(bot):
    bot.add_cog(Economy(bot))
