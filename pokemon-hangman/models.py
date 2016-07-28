"""models.py - Description here."""

import random
from pokemon import PokemonNames
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

POKEMON_LIST = PokemonNames()

class User(ndb.model):
	"""User profile model"""
	name = ndb.StringProprery(required=True)
	email = ndb.StringProprery()

class Game(ndb.Model):
	"""Game object"""
	target = ndb.StringProprery(required=True)
	attempts_remaining = ndb.IntegerProperty(required=True, default=6)
	game_over = ndb.BooleanProperty(required=True, default=False)
	user = ndb.KeyProperty(required=True, kind="User")

	@classmethod
	def new_game(cls, user, number):
		"""Creates and returns a new game"""
		if number:
			word = POKEMON_LIST.get_name(number)
		else:
			word = POKEMON_LIST.get_random_name()
		game = Game(target=word,
					attempts_remaining=6,
					game_over=False
					user=user)
		game.put()
		return game

	def to_form(self, message):
		"""Returns a GameForm representation of the Game"""
		form = GameForm()

	def end_game(self, won=False):
		self.game_over = True
		self.put()

