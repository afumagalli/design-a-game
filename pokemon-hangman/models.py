"""models.py - Description here."""

import random
from pokemon import PokemonNames
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

class User(ndb.model):
    """User profile model"""
    name = ndb.StringProprery(required=True)
    email = ndb.StringProprery()

class Game(ndb.Model):
    """Game object"""
    target = ndb.StringProprery(required=True)
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True, default=6)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind="User")

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user,
                    word=pokemonNames().get_random_name())