#!/usr/bin/env python
from ants import *
import random

turn_number = 0

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
        
        ants.initialize_diffusion_map()
        ants.diffuse_map()
        
        for ant_loc in ants.my_ants():
            # Move each ant in the direction of it's highest diffusion value
            up_loc = ants.destination(ant_loc, 'n')
            left_loc = ants.destination(ant_loc, 'w')
            right_loc = ants.destination(ant_loc, 'e')
            down_loc = ants.destination(ant_loc, 's')
            
            up_val = ants.diffusion_map[up_loc[0]][up_loc[1]]
            left_val = ants.diffusion_map[left_loc[0]][left_loc[1]]
            right_val = ants.diffusion_map[right_loc[0]][right_loc[1]]
            down_val = ants.diffusion_map[down_loc[0]][down_loc[1]]
            
            values = [(up_val, 'n'), (left_val, 'w'), (right_val, 'e'), (down_val, 's')]
            values.sort()
            values.reverse()
            directions = [direction for val, direction in values]
            if up_val==0 and down_val==0 and right_val==0 and left_val==0:
                directions = ['n','s','e','w']
                random.shuffle(directions)
            
            while directions:
                direction = directions[0]
                directions.remove(direction)    

                new_loc = ants.destination(ant_loc, direction)
                # passable returns true if the location is land
                if (ants.passable(new_loc)):
                    # an order is the location of a current ant and a direction
                    ants.issue_order((ant_loc, direction))
                    break
                    # stop now, don't give 1 ant multiple orders
                    
            # check if we still have time left to calculate more orders
            if ants.time_remaining() < 10:
                break
                

        stats = {}
        stats['TOTAL_ANTS'] = len(ants.my_ants())
        stats['TOTAL_FOOD'] = len(ants.food())
        stats['ENEMY_HILLS'] = len(ants.enemy_hills())

        stats['TOTAL_UNKNOWN'] = len(ants.unknown())
        stats['TOTAL_SIZE'] = ants.rows * ants.cols
        stats['PATH_CACHE_SIZE'] = len(ants.path_cache)

        for stat in stats.keys():
            logging.info(str(stat) + ": " + str(stats[stat]))
            
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
