import anvil.server
import pydealer
import random
import copy
import neat
import os
import pickle
import warnings
import matplotlib.pyplot as plt
import numpy as np
from google.colab import files

##General variable
ranks = {
    "values": {
        "Ace": 13,
        "King": 12,
        "Queen": 11,
        "Jack": 10,
        "10": 9,
        "9": 8,
        "8": 7,
        "7": 6,
        "6": 5,
        "5": 4,
        "4": 3,
        "3": 2,
        "2": 1
    },
    "suits": {
        "Spades": 4,
        "Hearts": 3,
        "Clubs": 2,
        "Diamonds": 1
    }
}
deck = pydealer.Deck(ranks = ranks)
card_position = {
    f'{card.value} of {card.suit}' : 0 for card in deck
}
'''
card poistion keys:
  0   in deck or unknown
  1   drawn
  2   in discard
  3   in hand
  4   in play
  5   in oponent victory stack
  6   in personal victory stack
'''

##Classes
class Person:
    def __init__(self, name):
        self.name = name
        self.hand = pydealer.Stack()
        self.card_position = copy.deepcopy(card_position)
        self.possible_cards = pydealer.Stack()
        self.air_stack = pydealer.Stack()
        self.card_per_suit = {
            'Spades' : pydealer.Stack(),
            'Hearts' : pydealer.Stack(),
            'Diamonds' : pydealer.Stack(),
            'Clubs' : pydealer.Stack()
        }
        self.card_played = None
        self.bid = 0
        self.tricks = 0
        self.bags = 0
        self.score = 0
        self.print = False

    ## Functions to replace behaviors card choosing
    def change_card_strategy(self, card_strategy):
        if card_strategy != "random":
            if card_strategy == "take_all_black":
                self.draw_decision = self.take_all_black
            elif card_strategy == "take_spades_hearts":
                self.draw_decision = self.take_spades_hearts
            elif card_strategy == "take_spades_diamonds":
                self.draw_decision = self.take_spades_diamonds

    def draw_decision(self, card_drawn, other_player):
        #create decision bot
        draw_choice = random.choice([True, False])
        if self.print:
            print(f"{self.name} drew the {'first card' if draw_choice else 'second card'}")
        return draw_choice, other_player

    def take_all_black(self, card_drawn, other_player):
        if card_drawn.suit in ['Clubs', 'Spades']:
            return True, other_player
        else:
            return False, other_player

    def take_spades_hearts(self, card_drawn, other_player):
        if card_drawn.suit in ['Hearts', 'Spades']:
            return True, other_player
        else:
            return False, other_player

    def take_spades_diamonds(self, card_drawn, other_player):
        if card_drawn.suit in ['Diamonds', 'Spades']:
            return True, other_player
        else:
            return False, other_player

    ## Functions to replace behaviors bidding
    def change_bid_strategy(self, bid_strategy):
        if bid_strategy != "random":
            if bid_strategy == "high_card":
                self.bid_decision = self.high_card

    def bid_decision(self, num_list, bid_turn, other_player):
        #create decision bot
        bid_choice = random.choice(num_list)
        if self.print:
            print(f"{self.name} bid {bid_choice}")
        return bid_choice, other_player

    def high_card(self, num_list, bid_turn, other_player):
        self.air_stack = copy.deepcopy(self.hand)
        bid_choice = len(self.air_stack.get_list(['Ace', 'King', 'Queen']))
        self.air_stack.empty()
        if self.print:
            print(f"{self.name} bid {bid_choice}")
        return bid_choice, other_player

    ## Functions to replace behaviors playing
    def change_play_strategy(self, play_strategy):
        if play_strategy != "random":
            if play_strategy == "longest_suit":
                self.play_card = self.longest_suit

    def play_card(self, other_player, play_turn):
        #create decision bot
        self.card_played = self.possible_cards.random_card()
        self.hand.get(pydealer.card.card_name(value=self.card_played.value, suit=self.card_played.suit))
        if self.print:
            print(f"{self.name} played the {self.card_played}")
        return other_player

    def longest_suit(self, other_player, play_turn):
        self.air_stack = copy.deepcopy(self.possible_cards)
        for suit, stack in self.card_per_suit.items():
            stack.insert_list(self.air_stack.get_list([suit]))
        size_per_suit = { suit : stack.size for suit, stack in self.card_per_suit.items()}
        self.possible_cards = self.card_per_suit[max(size_per_suit, key=size_per_suit.get)]
        self.possible_cards.shuffle()
        self.card_played = self.possible_cards.random_card()
        self.hand.get(pydealer.card.card_name(value=self.card_played.value, suit=self.card_played.suit))
        self.air_stack.empty()
        for stack in self.card_per_suit.values():
            stack.empty()
        if self.print:
            print(f"{self.name} played the {self.card_played}")
        return other_player

    ## Other functions
    def draw_and_decide(self, deck, other_player):
        card_drawn = deck.deal()
        next_card = deck.deal()
        take_the_card, other_player = self.draw_decision(card_drawn[0], other_player)
        if take_the_card:
            self.hand.add(card_drawn)
            self.card_position[f'{card_drawn[0].value} of {card_drawn[0].suit}'] = 3
            self.card_position[f'{next_card[0].value} of {next_card[0].suit}'] = 2
            if self.print:
                print(f"{self.name} drew the {card_drawn[0].value} of {card_drawn[0].suit}, and discarded the {next_card[0]. value} of {next_card[0].suit}")
        else:
            self.hand.add(next_card)
            self.card_position[f'{card_drawn[0].value} of {card_drawn[0].suit}'] = 2
            self.card_position[f'{next_card[0].value} of {next_card[0].suit}'] = 3
            if self.print:
                print(f"{self.name} discarded the {card_drawn[0].value} of {card_drawn[0].suit}, and drew the {next_card[0]. value} of {next_card[0].suit}")

        return deck

    def bagging_over(self, other_player):
        temp_bags = copy.deepcopy(self.bags)
        self.bags = self.bags % 10
        temp_bags -= self.bags
        other_player.score += 10 * temp_bags
        if self.print:
            print(f'{self.name} bagged over, {10 * temp_bags} points to {other_player.name}')
        return other_player


