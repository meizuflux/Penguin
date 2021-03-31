from discord.ext import commands
from utils.blackjack import Hand, Deck, Gamble
from utils.eco import get_stats
import asyncio
import random

class Blackjack:
    def __init__(self, ctx, bet: int = 100):
        self.ctx = ctx
        self.playing = True

        self.message = None
        self.embed = None

        self.deck = Deck()
        self.deck.shuffle()

        self.player = Hand()
        self.player.add_card(self.deck.deal())
        self.player.add_card(self.deck.deal())

        self.dealer = Hand()
        self.dealer.add_card(self.deck.deal())
        self.dealer.add_card(self.deck.deal())

        self.bet = Gamble(bet)

    @staticmethod
    def list_cards(cards):
        return "\n".join(str(card) for card in cards)

    async def show_some(self, message=None):
        dealer_card = self.dealer.cards[1]
        self.embed = self.ctx.embed(
            description=f"Type `hit` to hit, `stand` to stand.\n {len(self.deck.deck)} cards left.")
        if self.player.value > 21:
            self.bet.lose_bet()
            self.embed.description = f"Result: Bust **-${self.bet.bet}**"
        self.embed.add_field(
            name="Your hand:",
            value=self.list_cards(self.player.cards) + f"\n\nValue: **{self.player.value}**"
        )
        self.embed.add_field(
            name="Dealer's hand:",
            value=f"<hidden>\n"
                  f"{dealer_card}\n\n"
                  f"Value: **{int(dealer_card)}**"
        )
        if message:
            return await message.edit(content=None, embed=self.embed)
        return await self.ctx.send(embed=self.embed)

    def determine_outcome(self):
        dealer = self.dealer.value
        player = self.player.value

        if dealer > 21:
            self.bet.win_bet()
            self.embed.description = f"Result: Dealer bust **${self.bet.bet}**"

        elif dealer > player:
            self.bet.lose_bet()
            self.embed.description = f"Result: Loss **-${self.bet.bet}**"

        elif player > dealer:
            self.bet.win_bet()
            self.embed.description = f"Result: Win **${self.bet.bet}**"

        else:
            self.embed.description = f"Result: Push, money back."

    async def show_all(self):
        self.embed = self.ctx.embed(description=f"{len(self.deck.deck)} cards left.")
        self.embed.add_field(
            name="Your hand:",
            value=self.list_cards(self.player.cards) + f"\n\nValue: **{self.player.value}**"
        )
        self.embed.add_field(
            name="Dealer's hand:",
            value=self.list_cards(self.dealer.cards) + f"\n\nValue: **{self.dealer.value}**"
        )
        self.determine_outcome()
        print(self.bet.total)
        await self.message.edit(content=None, embed=self.embed)

    async def hit(self, hand):
        hand.add_card(self.deck.deal())
        hand.adjust_for_ace()
        if hand != self.dealer:
            await self.show_some(self.message)

    async def hit_or_stand(self):
        valid_options = ("hit", "stand")
        while True:
            try:
                message = await self.ctx.bot.wait_for("message",
                                                      timeout=30,
                                                      check=lambda
                                                          m: m.author == self.ctx.author and m.channel == self.ctx.channel and m.content.lower() in valid_options)
            except asyncio.TimeoutError:
                choice = random.choice(valid_options)

            content = message.content.lower()
            if content in valid_options:
                choice = content

            if choice == "hit":
                await self.hit(self.player)
                continue

            if choice == "stand":
                self.playing = False

            break

    async def start(self):
        cash, _ = await get_stats(self.ctx, self.ctx.author.id)
        self.message = await self.show_some()

        while self.playing:
            await self.hit_or_stand()

        if self.player.value <= 21:
            while self.dealer.value < 17:
                await self.hit(self.dealer)

            await self.show_all()


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def blackjack(self, ctx):
        """Play a game of blackjack."""
        bj = Blackjack(ctx)
        await bj.start()


def setup(bot):
    bot.add_cog(Casino(bot))