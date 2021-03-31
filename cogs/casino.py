import asyncio
import random

from discord.ext import commands

suits = ('Hearts', 'Diamonds', 'Spades', 'Clubs')
# ranks = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace')
values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'Jack': 10,
          'Queen': 10, 'King': 10, 'Ace': 11}

playing = True


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        return self.rank + " of " + self.suit

    def __int__(self):
        return values[self.rank]


class Deck:
    def __init__(self):
        self.deck = []
        for suit in suits:
            for rank in values:
                self.deck.append(Card(suit, rank))

    def shuffle(self):
        random.shuffle(self.deck)

    def deal(self):
        return self.deck.pop()


class Hand:
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def add_card(self, card):
        self.cards.append(card)
        self.value += values[card.rank]
        if card.rank == 'Ace':
            self.aces += 1

    def adjust_for_ace(self):
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1


class Gamble:
    def __init__(self, bet):
        self.total = bet
        self.bet = bet

    def win_bet(self):
        self.total += self.bet

    def lose_bet(self):
        self.total -= self.bet

    def win_blackjack(self):
        self.total += (self.bet + (self.bet / 2))


class Blackjack:
    def __init__(self, ctx):
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


    @staticmethod
    def list_cards(cards):
        return "\n".join(str(card) for card in cards)

    async def show_some(self, message=None):
        dealer_card = self.dealer.cards[1]
        embed = self.ctx.embed(description=f"Type `hit` to hit, `stand` to stand.\n {len(self.deck.deck)} cards left.")
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

    async def hit(self, deck, hand):
        hand.add_card(deck.deal())
        hand.adjust_for_ace()
        await self.show_some(self.message)

    async def hit_or_stand(self, deck, hand, message):
        valid_options = ("hit", "stand")
        while True:
            try:
                message = await self.ctx.bot.wait_for("message",
                                                      timeout=30,
                                                      check=lambda m: m.author == self.ctx.author and m.channel == self.ctx.channel and m.content.lower() in valid_options)
            except asyncio.TimeoutError:
                choice = random.choice(valid_options)

            content = message.content.lower()
            if content in valid_options:
                choice = content

            if choice == "hit":
                await self.hit(deck, hand)
                continue

            if choice == "stand":
                self.playing = False

            break



    async def start(self, bet: int = 100):
        player_bet = Gamble(bet)

        self.message = await self.show_some()


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bj(self, ctx):
        bj = Blackjack(ctx)
        await bj.start()


def setup(bot):
    bot.add_cog(Casino(bot))
