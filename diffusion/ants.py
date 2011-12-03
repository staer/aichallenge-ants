#!/usr/bin/env python
import sys
import traceback
import random
import time
from collections import defaultdict
from math import sqrt

import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='/tmp/MyBot.log',
                    filemode='w')

MY_ANT = 0
ANTS = 0
DEAD = -1
LAND = -2
FOOD = -3
WATER = -4
UNKNOWN = -5

DIFFUSION = {
    'FOOD': 1000,
    'UNKNOWN': 200,
    'OWN_HILL': 0,
    'ENEMY_HILL': 600,
    'ENEMY_ANT': 200,
    'MAX_VALUE': 1000,
    'WATER': 0,
}

PLAYER_ANT = 'abcdefghij'
HILL_ANT = string = 'ABCDEFGHIJ'
PLAYER_HILL = string = '0123456789'
MAP_OBJECT = '?%*.!'
MAP_RENDER = PLAYER_ANT + HILL_ANT + PLAYER_HILL + MAP_OBJECT

AIM = {'n': (-1, 0),
       'e': (0, 1),
       's': (1, 0),
       'w': (0, -1)}
RIGHT = {'n': 'e',
         'e': 's',
         's': 'w',
         'w': 'n'}
LEFT = {'n': 'w',
        'e': 'n',
        's': 'e',
        'w': 's'}
BEHIND = {'n': 's',
          's': 'n',
          'e': 'w',
          'w': 'e'}

