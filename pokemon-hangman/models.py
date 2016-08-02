"""models.py - Description here."""

import random
from pokemon import PokemonNames
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
	guessed_letters = ndb.StringProperty(required=True, default="")
	game_over = ndb.BooleanProperty(required=True, default=False)
	penalty = ndb.FloatProperty(required=True, default=0.0)

	@classmethod
	def new_game(cls, user):
		"""Creates and returns a new game"""
		# if number:
		# 	word = POKEMON_LIST.get_name(number)
		# else:
		# 	word = POKEMON_LIST.get_random_name()
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
	# TODO
	# Redefine score as number of _ remaining when word correctly guessed
	# (perhaps as percentage of length of word to normalize length of word)
	user = ndb.KeyProperty(required=True, kind="User")
	date = ndb.DateProperty(required=True)
	won = ndb.BooleanProperty(required=True)
	score = ndb.FloatProperty(required=True)

	def to_form(self):
		return ScoreForm(user_name=self.user.get().name, won=self.won, date=str(self.date), score=self.score)


class UserForm(messages.Message):
	user_name = messages.StringField(1, required=True)
	total_score = messages.FloatField(2, required=True)


class UserForms(messages.Message):
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
	#number = messages.BooleanField(2, required=False)


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


class StringMessage(messages.Message):
	"""Outbound single string message"""
	message = messages.StringField(1, required=True)
