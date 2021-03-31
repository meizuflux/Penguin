import random

from discord.ext import commands

suits = ('Hearts', 'Diamonds', 'Spades', 'Clubs')
ranks = ('2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A')
values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10,
          'Q': 10, 'K': 10, 'A': 11}

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
            for rank in ranks:
                self.deck.append(Card(suit, rank))

    def shuffle(self):
        random.shuffle(self.deck)

    def deal(self):
        single_card = self.deck.pop()
        return single_card


class Hand:
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0

    def add_card(self, card):
        self.cards.append(card)
        self.value += values[card.rank]
        if card.rank == 'A':
            self.aces += 1

    def adjust_for_ace(self):
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1


class Gamble:
    def __init__(self, bet):
        self.total = 100
        self.bet = bet

    def win_bet(self):
        self.total += self.bet

    def lose_bet(self):
        self.total -= self.bet

    def win_blackjack(self):
        self.total += (self.bet + (self.bet / 2))


class Casino(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def setup(self, bet: int = 100):
        deck = Deck()
        deck.shuffle()

        player_hand = Hand()
        player_hand.add_card(deck.deal())
        player_hand.add_card(deck.deal())

        dealer_hand = Hand()
        dealer_hand.add_card(deck.deal())
        dealer_hand.add_card(deck.deal())

        player_bet = bet

        return deck, player_hand, dealer_hand, player_bet

    @staticmethod
    def list_cards(cards):
        return "\n".join(str(card) for card in cards)

    async def show_some(self, ctx, player, dealer, total_cards, message=None):
        dealer_card = dealer.cards[1]
        embed = ctx.embed(description=f"Type `hit` to hit, `stand` to stand.\n {total_cards} cards left.")
        embed.add_field(
            name="Your hand:",
            value=self.list_cards(player.cards) + f"\nValue: {player.value}"
        )
        embed.add_field(
            name="Dealer's hand:",
            value=f"<hidden>\n"
                  f"{dealer_card}\n"
                  f"Value: {int(dealer_card)}"
        )
        if message:
            return await message.edit(content=None, embed=embed)
        return await ctx.send(embed=embed)

    @commands.command()
    async def bj(self, ctx):
        bet = 100

        deck, player_hand, dealer_hand, player_bet = self.setup(bet)

        message = await self.show_some(ctx, player_hand, dealer_hand, len(deck.deck))


def setup(bot):
    bot.add_cog(Casino(bot))
