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
            game = Game.new_game(user.key)
        # Task queue updates average score.
        taskqueue.add(url="/tasks/cache_average_attempts")
        return game.to_form("Good luck playing Pokemon Hangman!")

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path="game/{urlsafe_game_key}",
                      name="get_game",
                      http_method="GET")
    def get_game(self, request):
        """Return the current game state"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form("Guess a letter!")
        else:
            raise endpoints.NotFoundException("Game not found!")

    @endpoints.method(request_message=GUESS_LETTER_REQUEST,
                      response_message=GameForm,
                      path="game/{urlsafe_game_key}",
                      name="guess_letter",
                      http_method="PUT")
    def guess_letter(self, request):
        """Guesses a letter. Returns game state with message."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form("Game is already over!")
        if request.guess in game.guessed_letters:
            return game.to_form("You already guessed that letter!")
        game.attempts_remaining -= 1
        game.guessed_letters += request.guess
        if request.guess in game.word:
            guess_instances = [i for i, ltr in enumerate(game.word.lower()) if ltr == request.guess]
            for i in guess_instances:
                game.word_so_far = game.word_so_far.replace(game.word_so_far[i], request.guess)
            if game.word_so_far = game.word:
                game.end_game(True)
                return game.to_form("You won!")
            else:
                game.put()
                game.to_form("Correct guess!")
        elif game.attempts_remaining < 1:
            game.end_game(False)
            return game.to_form("Game over!")
        else:
            game.put()
            game.to_form("Incorrect guess!")
