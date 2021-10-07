#!/usr/bin/env python3
"""Generates trials json for the experiment."""

import json
import random

def emoji():
    return random.choice('😀😃😄😁😆😅😂️😊😇🙂🙃😉😌😍😘😗😙😚😋😜😝😛🤑🤗🤓😎')

def grid(size):
    
    graph = {}
    layout = {}

    def reward():
        return random.randint(-5, 5)
    
    def state(x, y):
        name = '{}_{}'.format(x, y)
        if name in graph:
            return name

        graph[name] = {}
        layout[name] = [x, y]
        if y < size:
            graph[name]['down'] = [reward(), state(x, y+1)]
        if x < size:
            graph[name]['right'] = [reward(), state(x+1, y)]
        return name

    state(0, 0)

    return {
        'stateLabels': {s: emoji() for s in layout},
        'graph': graph,
        'layout': layout,
        'initial': '0_0',
    }

def grid_trials_exp1():

    yield {
        **grid(3),
        'centerMessage': '<b>Clickable states</b>',
        'edgeDisplay': False,
        'stateDisplay': 'click',
        'stateClickCost': 1,
        'playerImage': 'static/images/spider.png'
    }

def grid_trials_exp2():
    yield {
        **grid(3),
        'centerMessage': '<b>Clickable Edges</b>',
        'edgeDisplay': 'click',
        'stateDisplay': False,
        'edgeClickCost': 1,
        'playerImage': 'static/images/plane.png'
    }



def main():

    trials_exp1 = list(grid_trials_exp1())
    trials_exp2 = list(grid_trials_exp2())
    values = trials_exp1 * 3 + trials_exp2 * 3
    outfile = '../static/json/trials.json'
    with open(outfile, 'w+') as f:
        json.dump(values, f)

    print('wrote {} trials to {}'.format(len(values), outfile))



import numpy as np
import itertools as it
from scipy.io import savemat
import os
import json
from collections import defaultdict

import toolz

# ---------- Constructing environments ---------- #
DIRECTIONS = ('up', 'right', 'down', 'left')
ACTIONS = dict(zip(DIRECTIONS, it.count()))


BRANCH_DIRS = {
    2: {'up': ('right', 'left'),
        'right': ('up', 'down'),
        'down': ('right', 'left'),
        'left': ('up', 'down'),
        'all': ('right', 'left')},
    3: {'up': ('up', 'right', 'left'),
        'right': ('up', 'right', 'down'),
        'down': ('right', 'down', 'left'),
        'left': ('up', 'down', 'left'),
        'all': DIRECTIONS}
}

def move_xy(x, y, direction, dist=1):
    return {
        'right': (x+dist, y),
        'left': (x-dist, y),
        'down': (x, y+dist),
        'up': (x, y-dist),
    }.get(direction)



    
class Layouts:

    def cross(depth):
        graph = {}
        layout = {}
        names = it.count()

        def direct(prev):
            if prev == 'all':
                yield from DIRECTIONS
            else:
                yield prev
        
        def node(d, x, y, prev_dir):
            r = 0  # reward is 0 for now
            name = str(next(names))
            layout[name] = (x, y)
            graph[name] = {}
            if d > 0:
                for direction in direct(prev_dir):
                    x1, y1 = move_xy(x, y, direction, 1)
                    graph[name][direction] = (r, node(d-1, x1, y1, direction))
                                            
            return name
        
        node(depth, 0, 0, 'all')
        return graph, layout


    def tree(branch, depth, first='up', **kwargs):
        graph = {}
        layout = {}
        names = it.count()

        def dist(d):
            if branch == 3:
                return 2 ** (d - 1)
            else:
                return 2 ** (d/2 - 0.5)

        def node(d, x, y, prev_dir):
            r = 0  # reward is 0 for now
            name = str(next(names))
            layout[name] = (x, y)
            graph[name] = {}
            if d > 0:
                for direction in BRANCH_DIRS[branch][prev_dir]:
                    x1, y1 = move_xy(x, y, direction, dist(branch, d))
                    graph[name][direction] = (r, node(d-1, x1, y1, direction))
                                            
            return name

        node(depth, 0, 0, first)
        return graph, layout


    


def rescale(layout):
    names, xy = zip(*layout.items())
    x, y = np.array(list(xy)).T
    y *= -1
    x -= x.min()
    y -= y.min()
    y *= 0.5
    x *= 1.5
    return dict(zip(names, zip(x.tolist(), y.tolist())))


def build(kind, **kwargs):
    graph, layout = getattr(Layouts, kind)(**kwargs)
    return graph, rescale(layout)



if __name__ == '__main__':
    main()
    # s = Stims().run()
