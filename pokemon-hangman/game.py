"""game.py - Description here."""

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

@endpoints.api(name="pokemon_hangman", version="v1")
class PokemonHangmanAPI(remote.Service):
    """Game API"""
    def create_user(self, request):
        pass
    def new_game(self, request):
        pass
    def get_game(self, request):
        pass
    def guess_letter(self, request):
        pass
    def word_so_far(self, request):
        pass
    def all_words_so_far(self, request):
        pass
    def all_user_words_so_far(self, request):
        pass
