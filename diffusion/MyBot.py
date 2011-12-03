#!/usr/bin/env python
from ants import *

import logging
import random

turn_number = 0

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/MyBot.log',
                    filemode='w')

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
        global turn_number
        turn_number = turn_number + 1
        logging.info("Starting turn " + str(turn_number))
        
        
        ants.diffuse()
        
        orders = {
            'food': 0,
            'explore': 0,
            'random': 0,
            'combat': 0,
        }
        
        for ant_loc in ants.my_ants():
            row, col = ant_loc

            # Get the surrounding squares
            surrounding = ants.surrounding_squares(ant_loc)
            
            # For now just do food potential
            max_food_val = max([ants.potential_map[r][c]['FOOD'] for ((r, c), d) in surrounding])
            max_explore_val = max([ants.potential_map[r][c]['EXPLORE'] for ((r, c), d) in surrounding])
            max_combat_val = max([ants.potential_map[r][c]['COMBAT'] for ((r, c), d) in surrounding])
            
            if max_food_val!=0 and max_food_val >= max_explore_val and max_food_val >= max_combat_val:
                orders['food']+=1
                directions = [d for ((r, c), d) in surrounding if ants.potential_map[r][c]['FOOD']==max_food_val]
            elif max_explore_val!=0 and max_explore_val > max_food_val and max_explore_val > max_combat_val:
                orders['explore']+=1
                directions = [d for ((r, c), d) in surrounding if ants.potential_map[r][c]['EXPLORE']==max_explore_val]
            elif max_combat_val!=0 and max_combat_val > max_food_val and max_combat_val > max_explore_val:
                orders['combat']+=1
                directions = [d for ((r, c), d) in surrounding if ants.potential_map[r][c]['COMBAT']==max_combat_val]        
            elif max_explore_val==0 and max_food_val==0:
                orders['random']+=1
                directions = ['n','s','e','w']
                random.shuffle(directions)          
            else:
                logging.info("THIS SHOULDN'T HAPPEN!?")
        
            # Move the an in one of the available directions
            ant_moved = False
            while directions:
                direction = random.choice(directions)
                directions.remove(direction)
                new_loc = ants.destination(ant_loc, direction)
                if ants.passable(new_loc):
                    ants.issue_order((ant_loc, direction))
                    ant_moved = True
                    break    
            if ant_moved == False:
                logging.info("Ant " + str(ant_loc) + " appears to be stuck!")    

            # check if we still have time left to calculate more orders
            if ants.time_remaining() < ants.turntime * 0.08:
                logging.info("Had to end turn early due to time limit!")
                return

        stats = {}
        stats['TOTAL_ANTS'] = len(ants.my_ants())
        stats['TOTAL_FOOD'] = len(ants.food())
        stats['ENEMY_HILLS'] = len(ants.enemy_hills())
        stats['UNKNOWN'] = len(ants.unknown())
        stats['TOTAL_SIZE'] = ants.rows * ants.cols
        known = stats['TOTAL_SIZE'] - stats['UNKNOWN']
        stats['PERCENT_EXPLORED'] = str(float(known) / float(stats['TOTAL_SIZE']) * 100.0) + "%"
        stats['ORDERS'] = ["%s: %s" % (k,v) for k, v in orders.iteritems()]
        for stat in stats.keys():
            logging.info(str(stat) + ": " + str(stats[stat]))
        logging.info("-----------")
            
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
