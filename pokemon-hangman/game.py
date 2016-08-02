"""game.py - Description here."""

from __future__ import division
import math
import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score, History
from models import UserForm, UserForms, GameForm, GameForms, NewGameForm, GuessForm, ScoreForm, ScoreForms, HistoryForm, HistoryForms, StringMessage

from utils import get_by_urlsafe


USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1), email=messages.StringField(2))
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GAME_REQUEST = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1))
GUESS_REQUEST = endpoints.ResourceContainer(GuessForm, urlsafe_game_key=messages.StringField(1))
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(urlsafe_game_key=messages.StringField(1))
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(number_of_results=messages.IntegerField(1))
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
		# Task queue updates average attempts remaining.
		taskqueue.add(url="/tasks/cache_average_attempts")
		return game.to_form("Good luck playing Pokemon Hangman!")


	@endpoints.method(request_message=GAME_REQUEST,
					  response_message=GameForm,
					  path="game/{urlsafe_game_key}",
					  name="get_game",
					  http_method="GET")
	def get_game(self, request):
		"""Return the current game state."""
		game = get_by_urlsafe(request.urlsafe_game_key, Game)
		if game:
			return game.to_form("Guess a letter!")
		else:
			raise endpoints.NotFoundException("Game not found!")


	@endpoints.method(request_message=GUESS_REQUEST,
					  response_message=GameForm,
					  path="game/{urlsafe_game_key}/letter",
					  name="guess_letter",
					  http_method="PUT")
	def guess_letter(self, request):
		"""Guesses a letter. Returns game state with message."""
		game = get_by_urlsafe(request.urlsafe_game_key, Game)
		if game.game_over:
			return game.to_form("Game is already over!")
		if not request.guess:
			return game.to_form("Please guess a letter.")
		if request.guess.lower() in game.past_guesses:
			return game.to_form("You already guessed that letter!")
		if len(request.guess) != 1:
			return game.to_form("You can only guess a single letter.")

		game.past_guesses.append(request.guess.lower())
		move_number = len(game.past_guesses)
		if request.guess.lower() in game.word.lower():
			guess_instances = [i for i, ltr in enumerate(game.word.lower()) if ltr == request.guess.lower()]
			for i in guess_instances:
				game.word_so_far = game.word_so_far[:i] + game.word[i] + game.word_so_far[i+1:]
			if game.word_so_far == game.word:
				# 1 point for guessing final letter
				message = "You won! Score is 1."
				game.save_history(request.guess, message, move_number)
				game.end_game(True, 1.0)
				return game.to_form(message)
			else:
				message = "Correct guess! Word so far: " + game.word_so_far
				game.save_history(request.guess, message, move_number)
				game.put()
				return game.to_form(message)
		else:
			game.attempts_remaining -= 1
			if game.attempts_remaining < 1:
				# 0 points for loss
				message = "Game over! Score is 0."
				game.save_history(request.guess, message, move_number)
				game.end_game(False, 0.0)
				return game.to_form(message)
			else:
				message = "Incorrect guess! Word so far: " + game.word_so_far
				game.save_history(request.guess, message, move_number)
				game.put()
				return game.to_form(message)


	@endpoints.method(request_message=GUESS_REQUEST,
					  response_message=GameForm,
					  path="game/{urlsafe_game_key}/word",
					  name="guess_word",
					  http_method="PUT")
	def guess_word(self, request):
		"""Guesses the entire word. Returns game state with message."""
		game = get_by_urlsafe(request.urlsafe_game_key, Game)
		if game.game_over:
			return game.to_form("Game is already over!")
		if request.guess.lower() in game.past_guesses:
			return game.to_form("You already guessed that word!")
		game.past_guesses.append(request.guess.lower())
		move_number = len(game.past_guesses)
		if request.guess.lower() == game.word.lower():
			# Algorithm for calculating score:
			# Ceiling (blanks remaining / length of word * 10) - penalty
			# --> Correct guess up front = 10 pts
			# --> Correct guess w/ one letter left ~= 1 pt
			# penalty == incorrect word (not letter) guesses
			score = round((game.word_so_far.count('_') / len(game.word)) * 10 - game.penalty, 1)
			if score < 1.0:
				score = 1.0
			game.word_so_far = game.word
			message = "You won! Score is " + str(score) + "."
			game.save_history(request.guess, message, move_number)
			game.end_game(True, score)
			return game.to_form(message)
		game.attempts_remaining -= 1
		if game.attempts_remaining < 1:
			message = "Game over! Score is 0."
			game.save_history(request.guess, message, move_number)
			game.end_game(False, 0.0)
			return game.to_form(message)
		else:
			# Assess a penalty for incorrect guess (subtracted from total score)
			game.penalty += 1.0
			message = "Incorrect guess! Penalty is " + str(game.penalty) + "."
			game.save_history(request.guess, message, move_number)
			game.put()
			return game.to_form(message)


	@endpoints.method(response_message=ScoreForms,
					  path='scores',
					  name='get_scores',
					  http_method='GET')
	def get_scores(self, request):
		"""Return all scores"""
		return ScoreForms(items=[score.to_form() for score in Score.query()])


	@endpoints.method(request_message=USER_REQUEST,
					  response_message=ScoreForms,
					  path='scores/user/{user_name}',
					  name='get_user_scores',
					  http_method='GET')
	def get_user_scores(self, request):
		"""Returns all of an individual User's scores"""
		user = User.query(User.name == request.user_name).get()
		if not user:
			raise endpoints.NotFoundException('A User with that name does not exist!')
		scores = Score.query(Score.user == user.key)
		return ScoreForms(items=[score.to_form() for score in scores])


	@endpoints.method(response_message=StringMessage,
					  path='games/average_attempts',
					  name='get_average_attempts_remaining',
					  http_method='GET')
	def get_average_attempts(self, request):
		"""Get the cached average moves remaining"""
		return StringMessage(message=memcache.get(MEMCACHE_GUESSES_REMAINING) or '')


	@endpoints.method(request_message=USER_REQUEST,
					  response_message=GameForms,
					  path="games/user/{user_name}",
					  name="get_user_games",
					  http_method="GET")
	def get_user_games(self, request):
		"""Get all games created by user."""
		user = User.query(User.name == request.user_name).get()
		if not user:
			raise endpoints.NotFoundException('A User with that name does not exist!')
		query = Game.query(ancestor=user.key)
		return GameForms(items=[game.to_form("") for game in query])


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


	@endpoints.method(request_message=HIGH_SCORES_REQUEST,
					  response_message=ScoreForms,
					  path="high_scores",
					  name="get_high_scores",
					  http_method="GET")
	def get_high_scores(self, request):
		"""Returns the n highest scores"""
		number_of_results = 5 # default
		if request.number_of_results:
			number_of_results = request.number_of_results
		query = Score.query().order(-Score.score)
		results = query.fetch(limit=number_of_results)
		return ScoreForms(items=[result.to_form() for result in results])


	@endpoints.method(response_message=UserForms,
					  path="user_rankings",
					  name="get_user_rankings",
					  http_method="GET")
	def get_user_rankings(self, request):
		"""Ranks users by their total score."""
		results = []
		users = User.query()
		for user in users:
			query = Score.query(ancestor=user.key)
			total_score = sum([score.score for score in query])
			results.append((user, total_score))
		results.sort(key=lambda tup: tup[1], reverse=True)
		return UserForms(items=[result[0].to_form(result[1]) for result in results])


	@endpoints.method(request_message=GAME_REQUEST,
					  response_message=HistoryForms,
					  path="game/{urlsafe_game_key}/history",
					  name="get_game_history",
					  http_method="GET")
	def get_game_history(self, request):
		"""Returns a history of all moves made in game."""
		game = get_by_urlsafe(request.urlsafe_game_key, Game)
		history = History.query(ancestor=game.key).order(History.order)
		return HistoryForms(items=[move.to_form() for move in history])


	@staticmethod
	def _cache_average_attempts():
		"""Populates memcache with the average moves remaining of Games"""
		games = Game.query(Game.game_over == False).fetch()
		if games:
			count = len(games)
			total_attempts_remaining = sum([game.attempts_remaining
										for game in games])
			average = float(total_attempts_remaining)/count
			memcache.set(MEMCACHE_GUESSES_REMAINING,
						 'The average moves remaining is {:.2f}'.format(average))

api = endpoints.api_server([PokemonHangmanAPI])