class Play_Area:
    def __init__(self, dealer, first_bidder):
        self.deck = pydealer.Deck(ranks = ranks)
        self.deck.shuffle()
        self.dealer = dealer
        self.first_bidder = first_bidder
        self.current_bidder = first_bidder
        self.wait_for_bid = dealer
        self.opener = first_bidder
        self.follower = dealer
        self.play_turn = 0
        self.bid_turn = 0
        self.passed = False
        self.spade_broke = False
        self.print = False

    def swap_dealer(self):
        self. dealer, self.first_bidder = self.first_bidder, self.dealer
        self.current_bidder = self.first_bidder
        self.wait_for_bid = self.dealer
        self.opener = self.first_bidder
        self.follower = self.dealer
        self.deck = pydealer.Deck(ranks = ranks)
        self.deck.shuffle()
        self.dealer.card_position = copy.deepcopy(card_position)
        self.first_bidder.card_position = copy.deepcopy(card_position)
        self.dealer.bid = 0
        self.first_bidder.bid = 0
        self.dealer.tricks = 0
        self.first_bidder.tricks = 0
        if self.print:
            print(f"New Dealer: {self.dealer.name}")

    def swap_player(self):
        self.opener, self.follower = self.follower, self.opener

    def next_bidder(self):
        self.current_bidder, self.wait_for_bid = self.wait_for_bid, self.current_bidder

    def make_hand(self):
        while self.deck.size >= 2:
            self.deck = self.first_bidder.draw_and_decide(self.deck, self.dealer)
            self.deck = self.dealer.draw_and_decide(self.deck, self.first_bidder)

    def bid(self):
        while not self.passed:
            possible_bids = range(0,13,1)
            bid_attempt, self.wait_for_bid = self.current_bidder.bid_decision(possible_bids[self.current_bidder.bid:], self.bid_turn, self.wait_for_bid)
            #print(f'{self.current_bidder.name} has bid')
            if self.current_bidder.bid == bid_attempt:
                self.passed = True
            else:
                self.current_bidder.bid = bid_attempt
                self.next_bidder()

            self.bid_turn += 1

        self.passed = False
        self.bid_turn = 0

    def play_cards(self):
        #print(f"{self.opener.name}'s hand: {self.opener.hand}")
        #print(f"{self.follower.name}'s hand: {self.follower.hand}")
        # Openner plays a card
        if not self.spade_broke:
            self.opener.air_stack = copy.deepcopy(self.opener.hand)
            self.opener.possible_cards.insert_list(self.opener.air_stack.get_list(['Hearts', 'Diamonds', 'Clubs']))
            if self.opener.possible_cards.size == 0:
                self.opener.possible_cards = copy.deepcopy(self.opener.hand)
        else:
            self.opener.possible_cards = copy.deepcopy(self.opener.hand)

        self.follower = self.opener.play_card(self.follower, self.play_turn)
        self.opener.possible_cards.empty()
        self.opener.card_position[f'{self.opener.card_played.value} of {self.opener.card_played.suit}'] = 4
        self.follower.card_position[f'{self.opener.card_played.value} of {self.opener.card_played.suit}'] = 4

        # Follower plays a card
        self.follower.air_stack = copy.deepcopy(self.follower.hand)
        self.follower.possible_cards.insert_list(self.follower.air_stack.get_list([self.opener.card_played.suit]))
        if self.follower.possible_cards.size == 0:
            self.follower.possible_cards = copy.deepcopy(self.follower.hand)

        self.opener = self.follower.play_card(self.opener, self.play_turn)
        self.follower.possible_cards.empty()
        self.follower.card_position[f'{self.follower.card_played.value} of {self.follower.card_played.suit}'] = 4
        self.opener.card_position[f'{self.follower.card_played.value} of {self.follower.card_played.suit}'] = 4

    def register_cards(self, winner, looser):
        winner.card_position[f'{winner.card_played.value} of {winner.card_played.suit}'] = 6
        winner.card_position[f'{looser.card_played.value} of {looser.card_played.suit}'] = 6
        looser.card_position[f'{winner.card_played.value} of {winner.card_played.suit}'] = 5
        looser.card_position[f'{looser.card_played.value} of {looser.card_played.suit}'] = 5
        return winner, looser

    def who_get_the_trick(self):
        if self.opener.card_played.suit == self.follower.card_played.suit:
            if ranks["values"][self.opener.card_played.value] > ranks["values"][self.follower.card_played.value]:
              self.opener.tricks += 1
              self.opener, self.follower = self.register_cards(self.opener, self.follower)
              if self.print:
                print(f"{self.opener.name} takes the trick")
            else:
              self.follower.tricks += 1
              self.follower, self.opener = self.register_cards(self.follower, self.opener)
              if self.print:
                print(f"{self.follower.name} takes the trick")
              self.swap_player()

        elif self.follower.card_played.suit == 'Spades':
            self.follower.tricks += 1
            self.follower, self.opener = self.register_cards(self.follower, self.opener)
            if self.print:
              print(f"{self.follower.name} takes the trick")
            self.swap_player()

        else:
            self.opener.tricks += 1
            self.opener, self.follower = self.register_cards(self.opener, self.follower)
            if self.print:
              print(f"{self.opener.name} takes the trick")

    def score(self):
        total_bid = self.dealer.bid + self.first_bidder.bid
        bag_price = 13 - total_bid

        for player, other_player in [(self.dealer, self.first_bidder), (self.first_bidder, self.dealer)]:
            if player.tricks >= player.bid:
                if player.bid == 10:
                    player.score += 200
                else:
                    player.score += 10 * player.bid
            else:
                if player.bid == 10:
                    other_player.score += 200
                else:
                    other_player.score += 10 * player.bid

            if player.bid == 10 and player.tricks > player.bid:
                pass
            elif player.tricks > player.bid:
                bags = bag_price * (player.tricks - player.bid)
                if bags > 0:
                    player.bags += bags
                    player.score += bags

                else:
                    other_player.bags -= bags
                    other_player.score -= bags


        if self.dealer.bags >= 10:
              self.first_bidder = self.dealer.bagging_over(self.first_bidder)

        if self.first_bidder.bags >= 10:
              self.dealer = self.first_bidder.bagging_over(self.dealer)

    def play(self):
        if self.print:
          self.dealer.print = True
          self.first_bidder.print = True

        self.dealer.score = 0
        self.first_bidder.score = 0

        while self.dealer.score < 1000 and self.first_bidder.score < 1000:
          self.make_hand()
          if self.print:
              print(f"{self.dealer.name} hand:")
              print(self.dealer.hand)
              print(f"{self.first_bidder.name} hand:")
              print(self.first_bidder.hand)

          self.bid()

          if self.first_bidder.bid == 0:
              self.dealer.score += 100
          elif self.dealer.bid == 0:
              self.first_bidder.score += 10 * self.first_bidder.bid
          else:
            while self.play_turn < 13:
                self.play_cards()

                # Check if Spades broke
                if self.opener.card_played.suit == 'Spades' or self.follower.card_played.suit == 'Spades':
                    self.spade_broke = True

                self.who_get_the_trick()
                self.play_turn += 1

            self.spade_broke = False
            self.score()
            self.play_turn = 0

          self.dealer.card_played = None
          self.first_bidder.card_played = None

          if self.print:
            print(f"{self.dealer.name} tricks: {self.dealer.tricks}, bid: {self.dealer.bid}, score: {self.dealer.score}")
            print(f"{self.first_bidder.name} tricks: {self.first_bidder.tricks}, bid: {self.first_bidder.bid}, score: {self.first_bidder.score}")

          self.swap_dealer()

        if self.dealer.score > self.first_bidder.score:
          winner = self.dealer.name
        elif self.dealer.score == self.first_bidder.score:
          winner = "Draw"
        else:
          winner = self.first_bidder.name

        if self.print:
          print(f"Game over, WINNER: {winner}")
        self.dealer.score = 0
        self.first_bidder.score = 0

        return winner


