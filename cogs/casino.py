import asyncio
import random

import discord
import humanize
from discord.ext import commands

from utils.blackjack import Deck, Gamble, Hand
from utils.eco import get_number, get_stats


class Blackjack:
    def __init__(self, ctx, bet: int):
        self.ctx = ctx
        self.playing = True

        self.message = None

        self.deck = Deck()
        self.deck.shuffle()

        self.player = Hand()
        self.player.add_card(self.deck.deal())
        self.player.add_card(self.deck.deal())

        self.dealer = Hand()
        self.dealer.add_card(self.deck.deal())
        self.dealer.add_card(self.deck.deal())

        self.bet = Gamble(bet)

        self.blackjack = False

    @staticmethod
    def list_cards(cards):
        return "\n".join(str(card) for card in cards)

    async def show_some(self, message=None):
        dealer_card = self.dealer.cards[1]

        embed = self.ctx.embed(description=f"Type `hit` to draw another card or `stand` to pass.",
                               color=discord.Color.green())
        embed.set_footer(text=f"Cards remaining: {len(self.deck.deck)}/52")

        embed.add_field(
            name="Your hand:",
            value=self.list_cards(self.player.cards) + f"\n\nValue: **{self.player.value}**"
        )
        embed.add_field(
            name="Dealer's hand:",
            value=f"<hidden>\n"
                  f"{dealer_card}\n\n"
                  f"Value: **{int(dealer_card)}**"
        )

        if message:
            return await message.edit(content=None, embed=embed)

        return await self.ctx.send(embed=embed)

    def determine_outcome(self):
        dealer = self.dealer.value
        player = self.player.value

        bet = humanize.intcomma(self.bet.bet)

        color = None

        if self.blackjack:
            self.bet.win_blackjack()
            description = f"Result: Blackjack! **${humanize.intcomma(self.bet.bet)}**"
            color = discord.Color.green()

        elif dealer > 21:
            self.bet.win_bet()
            description = f"Result: Dealer bust **${bet}**"

        elif player > 21:
            self.bet.lose_bet()
            description = f"Result: Player bust **$-{bet}**"
            color = discord.Color.red()

        elif dealer > player:
            self.bet.lose_bet()
            description = f"Result: Loss **$-{bet}**"
            color = discord.Color.red()

        elif player > dealer:
            self.bet.win_bet()
            description = f"Result: Win **${bet}**"

        else:
            description = f"Result: Push, money back."
            color = discord.Color.gold()

        return description, color

    async def show_all(self):
        desc, c = self.determine_outcome()
        embed = self.ctx.embed(description=desc, color=c or discord.Color.green())
        embed.set_footer(text=f"Cards remaining: {len(self.deck.deck)}/52")
        embed.add_field(
            name="Your hand:",
            value=self.list_cards(self.player.cards) + f"\n\nValue: **{self.player.value}**"
        )
        embed.add_field(
            name="Dealer's hand:",
            value=self.list_cards(self.dealer.cards) + f"\n\nValue: **{self.dealer.value}**"
        )
        await self.message.edit(content=None, embed=embed)

    async def hit(self, hand):
        hand.add_card(self.deck.deal())
        hand.adjust_for_ace()
        if hand != self.dealer:
            if hand.value > 21:
                return True
            await self.show_some(self.message)
            return None

    async def hit_or_stand(self):
        valid_options = ("hit", "stand")
        iteration = 1
        while True:
            message = None
            if iteration == 1 and self.player.value == 21:
                self.blackjack = True
                iteration += 1
                self.playing = False
                break
            try:
                message = await self.ctx.bot.wait_for("message",
                                                      timeout=30,
                                                      check=lambda
                                                          m: m.author == self.ctx.author and m.channel == self.ctx.channel and m.content.lower() in valid_options)
            except asyncio.TimeoutError:
                choice = "stand"
                if self.player.value < 17:
                    choice = "hit"

            if message:
                content = message.content.lower()
                if content in valid_options:
                    choice = content

            if choice == "hit":
                stay = await self.hit(self.player)
                if stay:
                    self.playing = False
                    break
                iteration += 1
                continue

            if choice == "stand":
                self.playing = False

            break

    async def start(self):

        self.message = await self.show_some()

        while self.playing:
            await self.hit_or_stand()

        if self.player.value <= 21 and not self.blackjack:
            while self.dealer.value < 17:
                await self.hit(self.dealer)

        await self.show_all()

        query = (
            """
            UPDATE economy SET cash = cash + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        await self.ctx.bot.db.execute(query, self.bet.total, self.ctx.guild.id, self.ctx.author.id)


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['bj'])
    async def blackjack(self, ctx, bet: str):
        """Play a game of blackjack.
        If you do not respond, the bot will choose hit if your value is under 17, and hit otherwise.

        Arguments:
            `bet`: The bet you want to play. This takes from your wallet."""
        cash, _ = await get_stats(ctx, ctx.author.id)
        amount = get_number(bet, cash)
        query = (
            """
            UPDATE economy SET cash = cash - $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        await self.bot.db.execute(query, amount, ctx.guild.id, ctx.author.id)

        bj = Blackjack(ctx, amount)
        await bj.start()

    @commands.command()
    async def slots(self, ctx, bet: str):
        cash, _ = await get_stats(ctx, ctx.author.id)
        amount = get_number(bet, cash)

        emojis = ("⭐", "🎖️", "🎁")
        e = random.choices(emojis, k=3)

        if e[0] == e[1] == e[2]:
            total = amount
            result = f"🎉 All three match!  **${total}**"
        elif (e[0] == e[1]) or (e[0] == e[2]) or (e[1] == e[2]):
            total = int(amount * 0.5)
            result = f"🎉 Two in a row! **${total}**"
        else:
            total = -amount
            result = f"😥 No match. **${total}**"

        query = (
            """
            UPDATE economy SET cash = cash + $1
            WHERE guild_id = $2 AND user_id = $3
            """
        )
        await self.bot.db.execute(query, total, ctx.guild.id, ctx.author.id)
        await ctx.send(embed=ctx.embed(description=f"{' '.join(e)}\n\n{result}"))


def setup(bot):
    bot.add_cog(Casino(bot))
