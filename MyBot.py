#!/usr/bin/env python
from ants import *
from random import choice, shuffle

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/MyBot.log',
                    filemode='w')
#console = logging.StreamHandler()
#console.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
#console.setFormatter(formatter)
#logging.getLogger('').addHandler(console)

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
    def __init__(self):
        # define class level variables, will be remembered between turns
        pass
    
    # do_setup is run once at the start of the game
    # after the bot has received the game settings
    # the ants class is created and setup by the Ants.run method
    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        pass
    
    # do turn is run once per turn
    # the ants class has the game state and is updated by the Ants.run method
    # it also has several helper methods to use
    def do_turn(self, ants):
        logging.info("Starting turn...")
        # loop through all my ants and try to give them orders
        # the ant_loc is an ant location tuple in (row, col) form
        
        future_ants = []
        unknown_targets = []
        food_targets = []
        find_closest = True
        for index, ant_loc in enumerate(ants.my_ants()):
            if ants.time_remaining() < 0.3 * ants.turntime:
                logging.info("BREAKING")
                logging.info("TIME REMAINING: " + str(ants.time_remaining()))
                return
                
            if ants.time_remaining() < 0.4 * ants.turntime:
                logging.info("Running low on time!")
                logging.info("TIME REMAINING: " + str(ants.time_remaining()))
                find_closest = False
                
                #break
            directions = ['n', 'e', 's', 'w']
            shuffle(directions)
            
            closest_unknown = None
            if find_closest:
                # Each ant should move to the nearest unknown location to map it that another ant isn't moving to
                closest_unknown = ants.closest_unknown(ant_loc, unknown_targets)
                while closest_unknown and closest_unknown in unknown_targets:
                    closest_unknown = ants.closest_unknown(ant_loc, unknown_targets)
            
            
            # For now the first 25 ants are "explorers", the rest are random fools
            # This is to avoid timeout until we have some type of memory for each ant of what 
            # their order is!
            if closest_unknown:
                ds = ants.a_star_direction(ant_loc, closest_unknown)
                directions = ds + directions
            elif find_closest and ants.time_remaining() < 0.4 * ants.turntime:
                logging.info("No unknowns, finding food instead!")
                closest_food = ants.closest_food(ant_loc, food_targets)
                while closest_food and closest_food in food_targets:
                    closest_food = ants.closest_food(ant_loc, food_targets)
                    
                if closest_food:
                    ds = ants.a_star_direction(ant_loc, closest_food)
                    directions = ds + directions
                else:
                    logging.info("NO FOOD!")

                
            # try all directions in RANDOM order
            order_issued = False
            while directions:
                direction = directions[0]
                del directions[0]
                
                # Try to move the ant in the random direction, but only if it isn't
                # water or one of our own ants.
                new_loc = ants.destination(ant_loc, direction)
                if ants.passable(new_loc) and not new_loc in future_ants:
                    ants.issue_order((ant_loc, direction))
                    # Save the new location in the future_ants so we can avoid collisions
                    future_ants.append(new_loc)  
                    order_issued = True
                    break
                    
                    
            if order_issued:
                pass
                #logging.info("Order given!")
            else:
                logging.info("Ant stuck!")
            # check if we still have time left to calculate more orders
            if ants.time_remaining() < 10:
                break
            
if __name__ == '__main__':
    # psyco will speed up python a little, but is not needed
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        Ants.run(MyBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
