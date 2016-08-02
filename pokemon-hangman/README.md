# Pokémon Hangman Endpoints API

This project provides an endpoints API for a Pokémon Hangman game, though in theory this project could be easily adapted to work on any set of words. The project contains the following files:

`main.py`: Contains handlers that are called by taskqueue and
cronjobs
`game.py`: Contains all of the APIs and game logic
`models.py`: Contains all Datastore models and ProtoRPC messages for the game
`pokemon.py`: Contains code for generating a list of Pokemon names and selecting one at random or by number
`utils.py`: Contains a function for getting an entity from its urlsafe key

# Game Rules

Once a user has created a game, their word will be assigned - they will know how many letters are in the Pokemon's name but nothing more. At any point, the user can choose to guess a single letter in the name or the entire name at once. The user gets 6 "attempts" or "strikes" throughout the game. Incorrect guesses decrease the "attempts" counter - correct guesses do not. An incorrect name guess also increases the "penalty" (see Score Keeping below). If the counter hits 0, the game is over and the user gets a score of 0.0. Alternatively, if the user correctly guesses the name or final letter(s) then the game is over their score is calculated according to the algorithm in the following section.

# Score Keeping

To maximize score it is always advisable to guess the entire name once it is known. A score is defined to be a single decimal floating point number calculated based on the number of blanks remaining when the user guessed the name, relative to the length of the name, minus any penalties. In short, we take (((blanks remaining / length of word) * 10) - penalty) rounded to one decimal place where penalty is the number of inccorect name guesses.

The maximum score is 10.0 and the minimum score is 1.0. If the calculation gives a score less than 1.0, it is ignored and the score is assessed to be 1.0.

# API Documentation

The API contains the following endpoints:

`create_user`: Creates a user from a given username and email (optional) - only one account allowed per email, no duplicate usernames
`new_game`: Creates a new game for the user with the supplied username
`get_game`: Returns a game form message for the game with the supplied urlsafe key
`guess_letter`: Allows the user to guess a letter in the game with the suppled urlsafe key - only one letter may be guessed at a time from this endpoint
`guess_word`: Allows the user to guess the entire name in the game with the supplied urlsafe key - a penalty is assessed for incorrect guesses
`get_scores`: Returns all scores for all completed games
`get_user_scores`: Returns all scores for all of the user's completed games
`get_average_attempts`: Returns the average number of attempts remaining
`get_user_games`: Returns a series of game form messages for all games tied to the given username
`cancel_game`: Cancels and deletes a game from the Datastore
`get_high_scores`: Returns the n highest score where n is given as `number_of_results` - if `number_of_results` is not given, it's default is 5
`get_user_rankings`: Returns all of the registered users ranked by their total completed game score
`get_game_history`: Returns a history of all the moves made in a game along with their results

Also contained in this project is a cron job to send an hourly email to all users with an unfinished game in the Datastore.

You can interact with this API online at: pokemon-hangman.appspot.com/_ah/api/explorer
