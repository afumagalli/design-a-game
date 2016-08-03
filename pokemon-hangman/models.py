"""models.py - Contains all Datastore models and ProtoRPC messages for the game"""

import random
from utils import PokemonNames
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

POKEMON_LIST = PokemonNames()

class User(ndb.Model):
	"""User profile object"""
	name = ndb.StringProperty(required=True)
	email = ndb.StringProperty()

	def to_form(self, total_score):
		form = UserForm()
		form.user_name = self.name
		form.total_score = total_score
		return form


class Game(ndb.Model):
	"""Game object"""
	user = ndb.KeyProperty(required=True, kind="User")
	word = ndb.StringProperty(required=True)
	word_so_far = ndb.StringProperty(required=True)
	attempts_remaining = ndb.IntegerProperty(required=True, default=6)
	past_guesses = ndb.StringProperty(repeated=True)
	game_over = ndb.BooleanProperty(required=True, default=False)
	penalty = ndb.FloatProperty(required=True, default=0.0)

	@classmethod
	def new_game(cls, user):
		"""Creates and returns a new game"""
		word = POKEMON_LIST.get_random_name()
		word_so_far = "_" * len(word)
		game = Game(parent=user,
					user=user,
					word=word,
					word_so_far=word_so_far,
					attempts_remaining=6,
					game_over=False)
		game.put()
		return game

	def save_history(self, guess, message, order):
		"""Saves the last made move to history"""
		move = History(parent=self.key,
					   guess=guess,
					   message=message,
					   order=order)
		move.put()
		return move

	def to_form(self, message):
		"""Returns a GameForm representation of the Game"""
		form = GameForm()
		form.urlsafe_key = self.key.urlsafe()
		form.user_name = self.user.get().name
		form.attempts_remaining = self.attempts_remaining
		form.game_over = self.game_over
		form.message = message
		form.word_so_far = self.word_so_far
		return form

	def end_game(self, won=False, score=0):
		self.game_over = True
		self.put()
		score = Score(parent=self.user, user=self.user, date=date.today(), won=won, score=score)
		score.put()


class Score(ndb.Model):
	"""Score object"""
	user = ndb.KeyProperty(required=True, kind="User")
	date = ndb.DateProperty(required=True)
	won = ndb.BooleanProperty(required=True)
	score = ndb.FloatProperty(required=True)

	def to_form(self):
		form = ScoreForm()
		form.user_name = self.user.get().name
		form.won = self.won
		form.date = str(self.date)
		form.score = self.score
		return form


class History(ndb.Model):
	"""Object representing a past guess and result"""
	guess = ndb.StringProperty(required=True)
	message = ndb.StringProperty(required=True)
	order = ndb.IntegerProperty(required=True)

	def to_form(self):
		form = HistoryForm()
		form.guess = self.guess
		form.message = self.message
		return form


class UserForm(messages.Message):
	"""UserForm for outbound user information"""
	user_name = messages.StringField(1, required=True)
	total_score = messages.FloatField(2, required=True)


class UserForms(messages.Message):
	"""Returns multiple UserForms"""
	items = messages.MessageField(UserForm, 1, repeated=True)


class GameForm(messages.Message):
	"""GameForm for outbound game state information"""
	urlsafe_key = messages.StringField(1, required=True)
	attempts_remaining = messages.IntegerField(2, required=True)
	game_over = messages.BooleanField(3, required=True)
	message = messages.StringField(4, required=True)
	user_name = messages.StringField(5, required=True)
	word_so_far = messages.StringField(6, required=True)

class GameForms(messages.Message):
	"""Return multiple GameForms"""
	items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
	"""Form for creting a new game"""
	user_name = messages.StringField(1, required=True)


class GuessForm(messages.Message):
	"""Form to guess a letter in the word"""
	guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
	"""ScoreForm for outbound Score information"""
	user_name = messages.StringField(1, required=True)
	date = messages.StringField(2, required=True)
	won = messages.BooleanField(3, required=True)
	score = messages.FloatField(4, required=True)


class ScoreForms(messages.Message):
	"""Return multiple ScoreForms"""
	items = messages.MessageField(ScoreForm, 1, repeated=True)


class HistoryForm(messages.Message):
	"""Form for outbound History information"""
	guess = messages.StringField(1, required=True)
	message = messages.StringField(2, required=True)


class HistoryForms(messages.Message):
	"""Returns multiple HistoryForms"""
	items = messages.MessageField(HistoryForm, 1, repeated=True)


class StringMessage(messages.Message):
	"""Outbound single string message"""
	message = messages.StringField(1, required=True)
