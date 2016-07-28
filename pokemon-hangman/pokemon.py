import os
from random import randrange

PATH = os.path.join(os.path.dirname(__file__), "names.txt")

class PokemonNames():
    """Get all Pokemon names and put in a list"""

    def __init__(self, default=True):
        """Initialize the list of Pokemon names"""
        self.namesDict = {}
        self.totalPokemon = 0
        if default:
            self.namesDict = self.get_from_file(PATH)

    def get_from_file(self, filePath):
        """Read the txt file containing all Pokemon names"""
        file = open(filePath, 'r+')
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
