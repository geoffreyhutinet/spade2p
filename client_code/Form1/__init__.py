from ._anvil_designer import Form1Template
from anvil import *
import anvil.server
from .. import Spade2p as s2p


class Form1(Form1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.player1 = s2p.Person("Random Player 1")
    self.player2 = s2p.Person("Random Player 2")
    self.play_area = None

    # Any code you write here will run before the form opens.

  def play_click(self, **event_args):
    # Set up Player 1
    if self.type_player1 == "Human":
      self.player1 = s2p.Human(self.player1_name)
    elif self.player1_type == "Premade":
      self.player1 = s2p.Person(self.player1_name)
      self.player1.change_card_strategy('_'.join(self.player1_card_strategy.split(' ')))
      self.player1.change_bid_strategy('_'.join(self.player1_bid_strategy.split(' ')))
      self.player1.change_play_strategy('_'.join(self.player1_play_strategy_strategy.split(' ')))
    
    # Set up Player 1
    if self.type_player2 == "Human":
      self.player2 = s2p.Human(self.player2_name)
    elif self.player2_type == "Premade":
      self.player2 = s2p.Person(self.player2_name)
      self.player2.change_card_strategy('_'.join(self.player2_card_strategy.split(' ')))
      self.player2.change_bid_strategy('_'.join(self.player2_bid_strategy.split(' ')))
      self.player2.change_play_strategy('_'.join(self.player2_play_strategy_strategy.split(' ')))

    #Set up the game
    self.play_area = s2p.Play_Area(
      dealer = self.player1,
      first_bidder = self.player2
    )

    #Start
    winner = self.play_area.play()
    alert(f"the winner is {winner}")
    
    
