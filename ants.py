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
#console = logging.StreamHandler()
#console.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
#console.setFormatter(formatter)
#logging.getLogger('').addHandler(console)


MY_ANT = 0
ANTS = 0
DEAD = -1
LAND = -2
FOOD = -3
WATER = -4
UNKNOWN = -5

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
        self.viewradius = 0
        self.attackradius = 0
        self.spawnradius = 0
        
        self.current_paths = 0

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
                    self.viewradius = sqrt(self.viewradius2)
                elif key == 'attackradius2':
                    self.attackradius2 = int(tokens[1])
                    self.attackradius = sqrt(self.attackradius2)
                elif key == 'spawnradius2':
                    self.spawnradius2 = int(tokens[1])
                    self.spwanradius = sqrt(self.spawnradius2)
                elif key == 'turns':
                    self.turns = int(tokens[1])
        self.map = [[UNKNOWN for col in range(self.cols)]
                    for row in range(self.rows)]

    def update(self, data):
        self.current_paths = 0
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
                        
    def time_remaining(self):
        return self.turntime - int(1000 * (time.time() - self.turn_start_time))
    
    def issue_order(self, order):
        'issue an order by writing the proper ant location and direction'
        (row, col), direction = order
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
        'calculate the manhatten closest distance between to locations'
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), self.cols - abs(col1 - col2))
        d_row = min(abs(row1 - row2), self.rows - abs(row1 - row2))
        return d_row + d_col
    
    def real_distance(self, loc1, loc2):
        dr = min(abs(loc1[0]-loc2[0]), self.rows - abs(loc1[0]-loc2[0]))
        dc = min(abs(loc1[1]-loc2[1]), self.cols - abs(loc1[1]-loc2[1]))
        d = sqrt(dr**2 + dc**2)
        return d

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
    
    def neighbors(self, loc):
        n = []
        directions = ['n', 's', 'e', 'w']
        for direction in directions:
            d = self.destination(loc, direction)
            if self.passable(d):
                n.append(d)
        return n    
    
    
    def find_path(self, start, end):
        if self.current_paths > 6:
            logging.info("Calculated too many paths, skipping the rest for the turn")
            return []    
        """ Finds a path from start to end using the A* algorithm, WATER tiles is considered the only barrier. """
        closed_set = []
        open_set = [start]
        came_from = {}
        
        g_score = {}
        h_score = {}
        f_score = {}        # f = g + h    
        
        g = 0
        h = self.distance(start, end)
        f = g + h    
        g_score[start] = g
        h_score[start] = h
        f_score[start] = f
        
        iterations = 0

        def reconstruct_path(from_list, node):
            """ Reconstructions a path from node, return a list of map coordinates (row, col) to take to get to node """
            if node in from_list:
                path = reconstruct_path(from_list, from_list[node])
                path.append(node)
                return path
            else:
                return [node]
        
        while open_set:
            iterations = iterations + 1
            if iterations > self.viewradius2:
                self.current_paths = self.current_paths + 1 # Increment timed-out calculations
                return []
            # Get the item from open set with the smallest f-score
            x = open_set[0]
            for i in open_set:
                if f_score[i] < f_score[x]:
                    x = i
                    
            if x == end:
                self.current_paths = self.current_paths + 1 # Increment sucessful calculations
                path = reconstruct_path(came_from, end)
                return path
                    
            open_set.remove(x)
            closed_set.append(x)
            
            for neighbor in self.neighbors(x):
                if neighbor in closed_set:
                    continue
                
                tentative_is_better = False
                    
                tentative_g_score = g_score[x] + 1
                
                if neighbor not in open_set:
                    open_set.append(neighbor)
                    tentative_is_better = True
                elif tentative_g_score < g_score[neighbor]:
                    tentative_is_better = True
                else:
                    tentative_is_better = False
                    
                if tentative_is_better == True:
                    came_from[neighbor] = x
                    g_score[neighbor] = tentative_g_score
                    h = self.distance(neighbor, end)
                    h_score[neighbor] = h
                    f_score[neighbor] = tentative_g_score + h
                    
                    
        # No path!?
        logging.info("THIS IS BAD, SHOULD NEVER HAPPEN!")
        return []            

    def find_first_path(self, location, destinations):
        random.shuffle(destinations)    # Add some randomness to our lives!
        path = None
        dest = None
        for d in destinations:
            path = self.find_path(location, d)
            if path:
                return (d, path)
        
        return (None, None)

    def closest_unknown(self, loc, exclude=None):
        lr, lc = loc

        if exclude==None:
            exclude = [] 
        mindist = sys.maxint
        closest = None

        for row in xrange(self.rows):
            for col in xrange(self.cols):
                if self.map[row][col] == UNKNOWN and (row, col) not in exclude:
                    d = self.distance(loc, (row, col))
                    if d < mindist:
                        mindist = d
                        closest = (row, col)
        return closest
        
    def nearby_location(self, loc, radius=5):
        """ Find a nearby non-water location """
        locations = []
        for r in xrange(-radius, radius):
            for c in xrange(-radius, radius):
                row = loc[0] + r
                col = loc[1] + c
                if row < 0:
                    row += self.rows
                if col < 0:
                    col += self.cols
                if row > self.rows-1:
                    row -= self.rows
                if col > self.cols-1:
                    col -= self.cols
                
                if self.map[row][col] != WATER and self.map[row][col] != UNKNOWN:
                    locations.append((row,col))
                    
        # Send back a random item from the set we just created
        return random.choice(locations)
        
    def nearby_unknown(self, loc, exclude=None):
        lr, lc = loc
                
        if exclude==None:
            exclude = [] 
        mindist = sys.maxint
        closest = None

        #for row in xrange(self.rows):
        #    for col in xrange(self.cols):
        unknowns = []
        for r in xrange(-5,5):
            for c in xrange(-5,5):
                row = lr + r
                col = lc +c
                if row < 0:
                    row += self.rows
                if col < 0:
                    col += self.cols
                if row > self.rows-1:
                    row -= self.rows
                if col > self.cols-1:
                    col -= self.cols
                    
                #logging.info("Start: " + str(loc))
                #logging.info("Row: " + str(row))
                #logging.info("Col: " + str(col))    
                    
                if self.map[row][col] == UNKNOWN and (row, col) not in exclude:
                    unknowns.append((row,col))
                    #d = self.distance(loc, (row, col))
                    #if d < mindist:
                    #    mindist = d
                    #    closest = (row, col)
        if unknowns:
            u = random.choice(unknowns)
            logging.info("Found random starting at: " + str(loc) + " to " + str(u))
            return u
        else:
            return None
        # return closest
            
    def random_nearby(self, loc, radius=10):
        """ Returns a random valid location radius'ish, units away."""
        while True:
            r_offset = random.randint(-1 * radius//2, radius//2)
            c_offset = random.randint(-1 * radius//2, radius//2)
            row = loc[0] + r_offset
            col = loc[0] + c_offset
            
            if row < 0:
                row += self.rows
            if col < 0:
                col += self.cols
            if row > self.rows-1:
                row -= self.rows
            if col > self.cols-1:
                col -= self.cols
                
            if self.map[row][col]!=WATER:
                return (row,col)
                     
    
    def closest_food(self, loc, exclude=None):
        if exclude==None:
            exclude = [] 
        mindist = sys.maxint
        closest = None
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                if self.map[row][col] == FOOD:
                        mindist = d
                        closest = (row, col)
        #logging.info("Closest: ")
        return closest   
        
    def nearby_food(self, location, food_list):
        results = []
        for food_loc in food_list:
            dist = self.real_distance(location, food_loc)
            if dist < self.viewradius:
                results.append(food_loc)
        return results
         

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
                        logging.info("OMG CAUGHT AN EXCEPTION")
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
