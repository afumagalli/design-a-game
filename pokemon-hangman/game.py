"""game.py - Description here."""

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import NewGameForm, GuessLetterForm, String Message


NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1),)
GUESS_LETTER_REQUEST = endpoints.ResourceContainer(GuessLetterForm, urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1), email=messages.StringField(2))
MEMCACHE_GUESSES_REMAINING = "GUESSES_REMAINING"


@endpoints.api(name="pokemon_hangman", version="v1")
class PokemonHangmanAPI(remote.Service):
    """Game API"""
    @endpoints.emthod(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path="user",
                      name="create_user",
                      http_method="POST")
    def create_user(self, request):
        """Create a User. Username must be unique"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException("A User with that name already exists!")
        if User.query(User.email == request.email).get():
            raise endpoints.ConflictException("A User with that email already exists!")
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message="User {} created!".format(request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=NewGameForm,
                      path="game",
                      name="new_game",
                      http_method="POST")
    def new_game(self, request):
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException("A user with that name does not exist!")
        try:
            game = Game.new_game(user.key, request.)


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