class SpadesAI(Person):
    def __init__(self, name, network):
        super().__init__(name)  # Call Person's __init__
        self.net = network

    def draw_decision(self, card_drawn, other_player):
        text_card = f'{card_drawn.value} of {card_drawn.suit}'
        self.card_position[text_card] = 1
        inputs = [value for value in self.card_position.values()] + [other_player.score, self.score, self.bid,
                                                                     other_player.bid]
        outputs = {
            card: round(output) for card, output in zip(self.card_position, self.net.activate(inputs)[:52])
        }
        if outputs[text_card] == 3:
            if self.print:
              print(f"{self.name} drew the first card")
            return True, other_player
        elif outputs[text_card] == 2:
            if self.print:
              print(f"{self.name} drew the second card")
            return False, other_player
        else:
            other_player.score += 0
            draw_choice = random.choice([True, False])
            if self.print:
              print(f"{self.name} drew the {'first card' if draw_choice else 'second card'}")
            return draw_choice, other_player

    def bid_decision(self, num_list, bid_turn, other_player):
        inputs = [value for value in self.card_position.values()] + [other_player.score, self.score, self.bid,
                                                                     other_player.bid]
        output = round(self.net.activate(inputs)[-1])
        if output in num_list:
            if self.print:
              print(f"{self.name} bid {output}")
            return output, other_player
        else:
            other_player.score += 0
            bid_choice = random.choice(num_list)
            if self.print:
              print(f"{self.name} bid {bid_choice}")
            return bid_choice, other_player

    def play_card(self, other_player, play_turn):
        inputs = [value for value in self.card_position.values()] + [other_player.score, self.score, self.bid,
                                                                     other_player.bid]
        outputs = {
            card: round(output) for card, output in zip(self.card_position, self.net.activate(inputs)[:52])
        }
        card_to_play = [
            card for card, output in outputs.items() if output == 4
        ]

        if len(card_to_play) == 0:
            other_player.score += 0
            self.card_played = self.possible_cards.random_card()
            self.hand.get(pydealer.card.card_name(value=self.card_played.value, suit=self.card_played.suit))
        else:
            possible_card_to_play = []
            for card in card_to_play:
                if card in self.possible_cards:
                    possible_card_to_play.append(card)
            if len(possible_card_to_play) != 1:
                other_player.score += 0
                self.card_played = self.possible_cards.random_card()
                self.hand.get(pydealer.card.card_name(value=self.card_played.value, suit=self.card_played.suit))
            else:
                self.card_played = pydealer.Card(value=possible_card_to_play[0].value,
                                                 suit=possible_card_to_play[0].suit)
                self.hand.get(pydealer.card.card_name(value=self.card_played.value, suit=self.card_played.suit))

        if self.print:
            print(f"{self.name} played the {self.card_played}")

        return other_player

