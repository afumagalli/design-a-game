"""game.py - Description here."""

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import GameForm, GameForms, NewGameForm, GuessLetterForm, StringMessage

from utils import get_by_urlsafe


USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1), email=messages.StringField(2))
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1),)
GUESS_LETTER_REQUEST = endpoints.ResourceContainer(GuessLetterForm, urlsafe_game_key=messages.StringField(1),)
GET_USER_GAMES_REQUEST = endpoints.ResourceContainer(urlsafe_user_key=messages.StringField(1),)
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1),)
MEMCACHE_GUESSES_REMAINING = "GUESSES_REMAINING"


@endpoints.api(name="pokemon_hangman", version="v1")
class PokemonHangmanAPI(remote.Service):
	"""Game API"""
	@endpoints.method(request_message=USER_REQUEST,
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
					  response_message=GameForm,
					  path="game",
					  name="new_game",
					  http_method="POST")
	def new_game(self, request):
		"""Create a new game."""
		user = User.query(User.name == request.user_name).get()
		if not user:
			raise endpoints.NotFoundException("A user with that name does not exist!")
		game = Game.new_game(user.key)
		# Task queue updates average score.
		# taskqueue.add(url="/tasks/cache_average_attempts")
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
		game.guessed_letters += request.guess
		if request.guess.lower() in game.word.lower():
			guess_instances = [i for i, ltr in enumerate(game.word.lower()) if ltr == request.guess.lower()]
			for i in guess_instances:
				game.word_so_far = game.word_so_far[:i] + game.word[i] + game.word_so_far[i+1:]
			if game.word_so_far == game.word:
				game.end_game(True)
				return game.to_form("You won!")
			else:
				game.put()
				return game.to_form("Correct guess!")
		else:
			game.attempts_remaining -= 1
			if game.attempts_remaining < 1:
				game.end_game(False)
				return game.to_form("Game over!")
			else:
				game.put()
				return game.to_form("Incorrect guess!")

	@endpoints.method(request_message=GET_USER_GAMES_REQUEST,
					  response_message=GameForms,
					  path="user-games/{urlsafe_user_key}",
					  name="get_user_games",
					  http_method="GET")
	def get_user_games(self, request):
		"""Get all games created by user."""
		user = get_by_urlsafe(request.urlsafe_user_key, User)
		if user:
			query = Game.query(ancestor=user.key)
			return GameForms(items=[game.to_form("") for game in query])
		else:
			raise endpoints.NotFoundException("User not found!")

	@endpoints.method(request_message=CANCEL_GAME_REQUEST,
					  response_message=GameForm,
					  path="game/{urlsafe_game_key}/cancel",
					  name="cancel_game",
					  http_method="PUT")
	def cancel_game(self, request):
		"""Cancels a game by deleting it from the Datastore"""
		game = get_by_urlsafe(request.urlsafe_game_key, Game)
		if game.game_over:
			return game.to_form("Game is already over!")
		form = game.to_form("Game cancelled")
		game.key.delete()
		return form

	def get_high_scores(self, request):
		pass

	def get_user_rankings(self, request):
		pass

	def get_game_history(self, request):
		pass

api = endpoints.api_server([PokemonHangmanAPI])
