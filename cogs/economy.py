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

import random
import typing

import discord
import humanize
from asyncpg import DataError
from discord.ext import commands

from utils.default import qembed


async def get_stats(ctx, user_id: int):
    try:
        data = dict(await ctx.bot.db.fetchrow('SELECT wallet, bank FROM economy WHERE user_id = $1', user_id))
    except TypeError:
        await ctx.bot.db.execute("INSERT INTO public.economy(user_id, wallet, bank) VALUES($1, 100, 100)", user_id)
        data = dict(await ctx.bot.db.fetchrow('SELECT wallet, bank FROM economy WHERE user_id = $1', user_id))

    wallet = data["wallet"]
    bank = data["bank"]

    return wallet, bank


class Economy(commands.Cog, command_attrs=dict(hidden=False)):
    """Earn some money. This ties in directly to the stock category."""

    def __init__(self, bot):
        self.bot = bot

    async def get_number(self, number: float, total: str):
        number = number.replace(",", "")
        if number.endswith("%"):
            number = number.strip("%")
            if not number.isdigit() or number > 100:
                raise commands.BadArgument("Invalid amount provided for percentage.")
            percentage = lambda percent, total_amount: (percent * total_amount) / 100
            amount = percentage(number, total)

        elif number == 'half':
            amount = total / 2

        elif number in ('max', 'all'):
            amount = total
        elif number.isdigit():
            amount = int(number)
            if amount == 0:
                raise commands.BadArgument("You need to provide an amount that results in over $0")
        else:
            raise commands.BadArgument("Invalid amount provided.")

        amount = round(amount)

        if amount > 100000000000:
            raise commands.BadArgument("Transfers of money over one billion are prohibited.")

        if amount > total:
            raise commands.BadArgument("That's more money than you have...")

        return amount

    @commands.command(help='Registers you into the database')
    async def register(self, ctx):
        try:
            await self.bot.db.execute("INSERT INTO public.economy(user_id, wallet, bank) VALUES($1, 100, 100)", id)
            await qembed(ctx, 'Successfully registered you!')
        except DataError:
            await qembed(ctx, 'You are already registered!')

    @commands.command(help='View yours or someone else\'s balance', aliases=['bal'])
    async def balance(self, ctx, user: discord.Member = None):
        wallet, bank = await get_stats(ctx, user.id if user else ctx.author.id)
        green_arrow = "<:green_arrow:811052039416447027>"
        e = discord.Embed(title=f'{user.name if user else ctx.author.name}\'s balance',
                          description=
                          f"{green_arrow} **Wallet**: ${humanize.intcomma(wallet)}\n"
                          f"{green_arrow} **Bank**: ${humanize.intcomma(bank)}\n"
                          f"{green_arrow} **Total**: ${humanize.intcomma(wallet + bank)}",
                          color=self.bot.embed_color, timestamp=ctx.message.created_at)

        e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=user.avatar_url if user else ctx.author.avatar_url)
        await ctx.send(embed=e)

    @commands.command(help='Gets the top 5 users.', aliases=['top', 'lb'])
    async def leaderboard(self, ctx, number: int = 5):
        if number > 10:
            return await qembed(ctx, 'No more than 10 please!')

        stats = await self.bot.db.fetch("SELECT * FROM economy ORDER BY bank+wallet DESC LIMIT $1", number)

        lb = [
            f'{number + 1}) {await self.bot.try_user(stats[number]["user_id"])} » ${stats[number]["wallet"] + stats[number]["bank"]}'
            for number, i in enumerate(range(number))
        ]

        lb = discord.Embed(title='Leaderboard',
                           color=self.bot.embed_color,
                           timestamp=ctx.message.created_at,
                           description='**TOP {} PLAYERS:**\n```py\n'.format(number) + "\n".join(lb) + '```')

        lb.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=lb)

    @commands.command(help='Deposits a set amount into your bank', aliases=['dep'])
    async def deposit(self, ctx, amount: str):
        wallet, bank = await get_stats(ctx, ctx.author.id)

        amount = self.get_number(amount, wallet)

        updated_wallet = amount
        bank += amount

        query = (
            """
            UPDATE economy SET wallet = $1, bank = $2
            WHERE user_id = $3
            """
        )

        await self.bot.db.execute(query, updated_wallet, bank, ctx.author.id)

        await qembed(ctx, f'You deposited **${humanize.intcomma(amount)}** into your bank.')

    @commands.command(help='Withdraws a set amount from your bank', aliases=['wd', 'with'])
    async def withdraw(self, ctx, amount: str):
        wallet, bank = await get_stats(ctx, ctx.author.id)

        amount = self.get_number(amount, wallet)

        wallet += amount
        updated_bank = bank - amount

        query = (
            """
            UPDATE economy SET wallet = $1, bank = $2
            WHERE user_id = $3
            """
        )

        await self.bot.db.execute(query, wallet, updated_bank, ctx.author.id)
        await qembed(ctx, f'You withdrew **${humanize.intcomma(amount)}** into your wallet.')

    @commands.command(help='Lets you send money over to another user', alises=['send', 'pay'])
    async def transfer(self, ctx, user: discord.Member, amount: str):
        author_wallet, _ = await get_stats(ctx, ctx.author.id)
        target_wallet, _ = await get_stats(ctx, user.id)

        amount = self.get_number(amount, author_wallet)

        author_wallet -= amount
        target_wallet += amount

        await self.bot.db.execute("UPDATE economy SET wallet = $1 WHERE user_id = $2", author_wallet, ctx.author.id)

        await self.bot.db.execute("UPDATE economy SET wallet = $1 WHERE user_id = $2", target_wallet, user.id)

        await qembed(ctx, f'You gave {user.mention} ${humanize.intcomma(amount)}')

    @commands.command(help='Takes a random amount of $ from someone', alises=['mug', 'steal'])
    async def rob(self, ctx, user: discord.Member):

        if random.randint(1, 2) == 2:
            desc = f"You try to rob {user.mention}, but the police see you and let you go with a warning."
            return await ctx.send(embed=ctx.embed(description=desc))

        author_wallet, author_bank = await get_stats(ctx, ctx.author.id)
        target_wallet, target_bank = await get_stats(ctx, user.id)

        if target_wallet == 0:
            return await qembed(ctx, 'That user has no money in their wallet. Shame on you for trying to rob them.')

        amount = random.randint(1, target_wallet)

        author_wallet += amount
        target_wallet -= amount

        author_query = (
            """UPDATE economy SET wallet = $1
            WHERE user_id = $2"""
        )
        target_query = (
            """UPDATE economy SET wallet = $1
            WHERE user_id = $2"""
        )

        await self.bot.db.execute(author_query, author_wallet, ctx.author.id)

        await self.bot.db.execute(target_query, target_wallet, user.id)

        await qembed(ctx, f'You stole **${humanize.intcomma(amount)}** from {user.mention}!')

    @commands.command(help='Work for some $$$')
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def work(self, ctx):
        author_wallet, author_bank = await get_stats(ctx, ctx.author.id)

        cash = random.randint(100, 500)

        query = (
            """UPDATE economy SET wallet = $1
            WHERE user_id = $3"""
        )

        await self.bot.db.execute(query, author_wallet + cash, ctx.author.id)
        if cash >= 250:
            amount = 'handsome'

        if cash <= 249:
            amount = 'meager'

        await qembed(ctx, f'You work and get paid a {amount} amount of **${cash}.**')

    @commands.command(help='Daily reward')
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.user)
    async def daily(self, ctx):
        wallet, _ = await get_stats(ctx, ctx.author.id)

        cash = random.randint(500, 1000)

        query = (
            """UPDATE economy SET wallet = $1
            WHERE user_id = $3"""
        )

        await self.bot.db.execute(query, wallet + cash, ctx.author.id)

        await qembed(ctx, f'You\'ve collected **${cash}** from the daily gift!')

    @commands.command(help='Fish in order to get some money.')
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def fish(self, ctx):
        wallet, _ = await get_stats(ctx, ctx.author.id)

        price = random.randint(20, 35)
        fish = random.randint(5, 20)
        cash = price * fish

        query = (
            """UPDATE economy SET wallet = $1
            WHERE user_id = $3"""
        )

        await self.bot.db.execute(query, wallet + cash, ctx.author.id)

        emoji = ['🐟', '🐠', '🐡']
        await qembed(ctx,
                     f'You travel to the local lake and catch {fish} fish {random.choice(emoji)}.'
                     f'Then you sell them to the market at a price of ${price}, totaling in at ${cash} for a days work.')

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
        wallet, _ = await get_stats(ctx, ctx.author.id)

        cash = random.randint(0, 500)

        query = (
            """UPDATE economy SET wallet = $1
            WHERE user_id = $3"""
        )

        await self.bot.db.execute(query, wallet + cash, ctx.author.id)
        city = cities["person"]["personal"]["city"]
        msg = f'You sit on the streets of {city} and a nice {random.choice(["man", "woman"])} hands you ${cash}.'
        await ctx.send(embed=ctx.embed(description=msg))

    @commands.command(help='Resets a cooldown on one command', aliases=['reset', 'cooldownreset'])
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def resetcooldown(self, ctx, command):
        eco = self.bot.get_cog("Economy")
        wallet, _ = await get_stats(ctx, ctx.author.id)
        if self.bot.get_command(command) not in eco.walk_commands():
            return await qembed(ctx,
                                f'You can only reset the cooldown for commands in this category. You can do `{ctx.clean_prefix}help Economy` to see all the commands.')

        if command == 'daily':
            return await qembed(ctx,
                                'You can\'t reset the daily command, sorry. '
                                'The whole point is that, well, it\'s meant to be once a day.')

        if wallet < 400:
            return await qembed(ctx, 'You need at least 400 dollars.')

        query = (
            """UPDATE economy SET wallet = $1
            WHERE user_id = $3"""
        )


        self.bot.get_command(command).reset_cooldown(ctx)
        await self.bot.db.execute(query, wallet - 400, ctx.author.id)
        await qembed(ctx,
                     f'Reset the command cooldown for the command `{command}` and subtracted $400 from your account.')


def setup(bot):
    bot.add_cog(Economy(bot))
