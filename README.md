AI Challenge Bot Code Repository
================================

This is the repository for my bot code for the Google AI Challenge. See the competition website at http://aichallenge.org/ for more information.

This bot is based off the concept of collaborative diffusion described in the paper ["Collaborative Diffusion: Programming Antiobjects"](http://www.cs.colorado.edu/~ralex/papers/PDF/OOPSLA06antiobjects.pdf) by Alexander Repenning.

The general concept is that every object in the world is given a weight which is then diffused across the map every turn and each ant simply moves in the direction of highest weight surround it's current position. In the case of this bot several maps are diffused each turn including a food, exploration, and combat maps.

The bot itself does an "ok" job against other bots, but needs a lot more work to be actually competitive. Most of logic is place, but all of the weights need fine tuning which takes time (or a genetic algorithm!).

Feel free to take this code and do whatever with it, everything is here for good clean fun! 