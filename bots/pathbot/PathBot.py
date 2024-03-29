#!/usr/bin/env python
from ants import *
import random
import time

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/MyBot.log',
                    filemode='w')

turn_number = 0

ORDERS = {
    'NOTHING': -1,
    'FOOD': 1,
    'EXPLORE': 2,
    'PATROL': 3,
    'SIEGE': 4,     # Attack an enemy hill
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
        
    def move_to_target(self, ants, ant, current_orders):
        target = current_orders[ant]['target']
        directions = ants.direction(ant, target)
        while directions:
            direction = directions[0]
            directions.remove(direction)
            new_loc = ants.destination(ant, direction)
            if ants.passable(new_loc):
                ants.issue_order((ant, direction))
                self.standing_orders[new_loc] = current_orders[ant]
                return True
        return False
        
    def move_along_path(self, ants, ant, current_orders):
        """ Issue an order to move ant, along path"""
        
        path = current_orders[ant]['path']
        
        # If there is no path, just do a "dumb" move.
        if not path:
            return self.move_to_target(ants, ant, current_orders)
        
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
                target = current_orders[ant]['target']
                if target == ant or current_orders[ant]['duration'] < 0 or ants.path_has_water(current_orders[ant]['path']):
                    if ants.map[target[0]][target[1]] == -4:
                        logging.info("THE TARGET WAS WATER!")
                    
                    needs_order = True
                    del current_orders[ant]

            if needs_order:                
                # For now we jsut make the ant search out food (or sit still if it can't find any, i guess)
                current_order = ORDERS['FOOD']

                # We should really just get a list of all ants near any hill, then be more specific later?
                nearby_enemy_hills = ants.nearby_enemy_hills(ant)
                if len(nearby_enemy_hills) > 0:
                    current_order=ORDERS['SIEGE']

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
                        current_orders[ant] = {
                            'order': ORDERS['PATROL'],
                            'target': dest,
                            'path': path,
                            'duration': len(path) + int(0.3 * len(path))
                        }
                    elif nearby_unknowns:
                        dest = nearby_unknowns[0]
                        current_orders[ant] = {
                            'order': ORDERS['PATROL'],
                            'target': dest,
                            'path': None,
                            'duration': int(ants.distance(dest, ant) * 1.3)
                        }
                    else:
                        # If there are no nearby unknowns, just patrol
                        current_order = ORDERS['PATROL']
                                                
                
                ################
                # ORDER: SIEGE #
                ################
                if current_order == ORDERS['SIEGE']:
                    # nearby_enemy_hills calculated above
                    dest, path = ants.find_first_path(ant, nearby_enemy_hills)
                    if dest:
                        current_orders[ant] = {
                            'order': ORDERS['SIEGE'],
                            'target': dest,
                            'path': path,
                            'duration': len(path) + int(0.3 * len(path))
                        }
                    else:
                        current_order = ORDERS['PATROL']
                        
                #################
                # ORDER: PATROL #
                #################
                if current_order == ORDERS['PATROL']:
                    nearby_location = ants.nearby_location(ant)

                    current_orders[ant] = {
                        'order': ORDERS['PATROL'],
                        'target': nearby_location,
                        'path': None,
                        'duration': int(ants.distance(nearby_location, ant) * 1.3)
                    }                        

                
        logging.info("Ants: " + str(len(ants.my_ants())))
        logging.info("Orders: " + str(len(current_orders)))
        ################################
        # Execute the "current" orders #
        ################################
        self.standing_orders = {}
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
                #ant_moved = self.move_along_path(ants, ant, current_orders)
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
                    
            ###################
            # EXECUTE: SIEGE #
            ###################
            elif current_order == ORDERS['SIEGE']:
                ant_moved = self.move_along_path(ants, ant, current_orders)
                if ant_moved == False:
                    logging.info("Siege ant at " + str(ant) + " appears to be stuck!")
                    
            ####################
            # EXECUTE: NOTHING #
            ####################
            elif current_order == ORDERS['NOTHING']:
                directions = ['n','s','e','w']
                random.shuffle(directions)
                while directions:
                    direction = directions[0]
                    directions.remove(direction)
                    new_loc = ants.destination(ant, direction)
                    if ants.passable(new_loc):
                        ants.issue_order((ant, direction))
                        break
                    
                    
            else:
                logging.info("Ant at " + str(ant) + " has an unknown order: " + str(current_order))                          
        
        # Calculate some turn statistics
        stats = {}
        stats['TOTAL_ANTS'] = len(ants.my_ants())
        stats['TOTAL_FOOD'] = len(ants.food())
        stats['ENEMY_HILLS'] = len(ants.enemy_hills())
        
        stats['TOTAL_UNKNOWN'] = len(ants.unknown())
        stats['TOTAL_SIZE'] = ants.rows * ants.cols
        stats['PATH_CACHE_SIZE'] = len(ants.path_cache)
        
        for ant_loc in self.standing_orders.keys():
            order = [k for k, v in ORDERS.iteritems() if v == self.standing_orders[ant_loc]['order']]
            if len(order)==1:
                order = "ORDER_%s" % order[0]
            else:
                order = "ORDER_UNKNOWN"
        
            if self.standing_orders[ant_loc]['order'] not in stats:
                stats[order] = 1
            else:
                stats[order]+=1
                
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
