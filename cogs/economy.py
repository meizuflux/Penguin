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
import math
import typing
import asyncio

import discord
import humanize
from discord.ext import commands

from utils.default import qembed
from utils.argparse import Arguments


async def get_stats(ctx, user_id: int):
    await ctx.bot.db.execute("INSERT INTO economy VALUES ($1, $2) ON CONFLICT DO NOTHING", ctx.guild.id, user_id)
    data = await ctx.bot.db.fetchrow("SELECT cash, bank FROM economy WHERE guild_id = $1 AND user_id = $2",
                                     ctx.guild.id, user_id)

    return data["cash"], data["bank"]


class Economy(commands.Cog, command_attrs=dict(hidden=False)):
    """
    A unique Economy system. This is per-server specific, so your money will not carry over from server to server.
    Kicking the bot will reset the leaderboard, and all data will be lost.
    
    For all the commands that ask you to provide an amount, there are some different ways you can use it. 
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

    def get_number(self, number: str, total: int):
        number = number.replace(",", "")
        if number.endswith("%"):
            number = number.strip("%")
            if not number.isdigit():
                raise commands.BadArgument("That's... not a valid percentage.")
            number = round(float(number))
            if number > 100:
                raise commands.BadArgument("You can't do more than 100%.")
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

        if amount > total:
            raise commands.BadArgument("That's more money than you have...")

        if amount > 100000000000:
            raise commands.BadArgument("Transfers of money over one hundred billion are prohibited.")

        return amount

    @commands.command(help='Registers you into the database')
    async def register(self, ctx):
        await get_stats(ctx, ctx.author.id)
        await ctx.send("k its done")

    @commands.command(help='View yours or someone else\'s balance', aliases=['bal'])
    async def balance(self, ctx, user: discord.Member = None):
        cash, bank = await get_stats(ctx, user.id if user else ctx.author.id)
        green_arrow = "<:green_arrow:811052039416447027>"
        e = discord.Embed(title=f'{user.name if user else ctx.author.name}\'s balance',
                          description=
                          f"{green_arrow} **Cash:** ${humanize.intcomma(cash)}\n"
                          f"{green_arrow} **Bank:** ${humanize.intcomma(bank)}\n"
                          f"{green_arrow} **Total:** ${humanize.intcomma(cash + bank)}",
                          color=self.bot.embed_color, timestamp=ctx.message.created_at)

        e.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        e.set_thumbnail(url=user.avatar_url if user else ctx.author.avatar_url)
        await ctx.send(embed=e)

    @commands.command(aliases=("lb", "top", "server-leaderboard", "server-lb"), usage="[page=1] [--cash | --bank]")
    async def leaderboard(self, ctx, page: typing.Optional[int] = 1, item: str = None):
        """
        Sends the economy leaderboard.
        Server specific.
        If the page you provide is higher than the total amount of pages, it defaults to the last page.
        
        Optional Flags:
            `--cash`: Orders by users with the most cash.
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
                
            
        count = await self.bot.db.fetchval(count_query, ctx.guild.id)
        max_pages = math.ceil(count / 10)
        # need to check if the page is more than the amount allowed
        page = min(page, max_pages)



        data = await self.bot.db.fetch(lb_query, ctx.guild.id, (page * 10) - 10)

        lb = []
        for user in data:
            # Need to escape markdown
            name = discord.utils.escape_markdown(str(await self.bot.try_user(user['user_id'])))
            # Add a rickroll cause I'm lazy
            item = f"**{user['number']}.** [{name}](https://www.youtube.com/watch?v=dQw4w9WgXcQ, 'seriously, don\'t click.') » **${humanize.intcomma(user['total'])}**"
            lb.append(item)
        lb.append(f"\nPage {page}/{max_pages}")

        embed = ctx.embed(title=f"{ctx.guild.name} Leaderboard", description="\n".join(lb))
        await ctx.send(embed=embed)

    @commands.command(help='Deposits a set amount into your bank', aliases=['dep'])
    async def deposit(self, ctx, amount: str):
        cash, bank = await get_stats(ctx, ctx.author.id)

        amount = self.get_number(amount, cash)
        
        if amount == 0:
            return await ctx.send(embed=ctx.embed(description="You have no cash."))

        updated_cash = cash - amount
        bank += amount

        query = (
            """
            UPDATE economy SET cash = $1, bank = $2
            WHERE guild_id = $3 AND user_id = $4
            """
        )

        await self.bot.db.execute(query, updated_cash, bank, ctx.guild.id, ctx.author.id)

        await qembed(ctx, f'You deposited **${humanize.intcomma(amount)}** into your bank.')

    @commands.command(help='Withdraws a set amount from your bank', aliases=['wd', 'with'])
    async def withdraw(self, ctx, amount: str):
        cash, bank = await get_stats(ctx, ctx.author.id)

        amount = self.get_number(amount, bank)
        if amount == 0:
            return await ctx.send(embed=ctx.embed(description="You have no cash."))

        cash += amount
        updated_bank = bank - amount

        query = (
            """
            UPDATE economy SET cash = $1, bank = $2
            WHERE guild_id = $3 AND user_id = $4
            """
        )

        await self.bot.db.execute(query, cash, updated_bank, ctx.guild.id, ctx.author.id)
        await qembed(ctx, f'You withdrew **${humanize.intcomma(amount)}** from your bank.')

    @commands.command(help='Lets you send money over to another user', alises=['send', 'pay'])
    async def transfer(self, ctx, user: discord.Member, amount: str):
        author_cash, _ = await get_stats(ctx, ctx.author.id)
        target_cash, _ = await get_stats(ctx, user.id)

        amount = self.get_number(amount, author_cash)

        author_cash -= amount
        target_cash += amount

        await self.bot.db.execute("UPDATE economy SET cash = $1 WHERE guild_id = $2 AND user_id = $3", author_cash,
                                  ctx.guild.id, ctx.author.id)
        await self.bot.db.execute("UPDATE economy SET cash = $1 WHERE guild_id = $2 AND user_id = $3", target_cash,
                                  ctx.guild.id, user.id)

        await qembed(ctx, f'You gave {user.mention} **${humanize.intcomma(amount)}**')

    @commands.command(help='Takes a random amount of $ from someone', alises=['mug', 'steal'])
    async def rob(self, ctx, user: discord.Member):

        if random.randint(1, 2) == 2:
            desc = f"You try to rob {user.mention}, but the police see you and let you go with a warning."
            return await ctx.send(embed=ctx.embed(description=desc))

        author_cash, author_bank = await get_stats(ctx, ctx.author.id)
        target_cash, target_bank = await get_stats(ctx, user.id)

        if target_cash == 0:
            return await qembed(ctx, 'That user has no cash. Shame on you for trying to rob them.')

        amount = random.randint(1, target_cash)

        author_cash += amount
        target_cash -= amount

        author_query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        target_query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(author_query, author_cash, ctx.guild.id, ctx.author.id)
        await self.bot.db.execute(target_query, target_cash, ctx.guild.id, user.id)

        await qembed(ctx, f'You stole **${humanize.intcomma(amount)}** from {user.mention}!')

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
            user_msg = await self.bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
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
        
        
        author_cash, author_bank = await get_stats(ctx, ctx.author.id)

        cash = random.randint(100, 500)

        query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, author_cash + cash, ctx.guild.id, ctx.author.id)
        
        embed.description = f"I transfered **${cash}** to you."
        await m.edit(embed=embed)

    @commands.command(help='Daily reward')
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.user)
    async def daily(self, ctx):
        cash, _ = await get_stats(ctx, ctx.author.id)

        cash = random.randint(500, 1000)

        query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, cash + cash, ctx.guild.id, ctx.author.id)

        await qembed(ctx, f'You\'ve collected **${cash}** from the daily gift!')

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
        
        
        
        user_cash, _ = await get_stats(ctx, ctx.author.id)

        price = random.randint(20, 35)
        fish = random.randint(5, 20)
        cash = price * fish

        query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, user_cash + cash, ctx.guild.id, ctx.author.id)
        
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
        author_cash, _ = await get_stats(ctx, ctx.author.id)

        cash = random.randint(0, 500)

        query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        await self.bot.db.execute(query, author_cash + cash, ctx.guild.id, ctx.author.id)
        city = cities["person"]["personal"]["city"]
        msg = f'You sit on the streets of {city} and a nice {random.choice(["man", "woman"])} hands you ${cash}.'
        await ctx.send(embed=ctx.embed(description=msg))

    @commands.command(help='Resets a cooldown on one command', aliases=['reset', 'cooldownreset'])
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def resetcooldown(self, ctx, command):
        eco = self.bot.get_cog("Economy")
        cash, _ = await get_stats(ctx, ctx.author.id)
        if self.bot.get_command(command) not in eco.walk_commands():
            return await qembed(ctx,
                                f'You can only reset the cooldown for commands in this category. You can do `{ctx.clean_prefix}help Economy` to see all the commands.')

        if command == 'daily':
            return await qembed(ctx,
                                'You can\'t reset the daily command, sorry. '
                                'The whole point is that, well, it\'s meant to be once a day.')

        if cash < 400:
            return await qembed(ctx, 'You need at least 400 dollars.')

        query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )

        self.bot.get_command(command).reset_cooldown(ctx)
        await self.bot.db.execute(query, cash - 400, ctx.guild.id, ctx.author.id)
        await qembed(ctx,
                     f'Reset the command cooldown for the command `{command}` and subtracted **$400** from your account.')
        
    @commands.command(aliases=("bankrob", "bank-rob"))
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)
    async def bank_rob(self, ctx):
        """
        Starts an interactive bank robbing session.
        
        This command takes no arguments.
        """
        numbers = ["<:better1:826124826493190175>", "<:better2:826124826456227870>", "<:better3:826124826401177640>", "<:better4:826124826228817950>"]

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
            amount = random.randint(200, 656)
            await final.edit(content=f"✅ The key matches! You enter the vault.\n💰 You gather **${amount}**")
            
        if var != result:
            return await final.edit(content="❌ The patterns do not match and the vault door stays shut.")
        
        valid_options = ("leave", "stay")
        choice = None
        
        
        while True:
            message = await ctx.send(f"Would you like to stay in the vault and collect more money or would you like to leave? (`stay`/`leave`)\nYou currently have **${amount}** in your moneybag.", delete_after=15)
            
            try:
                msg = await self.bot.wait_for("message", timeout=15, check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
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
                    return await message.edit(content="You push your luck too far and the cops catch you, leaving you with nothing!")
                
                grabbed_amount = amount = random.randint(400, 1200)
                amount += grabbed_amount
                await ctx.send(f"You grab another **${grabbed_amount}** to add to your moneybag.", delete_after=15)
                
            if choice == "leave":
                break
                
        cash, _ = await get_stats(ctx, ctx.author.id)
        
        query = (
            """
            UPDATE economy SET cash = $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        await self.bot.db.execute(query, cash + amount, ctx.guild.id, ctx.author.id)
                
        await ctx.send(f"You make off with a total of **${amount}** in your bag.")
                
    @commands.is_owner()
    @commands.group(name='set', hidden=True)
    async def _set(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @_set.command()
    async def cash(self, ctx, user: discord.User, amount: str):
        amount = amount.replace(",", "")
        if not amount.isdigit():
            raise commands.BadArgument("Amount must be a number.")
        amount = int(amount)
        await get_stats(ctx, user.id)
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
        await get_stats(ctx, user.id)
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
