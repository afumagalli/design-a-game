"""utils.py - Contains utility functions for getting a Pokemon name as well as getting a ndb Model from its urlsafe key"""

import endpoints
import os
from random import randrange
from google.appengine.ext import ndb

PATH = os.path.join(os.path.dirname(__file__), "names.txt")

class PokemonNames():
    """Get all Pokemon names and puts them in a list"""

    def __init__(self, default=True):
        """Initialize the list of Pokemon names"""
        self.namesDict = {}
        self.totalPokemon = 0
        if default:
            self.namesDict = self.get_from_file(PATH)

    def get_from_file(self, filePath):
        """Read the txt file containing all Pokemon names"""
        file = open(filePath, 'r')
        lines = file.readlines()
        self.totalCount = len(lines)
        for index, val in enumerate(lines):
            lines[index] = val.split()
        namesDict = {}
        for line in lines:
            namesDict[int(line[0])] = line[1]
        return namesDict

    def get_random_name(self):
        """Return a random name"""
        key = randrange(1, self.totalCount + 1)
        return self.namesDict[key]

    def get_name(self, key):
        """Get a name by a Pokemon's Pokedex number"""
        return self.namesDict.get(key, None)

def get_by_urlsafe(urlsafe, model):
	"""Returns an ndb.Model entity that the urlsafe key points to. Checks
		that the type of entity returned is of the correct kind. Raises an
		error if the key String is malformed or the entity is of the incorrect
		kind
	Args:
		urlsafe: A urlsafe key string
		model: The expected entity kind
	Returns:
		The entity that the urlsafe Key string points to or None if no entity
		exists.
	Raises:
		ValueError:"""
	try:
		key = ndb.Key(urlsafe=urlsafe)
	except TypeError:
		raise endpoints.BadRequestException('Invalid Key')
	except Exception, e:
		if e.__class__.__name__ == 'ProtocolBufferDecodeError':
			raise endpoints.BadRequestException('Invalid Key')
		else:
			raise

	entity = key.get()
	if not entity:
		return None
	if not isinstance(entity, model):
		raise endpoints.BadRequestException('Incorrect Kind')
	return entity
