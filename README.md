# blossom
Bocce Log Of Scores, Statistics, and Other Metrics

An extension of the ALISS tool (see repository 'aliss') that aggregates
Drone-Assisted Seated Chair Bocce statistics over time and across matches.
BLOSSOM currently logs the number of rounds per game, points per side, each
side's average distance from the jack, and the match winner. It can read out
career-long stats from the log, such as total rounds played, points scored,
overall average distance, and number of wins. This package comes with ALISS
already built-in and integrated, so all you need to do is fire up the drone,
find a comfy chair, and launch the jack!

TECHNICAL STUFF AND HOW TO USE:

Written in Python 3.8

See repository 'aliss' for details on how to optimize that system for your
individual setup.

Run BLOSSOM from the command line with 'python3 blossom.py' plus optional
arguments in the following order:
- the function to execute: 'r' to read from the log (default), 'w' to
  write new game data to the log (see info on game-specific arguments
  below), or 'wr' to write new data and read the updated log
- the log file to use: this defaults to 'log.csv', but you can specify
  other filenames to keep multiple logs (for example if you wanted to keep
  logs for multiple matchups with different teams/players
- game-specific arguments: see info in the 'aliss' repo for details

NOTE: The 'input' folder included here contains example images, but you should
replace these with your own images to track your play.