def eval_genomes(genomes, config):
    # Step 1, make sure that it wins against random 9/10 time
    random_person = Person('Random')
    fit_ai = []
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        ai_person = SpadesAI('AI', net)
        for _ in range(5):
            play_area1 = Play_Area(
                dealer=ai_person,
                first_bidder=random_person
            )
            play_area2 = Play_Area(
                dealer=random_person,
                first_bidder=ai_person
            )

            winner1 = play_area1.play()
            if winner1 == ai_person.name:
                genome.fitness += 1

            winner2 = play_area2.play()
            if winner2 == ai_person.name:
                genome.fitness += 1

        if genome.fitness >= 8:
            fit_ai.append((genome_id, genome, net))

    # Step 2 test AI against each other
    for genome_id1, genome1, net1 in fit_ai:
        for genome_id2, genome2, net2 in fit_ai:
            if genome_id1 != genome_id2:
                ai_person1 = SpadesAI('AI1', net1)
                ai_person2 = SpadesAI('AI2', net2)
                play_area = Play_Area(
                    dealer=ai_person1,
                    first_bidder=ai_person2
                )
                winner = play_area.play()
                if winner == ai_person1.name:
                    genome1.fitness += 1
                elif winner == ai_person2.name:
                    genome2.fitness += 1

def plot_stats(statistics, ylog=False, view=False, filename='avg_fitness.svg'):
    """ Plots the population's average and best fitness. """
    if plt is None:
        warnings.warn("This display is not available due to a missing optional dependency (matplotlib)")
        return

    generation = range(len(statistics.most_fit_genomes))
    best_fitness = [c.fitness for c in statistics.most_fit_genomes]
    avg_fitness = np.array(statistics.get_fitness_mean())
    stdev_fitness = np.array(statistics.get_fitness_stdev())

    plt.plot(generation, avg_fitness, 'b-', label="average")
    plt.plot(generation, avg_fitness - stdev_fitness, 'g-.', label="-1 sd")
    plt.plot(generation, avg_fitness + stdev_fitness, 'g-.', label="+1 sd")
    plt.plot(generation, best_fitness, 'r-', label="best")

    plt.title("Population's average and best fitness")
    plt.xlabel("Generations")
    plt.ylabel("Fitness")
    plt.grid()
    plt.legend(loc="best")
    if ylog:
        plt.gca().set_yscale('symlog')

    plt.savefig(filename)
    if view:
        plt.show()

    plt.close()

def test_debug():
  play_area = Play_Area(
      dealer = Person('Player 1'),
      first_bidder = Person('Player 2')
      )
  play_area.print = print
  play_area.play()

if __name__ == "__main__":
  test_debug()
