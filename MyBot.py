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
    'NOTHING': -1,
    'FOOD': 1,
    'EXPLORE': 2,
    'PATROL': 3,
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
    
    def move_along_path(self, ants, ant, current_orders):
        """ Issue an order to move ant, along path"""
        
        path = current_orders[ant]['path']
        index = path.index(ant) # Get the current location in the path
        #logging.info("Ant at " + str(ant) + " going to " + str(current_orders[ant]['target']))
        dest = path[index+1]    # Get the "next step"
        
        # Get the direction to move to get there
        directions = ants.direction(ant, dest)
        while directions:
            direction = directions[0]
            directions.remove(direction)
            new_loc = ants.destination(ant, direction)
            if ants.passable(new_loc):
                ants.issue_order((ant, direction))
                self.standing_orders[new_loc] = current_orders[ant]                        
                return True
                
        return False    #Coudln't move the ant
        
    # do turn is run once per turn
    # the ants class has the game state and is updated by the Ants.run method
    # it also has several helper methods to use
    def do_turn(self, ants):
        global turn_number
        turn_number = turn_number + 1
        logging.info("Starting turn " + str(turn_number))
        
        
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
            
            #########################################
            # Process Ants That Already Have Orders #
            #########################################
            if ant in ants_with_orders:
                needs_order = False
                current_orders[ant] = self.standing_orders[ant]
                current_orders[ant]['duration'] = current_orders[ant]['duration'] - 1                

                # If we have reached the target (or timed out?)
                if current_orders[ant]['target'] == ant or current_orders[ant]['duration'] < 0:
                    needs_order = True
                    del current_orders[ant]

            if needs_order:                
                # For now we jsut make the ant search out food (or sit still if it can't find any, i guess)
                current_order = ORDERS['FOOD']

                ###############
                # ORDER: FOOD #
                ###############
                if current_order == ORDERS['FOOD']:
                    nearby_food = ants.nearby_food(ant, available_food)  
                    
                    food, path = ants.find_first_path(ant, nearby_food)
                    if food:
                        available_food.remove(food)
                        current_orders[ant] = {
                            'order': ORDERS['FOOD'],
                            'target': food,
                            'path': path,
                            'duration': len(path) + int(0.3*len(path)),
                        }
                    # No food was found, either from a bad path or just no food in range
                    else:
                        # If we can't find food, patrol instead
                        current_order = ORDERS['EXPLORE']
                        if nearby_food:
                            logging.info("Coudln't find a valid path to any of the food")
                        else:
                            logging.info("No nearby food!")
                
                ##################
                # ORDER: EXPLORE #
                ##################
                if current_order == ORDERS['EXPLORE']:
                    nearby_unknowns = ants.nearby_unknowns(ant)
                    
                    dest, path = ants.find_first_path(ant, nearby_unknowns)
                    if dest:
                        logging.info("YAY, Found an exploration path!")
                        current_orders[ant] = {
                            'order': ORDERS['PATROL'],
                            'target': dest,
                            'path': path,
                            'duration': len(path) + int(0.3 * len(path))
                        }
                        
                    else:
                        current_order = ORDERS['PATROL']
                        logging.info("OH NOES. Nothing to explore!")
                    
                    
                
                #################
                # ORDER: PATROL #
                #################
                if current_order == ORDERS['PATROL']:
                    nearby_location = ants.nearby_location(ant)
                    path = ants.find_path(ant, nearby_location)
                    if path:
                        current_orders[ant] = {
                            'order': ORDERS['PATROL'],
                            'target': nearby_location,
                            'path': path,
                            'duration': len(path) + int(0.3*len(path))
                        }
                    else:
                        current_orders[ant] = {
                            'order': ORDERS['NOTHING']
                        }
                        logging.info("Coudln't find a valid path to the nearby location!")
                        

                
        logging.info("Ants: " + str(len(ants.my_ants())))
        logging.info("Orders: " + str(len(current_orders)))
        ################################
        # Execute the "current" orders #
        ################################
        self.standing_orders = {}
        logging.info("STARTING EXECUTION")
        for ant in current_orders.keys():
            current_order = current_orders[ant]['order']
            
            #################
            # EXECUTE: FOOD #
            #################
            if current_order == ORDERS['FOOD']:  
                ant_moved = self.move_along_path(ants, ant, current_orders)
                if ant_moved == False:
                    logging.info("Food ant at " + str(ant) + " appears to be stuck!")                    
                    
            ###################
            # EXECUTE: PATROL #
            ###################
            elif current_order == ORDERS['PATROL']:
                ant_moved = self.move_along_path(ants, ant, current_orders)
                if ant_moved == False:
                    logging.info("Patrol ant at " + str(ant) + " appears to be stuck!")
                    
            ####################
            # EXECUTE: EXPLORE #
            ####################
            elif current_order == ORDERS['EXPLORE']:
                ant_moved = self.move_along_path(ants, ant, current_orders)
                if ant_moved == False:
                    logging.info("Explore ant at " + str(ant) + " appears to be stuck!")
            else:
                logging.info("Ant at " + str(ant) + " has an unknown order: " + str(current_order))
        logging.info("DONE EXECUTION")                            
        
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
