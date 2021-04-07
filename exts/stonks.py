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

import math

import discord
import humanize
import tabulate
from discord.ext import commands, tasks

from utils.eco import get_stats

FINNHUB_URL = "https://finnhub.io/api/v1/"


class Stocks(commands.Cog, command_attrs=dict(hidden=False)):
    """
    Buy and sell stocks. Prices are directly related to real life prices.
    This works with the Economy entry.
    """

    def __init__(self, bot):
        """Creates the cog."""
        self.bot = bot
        self.finnhub = self.bot.settings['keys']['finnhub']
        self.del_none.start()

    @tasks.loop(hours=12)
    async def del_none(self):
        await self.bot.db.execute('DELETE FROM stocks WHERE amount = 0')

    @commands.command()
    async def dividend(self, ctx, dividend: float, stock_price: float, amount: int):
        """
        dividend can be find by searching it on google on the information card find `Div yield` you can enter it like 5.79 for 5.79%
        Stock price is just the stock price
        Amount is the amount of stocks you own
        """
        total_price = stock_price * amount
        real_dividend = dividend / 100
        price = total_price * real_dividend
        return await ctx.send(price)

    @commands.command()
    async def buy(self, ctx, ticker: str = 'MSFT', amount='1'):
        """Buys a stock
        You can view a list of all stocks at https://stockanalysis.com/stocks/
        """
        cash, _ = await get_stats(ctx, ctx.author.id)
        ticker = ticker.upper()

        async with self.bot.session.get(f'{FINNHUB_URL}/quote?symbol={ticker}&token={self.finnhub}') as data:
            stock = await data.json()

        if stock["c"] == 0:
            return await ctx.send('Invalid stock provided.')

        price: int = round(stock["c"])
        humanized_price: str = humanize.intcomma(price)

        if amount == 'max':
            amount = math.floor(cash / price)
            if amount == 0:
                return await ctx.send(f'You don\'t have enough money to buy a share of {ticker}. '
                                      f'You need **${humanize.intcomma(price - cash)}** more in order to purchase a share of {ticker}.')

        try:
            if int(amount):
                amount = int(amount)
        except ValueError:
            return await ctx.send("Invalid amount provided.")

        total: int = amount * price
        humanized_total: str = humanize.intcomma(total)

        share: str = ctx.plural("share(s)", amount)

        if total > cash:
            return await ctx.send(f'You need **${humanize.intcomma(total - cash)}** more in order to purchase'
                                  f' **{amount}** {share} of **{ticker}**')

        answer, message = await ctx.confirm(
            f'Confirm to buy **{amount}** {share} of **{ticker}** at **${humanized_price}**'
            f' per share for a total of **${humanized_total}**.'
        )

        if answer:
            stock_sql = (
                "INSERT INTO stocks VALUES($1, $2, $3, $4) "
                "ON CONFLICT (guild_id, user_id, ticker) "
                "DO UPDATE SET amount = stocks.amount + $4"
            )

            eco_values = (cash - total, ctx.author.id, ctx.guild.id)

            await self.bot.db.execute("UPDATE economy SET cash = $1 WHERE user_id = $2 AND guild_id = $3", *eco_values)
            await self.bot.db.execute(stock_sql, ctx.guild.id, ctx.author.id, ticker, amount)

            await message.edit(content=f'Purchased **{amount}** {share} of **{ticker}** for **${humanized_total}**.')

        if not answer:
            await message.edit(content='Cancelled the transaction.')

    @commands.command(help='Sells a stock')
    async def sell(self, ctx, ticker: str = 'MSFT', amount='1'):
        ticker = ticker.upper()

        sql = (
            "SELECT amount FROM stocks WHERE user_id = $1 AND guild_id = $2 AND ticker = $3"
        )
        check = await ctx.bot.db.fetchval(sql, ctx.author.id, ctx.guild.id, ticker)
        if not check:
            return await ctx.send(f'You don\'t have any shares of **{ticker}**')

        try:
            if amount != 'max' and int(amount) > check:
                return await ctx.send(f"You only have {check} {ctx.plural('share(s)', check)} of {ticker}")
        except ValueError:
            return await ctx.send("Invalid amount provided.")

        if amount == 'max':
            amount = check
        amount = int(amount)

        async with self.bot.session.get(f'{FINNHUB_URL}/quote?symbol={ticker}&token={self.finnhub}') as r:
            data: dict = await r.json()

        if data["c"] == 0:
            return await ctx.send('Invalid stock provided.')

        stock: dict = data

        price: int = round(stock["c"])
        total: int = amount * price

        humanized_price: str = humanize.intcomma(price)
        humanized_total: str = humanize.intcomma(total)

        share: str = ctx.plural("share(s)", amount)
        answer, message = await ctx.confirm(
            f'Confirm to sell **{amount}** {share} of **{ticker}** at **${humanized_price}**'
            f' per share for a total of **${humanized_total}**.'
        )

        if answer:
            stock_sql = (
                "UPDATE stocks "
                "SET amount = stocks.amount - $1 "
                "WHERE user_id = $3 AND guild_id = $4 AND ticker = $2 AND amount > 0"
            )
            stock_values = (amount, ticker, ctx.author.id, ctx.guild.id)

            wallet, _ = await get_stats(ctx, ctx.author.id)
            eco_values = (wallet + total, ctx.author.id, ctx.guild.id)

            await self.bot.db.execute("UPDATE economy SET cash = $1 WHERE user_id = $2 AND guild_id = $3", *eco_values)
            await self.bot.db.execute(stock_sql, *stock_values)

            await message.edit(content=f'Sold **{amount}** {share} of **{ticker}** for **${humanized_total}**.')
        else:
            await message.edit(content='Cancelled the transaction.')

    @commands.command(help='Views your stock portfolio')
    async def portfolio(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author

        query = (
            """
            SELECT ticker, amount FROM stocks 
            WHERE user_id = $1 AND guild_id = $2
            """
        )

        stuff = await self.bot.db.fetch(query, user.id, ctx.guild.id)
        if len(stuff) == 0:
            return await ctx.send(f'{user.mention} has no stocks', allowed_mentions=discord.AllowedMentions().none())
        table = tabulate.tabulate((dict(thing) for thing in stuff if thing["amount"] != 0), headers="keys",
                                  tablefmt="github")
        embed = ctx.embed(title=f"{user}\'s stocks:", description=f'```py\n{table}```')
        await ctx.send(embed=embed)

    @commands.command(help='Looks up a stocks price.', aliases=['stock_lookup'])
    async def lookup(self, ctx, ticker: str):
        ticker = ticker.upper()

        async with self.bot.session.get(f'{FINNHUB_URL}/quote?symbol={ticker}&token={self.finnhub}') as r:
            data: dict = await r.json()

        if data["c"] == 0:
            return await ctx.send('Yeah so that\'s not a valid stock lmao')

        stats = f'```yaml\n' \
                f'Current: {data["c"]}\n' \
                f'Daily High: {data["h"]}\n' \
                f'Daily Low: {data["l"]}\n' \
                f'Opening: {data["o"]}\n' \
                f'Previous Close: {data["pc"]}```'

        await ctx.send(stats)

    @commands.command(help='Search to see if a stock ticker exists.')
    async def check(self, ctx, search):
        search = search.upper()
        async with self.bot.session.get(f'{FINNHUB_URL}/search?q={search}&token={self.finnhub}') as r:
            data: dict = await r.json()

        if not data["result"]:
            return await ctx.message.add_reaction("❌")
        if data["result"][0]["symbol"] == search:
            await ctx.message.add_reaction("✅")
            await ctx.invoke(ctx.bot.get_command('lookup'), search)
        else:
            await ctx.message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Stocks(bot))
