#!/usr/local/bin/python

import random
import re
import sys

DICEPATTERN = re.compile(r'([-\+])?(\d*)d(\d+)')
BONUSPATTERN = re.compile(r'(^|[-\+])(\d+)(?!\d*d)')

BRACKETS = re.compile(r'([-+])?\(([^()]+)\)')
SAFETOEVAL = re.compile(r'^[-+]?\d+[-+]?[-+\d]*$')

PROBLEMATIC = re.compile(r'd\([-+d\d]+\)')

def _compact_sub(m):
    if m.group(1) == '-':
        s = '-'+m.group(2).replace('+', '-')
    elif m.group(1) == '+':
        s = '+'+m.group(2)
    else:
        s = m.group(2)
    if SAFETOEVAL.match(s):
        s = (m.group(1)=='+' and '+' or '')+str(eval(s))
    return s

def _compact(s):
    if PROBLEMATIC.search(s):
        raise ValueError("Variable dice are not allowed (e.g. no 'd(2d3)')")
    s2 = BRACKETS.sub(_compact_sub, s)
    if BRACKETS.search(s2):
        return _compact(s2)
    return s2

def parse(s):
    """Turns a dice string into a dice tuple

    Example: ([6,6,6], 4) == parse('3d6+4')
    
    Note that '-2d6' returns ((-6, -6), 0)
    """
    s = _compact(s.replace(' ', ''))
    raw_dice = DICEPATTERN.findall(s)
    raw_bonus = BONUSPATTERN.findall(s)
    dice = []
    bonus = 0
    if raw_dice:
        for d in raw_dice:
            # Each unit is a tuple translating '+nDx' to (+, n, x)
            dice.extend((int(d[2]) * (d[0] == '-' and -1 or 1),) * ((d[1] != '') and int(d[1]) or 1))
    if raw_bonus:
        for b in raw_bonus:
            # (sign, value)
            bonus = bonus + (int(b[1]) * ((b[0] == '-') and -1 or 1))
    return dice, bonus

def canonical(dice):
    """Turns a dice tuple into a canonical string representation"""
    if type(dice)==str:
        dice = parse(dice)
    out = []
    first = True
    dietypes = list(set(dice[0]))
    dietypes.sort()
    for d in dietypes:
        if first:
            first = False
        else:
            out.append(d < 0 and '-' or '+')
        out.append(str(dice[0].count(d)))
        out.append('d')
        out.append(str(abs(d)))
    if dice[1] != 0:
        if not first:
            out.append(dice[1] < 0 and '-' or '+')
        out.append(str(abs(dice[1])))
    return ''.join(out)

def _roll(d):
    """Rolls a single die"""
    if d == 0:
        return 0
    elif d > 0:
        return random.randint(1, d)
    else:
        return random.randint(d, -1)

def _max(d):
    """Returns the maximum possible roll of a die"""
    return d > 0 and d or -1

def _min(d):
    """Returns the minimum possible roll of a die"""
    return d > 0 and 1 or d

def _median(d):
    """Returns the median roll of a die"""
    return (d+(d > 0 and 1 or -1))/2.0

def _map_dice(d, f):
    """Applies a function to a pile of dice"""
    if type(d) == str:
        d = parse(d)
    elif type(d) == int:
        return f(d)
    # assume d is equivalent to the output of parse.
    result = d[1]
    for die in d[0]:
        result = result + f(die)
    return result

def roll(d):
    return _map_dice(d, _roll)

def max_roll(d):
    return _map_dice(d, _max)

def min_roll(d):
    return _map_dice(d, _min)

def median_roll(d):
    return _map_dice(d, _median)

def _cartesian(*args):
    """returns a generator that iterates over the cartesian product of the lists in *args
    
    Since python 2.6 is out now, this could be replaced with itertools.product
    """
    if len(args) > 1:
        for item in args[0]:
            for rest in _cartesian(*args[1:]):
                yield (item,) + rest
    elif len(args) == 1:
        for item in args[0]:
            yield (item,)

def distribution(dice):
    """returns the frequency distribution of the roll"""
    if type(dice) == str:
        dice = parse(dice)
    results = {}
    # I always forget this: the * before the list comprehension unpacks it into arguments
    # Inner list comprehension creates a list of ranges for each die, plus the total bonus
    # Outer comprehension sums each cartesian product (every possible combination)
    for roll in (sum(r) for r in _cartesian(*(xrange(_min(d)+dice[1], _max(d)+dice[1]+1) for d in dice[0]))):
        results[roll] = results.get(roll, 0) + 1
    return results

def success_total(dice, target):
    """returns the probability of rolling a total >= target"""
    if type(dice) == str:
        dice = parse(dice)
    dist = distribution(dice)
    successes = sum(dist[roll] for roll in dist if roll >= target)
    total = sum(dist.values())
    return float(successes) / total

def _factorial(x): return (1 if x==0 else x * _factorial(x-1))
def _permutations(n,r): return _factorial(n) / _factorial(n - r)
def _combinations(n,r): return _permutations(n, r) / _factorial(r)
def _unsuccessful_choices(n,z,p):
    """Generator for all unsuccessful outcomes
    
    n options, at least z successes, probability of success p

    Intended for use as, e.g.: 1/3 == 1 - sum(_unsuccessful_choices(1, 1, 1.0/3)
    """
    for r in xrange(0, z):
        yield _combinations(n,r) * p**r * (1-p)**(n-r)

def success(dice, target, n=1):
    """returns the probability of rolling >= target n times

    This isn't terribly meaningful if rolling more than one type of die, or if
    rolling negative dice; it's intended for scenarios like the Storyteller system,
    where you roll large piles of d10s, trying to beat a number.

    (In all honesty, I've always been awkward at probabilities; there may be a
    better way to work this out.)

    http://www.boardgamegeek.com/thread/255452
    """
    if type(dice) == str:
        dice = parse(dice)
    target = target - dice[1]
    p = []
    for die in dice[0]:
        # Probability that this die will roll a success:
        if target > _max(die):
            p.append(0)
        elif target <= _min(die):
            p.append(1)
        else:
            p.append(1 - (target-1)/float(die))
    # Average probability of a success being rolled across all die-types
    p_success = float(sum(p))/len(p)
    return 1 - sum(_unsuccessful_choices(len(p), n, p_success))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        rolls = sys.argv[1:]
        for dice in rolls:
            print "Rolling %s: %d" % (dice, roll(dice))
            print "Max: %d" % max_roll(dice)
            print "Min: %d" % min_roll(dice)
            print "Median: %d" % median_roll(dice)
            """print "Distribution:"
            dist = distribution(dice)
            for result in dist:
                print result, dist[result]
            """
