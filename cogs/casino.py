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
    def __init__(self, ctx, bet: int=100):
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

    async def player_bust(self):
        self.embed.description = f"You bust! **-${self.bet.bet}**."
        self.bet.lose_bet()
        await self.message.edit(embed=self.embed)

    async def show_some(self, message=None):
        dealer_card = self.dealer.cards[1]
        self.embed = self.ctx.embed(description=f"Type `hit` to hit, `stand` to stand.\n {len(self.deck.deck)} cards left.")
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

    async def hit(self, deck, hand):
        hand.add_card(deck.deal())
        hand.adjust_for_ace()
        await self.show_some(self.message)
        if hand.value > 21:
            await self.player_bust()

    async def hit_or_stand(self):
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
                await self.hit(self.deck, self.player)
                continue

            if choice == "stand":
                self.playing = False

            break



    async def start(self, bet: int = 100):
        self.message = await self.show_some()

        while self.playing:
            await self.hit_or_stand()


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bj(self, ctx):
        bj = Blackjack(ctx)
        await bj.start()


def setup(bot):
    bot.add_cog(Casino(bot))