class Ants():
    def __init__(self):
        self.cols = None
        self.rows = None
        self.map = None
        self.hill_list = {}
        self.ant_list = {}
        self.dead_list = defaultdict(list)
        self.food_list = []
        self.turntime = 0
        self.loadtime = 0
        self.turn_start_time = None
        self.vision = None
        self.viewradius2 = 0
        self.attackradius2 = 0
        self.spawnradius2 = 0
        self.turns = 0
        
        self.diffusion_map = None
        self.potential_map = None
        self.ant_locations = []
        
        

    def setup(self, data):
        'parse initial input and setup starting game state'
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()
                key = tokens[0]
                if key == 'cols':
                    self.cols = int(tokens[1])
                elif key == 'rows':
                    self.rows = int(tokens[1])
                elif key == 'player_seed':
                    random.seed(int(tokens[1]))
                elif key == 'turntime':
                    self.turntime = int(tokens[1])
                elif key == 'loadtime':
                    self.loadtime = int(tokens[1])
                elif key == 'viewradius2':
                    self.viewradius2 = int(tokens[1])
                elif key == 'attackradius2':
                    self.attackradius2 = int(tokens[1])
                elif key == 'spawnradius2':
                    self.spawnradius2 = int(tokens[1])
                elif key == 'turns':
                    self.turns = int(tokens[1])
        self.map = [[UNKNOWN for col in range(self.cols)]
                    for row in range(self.rows)]
        self.diffusion_map = [[0 for col in range(self.cols)]
                    for row in range(self.rows)]
                    
        # Just another name for a diffusion map
        self.potential_map = [[{'FOOD': 0, 'EXPLORE': 0, 'COMBAT': 0} for col in range(self.cols)]
                    for row in range(self.rows)]
    
    def update(self, data):
        'parse engine input and update the game state'
        # start timer
        self.turn_start_time = time.time()
        
        # reset vision
        self.vision = None
        
        # clear hill, ant and food data
        self.hill_list = {}
        for row, col in self.ant_list.keys():
            self.map[row][col] = LAND
        self.ant_list = {}
        for row, col in self.dead_list.keys():
            self.map[row][col] = LAND
        self.dead_list = defaultdict(list)
        for row, col in self.food_list:
            self.map[row][col] = LAND
        self.food_list = []
        
        # update map and create new ant and food lists
        for line in data.split('\n'):
            line = line.strip().lower()
            if len(line) > 0:
                tokens = line.split()
                if len(tokens) >= 3:
                    row = int(tokens[1])
                    col = int(tokens[2])
                    if tokens[0] == 'w':
                        self.map[row][col] = WATER
                    elif tokens[0] == 'f':
                        self.map[row][col] = FOOD
                        self.food_list.append((row, col))
                    else:
                        owner = int(tokens[3])
                        if tokens[0] == 'a':
                            self.map[row][col] = owner
                            self.ant_list[(row, col)] = owner
                        elif tokens[0] == 'd':
                            # food could spawn on a spot where an ant just died
                            # don't overwrite the space unless it is land
                            if self.map[row][col] == LAND:
                                self.map[row][col] = DEAD
                            # but always add to the dead list
                            self.dead_list[(row, col)].append(owner)
                        elif tokens[0] == 'h':
                            owner = int(tokens[3])
                            self.hill_list[(row, col)] = owner
                            
        self.ant_locations = self.my_ants()
        
        for row in xrange(self.rows):
            for col in xrange(self.cols): 
                if self.map[row][col] == UNKNOWN and self.visible((row, col)):
                    self.map[row][col] = LAND                                       
                    
    def diffuse(self):
        diffusion_count = 0
        time_left = self.turntime * 0.35
        time_remaining = self.time_remaining()
        
        pMap = self.get_fixed_potentials()
        self.set_fixed_potentials(pMap)
        
        # Create an ant map so we don't diffuse food potentials
        ant_map = [[False for col in xrange(self.cols)] for row in xrange(self.rows)]
        for row, col in self.my_ants():
            ant_map[row][col] = True
        
        while time_remaining > time_left:
            diffusion_count = diffusion_count + 1
        
            newMap = [[{'FOOD': 0, 'EXPLORE': 0, 'COMBAT': 0} for col in xrange(self.cols)]
                for row in xrange(self.rows)]
                
            for row in xrange(self.rows):
                for col in xrange(self.cols):
                    
                    # We never diffuse water!
                    if self.map[row][col] == WATER:
                        newMap[row][col]['FOOD'] = 0
                        newMap[row][col]['EXPLORE'] = 0
                        continue
            
                    surrounding = self.surrounding_squares((row, col))
                    
                    food_total = sum([self.potential_map[r][c]['FOOD'] for ((r,c), d) in surrounding])
                    explore_total = sum([self.potential_map[r][c]['EXPLORE'] for ((r,c), d) in surrounding])
                    combat_total = sum([self.potential_map[r][c]['COMBAT'] for ((r,c), d) in surrounding])

                    newMap[row][col]['FOOD'] = max(0.25 * food_total, 0)
                    newMap[row][col]['EXPLORE'] = max(0.25 * explore_total, 0)
                    newMap[row][col]['COMBAT'] = max(0.25 * combat_total, 0)
            
                    if ant_map[row][col]==True:
                        newMap[row][col]['FOOD'] = 0
                        newMap[row][col]['EXPLORE'] = 0
            
            self.potential_map = newMap  
            self.set_fixed_potentials(pMap)          
            
            time_remaining = self.time_remaining()
        
        # Before exiting give some useful info!
        logging.info("Diffused " + str(diffusion_count) + " times.")
        
    def set_fixed_potentials(self, pMap):
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                for k in pMap[row][col].iterkeys():
                    if pMap[row][col][k] > 0:
                        self.potential_map[row][col][k] = pMap[row][col][k]    
    
    def get_fixed_potentials(self):
        newMap = [[{'FOOD': 0, 'EXPLORE': 0, 'COMBAT': 0} for col in xrange(self.cols)]
            for row in xrange(self.rows)]
        
        # Fill in the food potential map
        food = self.food()
        for row, col in food:
            newMap[row][col]['FOOD'] = DIFFUSION['FOOD']
            
        # Fill in the unknown potential map
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                if self.map[row][col]==UNKNOWN:
                    surrounding = self.surrounding_squares((row, col))
                    # Get the number of neighbors that we know about
                    n = len([d for ((r, c), d) in surrounding if self.map[r][c]!=UNKNOWN])
                    # If we know about some of it's neighbors then the square is on the "edge" of what we know about
                    if n > 0:
                        newMap[row][col]['EXPLORE'] = DIFFUSION['UNKNOWN']   
                        
        # Fill in enemy ant hills
        hills = self.enemy_hills()
        for ((row, col), owner) in hills:
            # TODO: Enemy hill is more enticing if there are fewer enemy ants nearby
            newMap[row][col]['COMBAT'] = DIFFUSION['ENEMY_HILL'] 
            
        # Fill in enemy ants
        enemies = self.enemy_ants()
        for ((row, col), owner) in enemies:
            # TODO: Double or triple this if they are near one of our hills?
            newMap[row][col]['COMBAT'] = DIFFUSION['ENEMY_ANT']
    
        return newMap

    def print_diffusion_map(self):
        for row in xrange(self.rows):
            line = ""
            for col in xrange(self.cols):
                output = ""
                if self.map[row][col]==WATER:
                    output += "="
                elif (row, col) in self.my_ants():
                    output += "A"# + str(self.diffusion_map[row][col])
                elif (row, col) in self.my_hills():
                    output += "H"# + str(self.diffusion_map[row][col])
                elif self.map[row][col] == UNKNOWN and self.diffusion_map[row][col]==0:
                    output += "*"
                elif (row, col) in self.food():
                    output += "F" + str(self.diffusion_map[row][col])
                elif self.diffusion_map[row][col] == 0:
                    output += " "
                else:    
                    output += str(self.diffusion_map[row][col])
                output = output.rjust(6)
                line += output
            
            # Log out each row
            logging.info(line)
                   
    def surrounding_squares(self, location):
        """ Returns a list of ((row, col), 'direction') tuples"""
        row, col = location
        output = []
        
        # NORTH
        if row==0:
            loc = (self.rows-1, col)
            output.append((loc, 'n'))
        else:
            loc = (row-1, col)
            output.append((loc, 'n'))
        
        # SOUTH
        if row==self.rows-1:
            loc = (0, col)
            output.append((loc, 's'))
        else:
            loc = (row+1, col)
            output.append((loc, 's'))
        
        # EAST
        if col==self.cols-1:
            loc = (row, 0)
            output.append((loc, 'e'))
        else:
            loc = (row, col+1)
            output.append((loc, 'e'))
        
        # WEST
        if col==0:
            loc = (row, self.cols-1)
            output.append((loc, 'w'))
        else:
            loc = (row, col-1)
            output.append((loc, 'w'))

        return output
                           
    def unknown(self):
        output = []
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                if self.map[row][col] == UNKNOWN:
                    output.append((row,col))
        return output         
    def time_remaining(self):
        return self.turntime - int(1000 * (time.time() - self.turn_start_time))
    
    def issue_order(self, order):
        'issue an order by writing the proper ant location and direction'
        (row, col), direction = order
        
        src = (row, col)
        dest = self.destination(src, direction)
        if src in self.ant_locations:
            self.ant_locations.remove(src)    # Remove where we were
        self.ant_locations.append(dest)    # Add where we're going!
        
        sys.stdout.write('o %s %s %s\n' % (row, col, direction))
        sys.stdout.flush()
        
    def finish_turn(self):
        'finish the turn by writing the go line'
        sys.stdout.write('go\n')
        sys.stdout.flush()
    
    def my_hills(self):
        return [loc for loc, owner in self.hill_list.items()
                    if owner == MY_ANT]

    def enemy_hills(self):
        return [(loc, owner) for loc, owner in self.hill_list.items()
                    if owner != MY_ANT]
        
    def my_ants(self):
        'return a list of all my ants'
        return [(row, col) for (row, col), owner in self.ant_list.items()
                    if owner == MY_ANT]

    def enemy_ants(self):
        'return a list of all visible enemy ants'
        return [((row, col), owner)
                    for (row, col), owner in self.ant_list.items()
                    if owner != MY_ANT]

    def food(self):
        'return a list of all food locations'
        return self.food_list[:]

    def passable(self, loc):
        'true if not water'
        row, col = loc
        
        # Don't let ants run into each other
        if (row, col) in self.ant_locations:
            return False
            
        return self.map[row][col] != WATER
    
    def unoccupied(self, loc):
        'true if no ants are at the location'
        row, col = loc
        return self.map[row][col] in (LAND, DEAD)

    def destination(self, loc, direction):
        'calculate a new location given the direction and wrap correctly'
        row, col = loc
        d_row, d_col = AIM[direction]
        return ((row + d_row) % self.rows, (col + d_col) % self.cols)        

    def distance(self, loc1, loc2):
        'calculate the closest distance between to locations'
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), self.cols - abs(col1 - col2))
        d_row = min(abs(row1 - row2), self.rows - abs(row1 - row2))
        return d_row + d_col

    def direction(self, loc1, loc2):
        'determine the 1 or 2 fastest (closest) directions to reach a location'
        row1, col1 = loc1
        row2, col2 = loc2
        height2 = self.rows//2
        width2 = self.cols//2
        d = []
        if row1 < row2:
            if row2 - row1 >= height2:
                d.append('n')
            if row2 - row1 <= height2:
                d.append('s')
        if row2 < row1:
            if row1 - row2 >= height2:
                d.append('s')
            if row1 - row2 <= height2:
                d.append('n')
        if col1 < col2:
            if col2 - col1 >= width2:
                d.append('w')
            if col2 - col1 <= width2:
                d.append('e')
        if col2 < col1:
            if col1 - col2 >= width2:
                d.append('e')
            if col1 - col2 <= width2:
                d.append('w')
        return d

    def visible(self, loc):
        ' determine which squares are visible to the given player '

        if self.vision == None:
            if not hasattr(self, 'vision_offsets_2'):
                # precalculate squares around an ant to set as visible
                self.vision_offsets_2 = []
                mx = int(sqrt(self.viewradius2))
                for d_row in range(-mx,mx+1):
                    for d_col in range(-mx,mx+1):
                        d = d_row**2 + d_col**2
                        if d <= self.viewradius2:
                            self.vision_offsets_2.append((
                                # Create all negative offsets so vision will
                                # wrap around the edges properly
                                (d_row % self.rows) - self.rows,
                                (d_col % self.cols) - self.cols
                            ))
            # set all spaces as not visible
            # loop through ants and set all squares around ant as visible
            self.vision = [[False]*self.cols for row in range(self.rows)]
            for ant in self.my_ants():
                a_row, a_col = ant
                for v_row, v_col in self.vision_offsets_2:
                    self.vision[a_row + v_row][a_col + v_col] = True
        row, col = loc
        return self.vision[row][col]
    
    def render_text_map(self):
        'return a pretty string representing the map'
        tmp = ''
        for row in self.map:
            tmp += '# %s\n' % ''.join([MAP_RENDER[col] for col in row])
        return tmp

    # static methods are not tied to a class and don't have self passed in
    # this is a python decorator
    @staticmethod
    def run(bot):
        'parse input, update game state and call the bot classes do_turn method'
        ants = Ants()
        map_data = ''
        while(True):
            try:
                current_line = sys.stdin.readline().rstrip('\r\n') # string new line char
                if current_line.lower() == 'ready':
                    ants.setup(map_data)
                    bot.do_setup(ants)
                    ants.finish_turn()
                    map_data = ''
                elif current_line.lower() == 'go':
                    ants.update(map_data)
                    # call the do_turn method of the class passed in
                    try:
                        bot.do_turn(ants)
                    except:
                        import traceback
                        formatted_lines = traceback.format_exc()
                        logging.info(str(formatted_lines))
                    ants.finish_turn()
                    map_data = ''
                else:
                    map_data += current_line + '\n'
            except EOFError:
                break
            except KeyboardInterrupt:
                raise
            except:
                # don't raise error or return so that bot attempts to stay alive
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
