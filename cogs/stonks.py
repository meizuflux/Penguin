from discord.ext import commands
import discord
import humanize
import math
from asyncpg import CheckViolationError
from utils.default import plural
import re
from prettytable import PrettyTable

FINNHUB_URL = "https://finnhub.io/api/v1/"


class Stocks(commands.Cog, command_attrs=dict(hidden=False)):
    def __init__(self, bot):
        self.bot = bot
        self.finnhub = self.bot.config.finnhub

    @staticmethod
    async def get_stats(self, user_id: int):
        try:
            data = dict(await self.bot.db.fetchrow('SELECT wallet, bank FROM economy WHERE userid = $1', user_id))
            wallet = data["wallet"]
            bank = data["bank"]

        except TypeError:
            await self.bot.db.execute("INSERT INTO public.economy(userid, wallet, bank) VALUES($1, 100, 100)", user_id)
            data = dict(await self.bot.db.fetchrow('SELECT wallet, bank FROM economy WHERE userid = $1', user_id))
            wallet = data["wallet"]
            bank = data["bank"]

        return wallet, bank

    @commands.command(help='Buys a stock. BETA')
    async def buy(self, ctx, ticker: str = 'MSFT', amount='1'):

        wallet, bank = await self.get_stats(self, ctx.author.id)
        ticker = ticker.upper()
        async with self.bot.session.get(f'{FINNHUB_URL}/quote?symbol={ticker}&token={self.finnhub}') as r:
            data: dict = await r.json()
        if data["c"] == 0:
            return await ctx.send('Yeah so thats not a valid stock lmao')

        stock: dict = data
        price: int = round(stock["c"])
        humanized_price: str = humanize.intcomma(price)

        match = re.search(r'^[0-9]*$', str(amount))
        if match:
            amount = int(match[0])
        else:
            match = re.search(r'^[a-zA-Z]*$', amount)
            if match and match[0] == 'max':
                amount = math.floor(wallet / price)
                if amount == 0:
                    return await ctx.send('You don\'t have enough money to buy a share.')
            else:
                amount = 1

        total: int = amount * price
        humanized_total: str = humanize.intcomma(total)

        share: str = plural("share(s)", amount)
        answer, message = await ctx.confirm(
            f'Confirm to buy **{amount}** {share} of **{ticker}** at **${humanized_price}**'
            f' per share for a total of **${humanized_total}**.')

        if answer:
            if total > wallet:
                return await message.edit(
                    content=f'You need **${total - wallet}** more in order to purchase this stock.')
            sql = (
                "INSERT INTO stocks(user_id, ticker, amount) VALUES($1, $2, $3) "
                "ON CONFLICT (user_id, ticker) "
                "DO UPDATE SET amount = stocks.amount + $3"
            )
            values = (ctx.author.id, ticker, amount)
            await ctx.bot.db.execute(sql, *values)
            await self.bot.db.execute("UPDATE economy SET wallet = $1 WHERE userid = $2", wallet - total,
                                      ctx.author.id)
            await message.edit(
                content=f'Purchased **{amount}** {share} of **{ticker}** for **${humanized_total}**.')

        if not answer:
            await message.edit(content='Cancelled the transaction.')

    @commands.command(help='Sells a stock. BETA')
    async def sell(self, ctx, ticker: str = 'MSFT', amount='1'):
        wallet, bank = await self.get_stats(self, ctx.author.id)
        ticker = ticker.upper()

        async with self.bot.session.get(f'{FINNHUB_URL}/quote?symbol={ticker}&token={self.finnhub}') as r:
            data: dict = await r.json()

        if data["c"] == 0:
            return await ctx.send('Yeah so thats not a valid stock lmao')

        stock: dict = data
        price: int = round(stock["c"])
        humanized_price: str = humanize.intcomma(price)

        match = re.search(r'^[0-9]*$', str(amount))
        if match:
            amount = int(match[0])
        else:
            match = re.search(r'^[a-zA-Z]*$', amount)
            if match and match[0] == 'max':
                sql = (
                    "SELECT amount FROM stocks WHERE user_id = $1 AND ticker = $2"
                )
                amount = await ctx.bot.db.fetchval(sql, ctx.author.id, ticker)
            else:
                amount = 1

        total: int = amount * price
        humanized_total: str = humanize.intcomma(total)

        share: str = plural("share(s)", amount)
        answer, message = await ctx.confirm(
            f'Confirm to sell **{amount}** {share} of **{ticker}** at **${humanized_price}**'
            f' per share for a total of **${humanized_total}**.')

        if answer:
            try:
                query = await ctx.bot.db.execute(
                    "UPDATE stocks SET amount = stocks.amount - $3 WHERE user_id = $1 AND ticker = $2",
                    ctx.author.id, ticker, amount)
                if query == 'UPDATE 0':
                    return await message.edit(content="You don't any stock.")
                await ctx.bot.db.execute('DELETE FROM stocks WHERE amount = 0')
                await self.bot.db.execute("UPDATE economy SET wallet = $1 WHERE userid = $2", wallet + total,
                                          ctx.author.id)
                return await message.edit(
                    content=f'Sold **{amount}** {share} of **{ticker}** for **${humanized_total}**.')
            except CheckViolationError:
                return await message.edit("You don't have that much stock")
        else:
            await message.edit(content='Cancelled the transaction.')

    @commands.command(help='Views your stock portfolio')
    async def portfolio(self, ctx, user: discord.Member = None):
        if not user:
            user = ctx.author

        res = await self.bot.db.fetch("SELECT ticker, amount FROM stocks WHERE user_id = $1", user.id)
        if len(res) == 0:
            return await ctx.send(f'{user} has no stocks', allowed_mentions=discord.AllowedMentions().none())

        table = PrettyTable()
        table.field_names = list(res[0].keys())

        for record in res:
            lst = list(record)
            table.add_row(lst)

        msg = table.get_string()
        await ctx.send(f"{user.mention}\'s stocks:```\n{msg}\n```", allowed_mentions=discord.AllowedMentions().none())

    @commands.command(help='Looks up a stocks price.', aliases=['stock_lookup'])
    async def lookup(self, ctx, ticker: str):
        ticker = ticker.upper()

        async with self.bot.session.get(f'{FINNHUB_URL}/quote?symbol={ticker}&token={self.finnhub}') as r:
            data: dict = await r.json()

        if data["c"] == 0:
            return await ctx.send('Yeah so thats not a valid stock lmao')

        stats = f'```yaml\n'\
                f'Current: {data["c"]}\n'\
                f'Daily High: {data["h"]}\n'\
                f'Daily Low: {data["l"]}\n'\
                f'Opening: {data["o"]}\n'\
                f'Previous Close: {data["pc"]}```'

        await ctx.send(stats)


    @commands.command(help='Search to see if a stock ticker exists.')
    async def check(self, ctx, search):
        search = search.upper()
        async with self.bot.session.get(f'{FINNHUB_URL}/search?q={search}&token={self.finnhub}') as r:
            data: dict = await r.json()

        if not data["result"]:
            await ctx.message.add_reaction("❌")
        if data["result"][0]["symbol"] == search:
            await ctx.message.add_reaction("✅")
            await ctx.invoke(ctx.bot.get_command('lookup'), search)
        else:
            await ctx.message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Stocks(bot))
