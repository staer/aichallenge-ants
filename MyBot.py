#!/usr/bin/env python
from ants import *
from random import choice, shuffle
import time

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/MyBot.log',
                    filemode='w')

turn_number = 0

EXPLORE = 1
TRAVEL = 2
PATROL = 3

ORDERS = {
    'FOOD': 1,
    'EXPLORE': 2,
}

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
    def __init__(self):
        # define class level variables, will be remembered between turns
        self.standing_orders = {}
    
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
        
        
        future_ant_locations = []
        current_orders = {}     # Current orders to execute this turn
        food_list = ants.food() # All the available food
        available_food = ants.food()    # Food that isn't being targetted
        
        
        for ant in self.standing_orders.keys():
            if self.standing_orders[ant]['order'] == ORDERS['FOOD'] and self.standing_orders[ant]['target'] in available_food:
                # It is possible that we ate the food so it's no longer there
                available_food.remove(self.standing_orders[ant]['target'])
        
        ants_with_orders = self.standing_orders.keys()
        
        for ant in ants.my_ants():
            needs_order = True
            # Does the ant already have a standing order? If so go ahead and do that
            if ant in ants_with_orders:
                needs_order = False
                current_orders[ant] = self.standing_orders[ant]
                current_orders[ant]['duration'] = current_orders[ant]['duration'] - 1
                
                # If we have reached the target (or timed out?)
                if current_orders[ant]['target'] == ant or current_orders[ant]['duration']<0:
                    needs_order = True
                    del current_orders[ant]

            if needs_order:
                # TODO - Give the ant an order!
                
                # For now we jsut make the ant search out food (or sit still if it can't find any, i guess)
                current_order = ORDERS['FOOD']

                if current_order == ORDERS['FOOD']:
                    nearby_food = ants.nearby_food(ant, available_food)  
                    logging.info("Food near " + str(ant) + " = " + str(nearby_food))
                    
                    food, path = ants.find_first_path(ant, nearby_food)
                    if food:
                        available_food.remove(food)
                        current_orders[ant] = {
                            'order': ORDERS['FOOD'],
                            'target': food,
                            'path': path,
                            'duration': len(path) + int(0.3*len(path)),
                        }
                    else:
                        if nearby_food:
                            logging.info("Coudln't find a valid path to any of the food")
                        else:
                            logging.info("No nearby food!")
        
        # Execute the "current" orders
        self.standing_orders = {}
        for ant in current_orders.keys():
            current_order = current_orders[ant]['order']
            
            if current_order == ORDERS['FOOD']:
                # Issue an order to the next step on the path
                # This should be factored out
                path = current_orders[ant]['path']
                index = path.index(ant) # Get the current location in the path
                logging.info("Ant at " + str(ant) + " going to " + str(current_orders[ant]['target']))
                dest = path[index+1]    # Get the "next step"
                # Get the direction to move to get there
                directions = ants.direction(ant, dest)
                ant_moved = False
                while directions:
                    direction = directions[0]
                    directions.remove(direction)
                    new_loc = ants.destination(ant, direction)
                    if ants.passable(new_loc, future_ant_locations):
                        ants.issue_order((ant, direction))
                        ant_moved = True
                        self.standing_orders[new_loc] = current_orders[ant]                        
                        # Save the new location
                        future_ant_locations.append(new_loc)
                        break
                if not ant_moved:
                    logging.info("Ant at " + str(ant) + " appears to be stuck!")
                    future_ant_locations.append(ant)
                    # don't update the standing orders for a stuck any, just give them
                    # new orders
                    
            else:
                logging.info("Ant at " + str(ant) + " has no order!")
                                    
        
        # Calculate some turn statistics
        stats = {}
        stats['TOTAL_ANTS'] = len(ants.my_ants())
        stats['TOTAL_FOOD'] = len(ants.food())
        stats['ENEMY_HILLS'] = len(ants.enemy_hills())
        for ant_loc in self.standing_orders.keys():
            if self.standing_orders[ant_loc]['order'] not in stats:
                stats[self.standing_orders[ant_loc]['order']] = 1
            else:
                stats[self.standing_orders[ant_loc]['order']]+=1
                
        for stat in stats.keys():
            logging.info(str(stat) + ": " + str(stats[stat]))
        logging.info("Of " + str(len(food_list)) + " known food, " + str(len(available_food)) + " are NOT being gathered.")
        
        logging.info("Finishing turn " + str(turn_number))
        logging.info("-------------")
        # End turn!            
        return    
            
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
