#!/usr/bin/env python3
#
# Usage: advent_2017.py [CHALLENGE_NUM]
# Solutions to programming challenges from http://adventofcode.com/
# If no arguments are passed, it will try to solve all challenges.

from collections import Counter, namedtuple, defaultdict
from copy import copy, deepcopy
from enum import Enum
from functools import reduce
import hashlib
from inspect import signature
from itertools import *
import json
from math import *
import numpy as np
import operator as op
import re
import sys
from time import sleep, time
from tqdm import tqdm

from util import *


FILENAME_TEMPLATE = 'data_2017/{}.data'


###
##  PROBLEMS
#

def p_1(data):
    def get_sum(digits, d):
        shifted = digits[d:] + digits[:d]
        pairs = zip(digits, shifted)
        return sum(a for a, b in pairs if a == b)

    digits = [int(digit) for digit in data[0]]
    half_index = int(len(digits) / 2)
    return get_sum(digits, 1), get_sum(digits, half_index)


def p_2(data):
    def get_division(ints):
        for a, b in combinations(ints, 2):
            if not a % b:
                return a / b
            elif not b % a:
                return b / a

    lines_of_ints = [[int(a) for a in line.split()] for line in data]
    deltas = (max(ints) - min(ints) for ints in lines_of_ints)
    divisions = (int(get_division(ints)) for ints in lines_of_ints)
    return sum(deltas), sum(divisions)


def p_3(data):
    HEADS = list(product([-1, 0, 1], [-1, 0, 1]))
    HEADS.remove((0, 0))
    LEFT_TURN = {(1, 0): (0, 1), (0, 1): (-1, 0), (-1, 0): (0, -1),
                 (0, -1): (1, 0)}

    def get_manhattan(square_i):
        for i, loc in enumerate(pos_generator(), 1):
            if i == square_i:
                return abs(loc[0]) + abs(loc[1])

    def get_first_larger(threshold):
        mem = defaultdict(int)
        mem[(0, 0)] = 1
        gen = pos_generator()
        next(gen)
        for loc in gen:
            val = sum(mem[n] for n in get_neighbours(loc))
            if val > threshold:
                return val
            mem[loc] = val

    def get_neighbours(loc):
        return [move(loc, head) for head in HEADS]

    def pos_generator():
        loc, head = (0, 0), (1, 0)
        yield loc
        for i in count(1):
            for _ in range(2):
                for j in range(i):
                    loc = move(loc, head)
                    yield loc
                head = LEFT_TURN[head]

    def move(loc, head):
        return tuple(a + b for a, b in zip(loc, head))

    square_i = int(data[0])
    return get_manhattan(square_i), get_first_larger(square_i)


def p_4(data):
    def get_sum(phrases, checker):
        return sum(1 for phrase in phrases if checker(phrase))

    def has_no_dups(words):
        return len(words) == len(set(words))

    def has_no_anagrams(words):
        letter_counters = [frozenset(Counter(word).items()) for word in words]
        return has_no_dups(letter_counters)

    phrases = [line.split() for line in data]
    return get_sum(phrases, has_no_dups), get_sum(phrases, has_no_anagrams)


# def p_5(data):
#     def run(mem, strange=False):
#         pc = 0
#         for i in count():
#             if pc < 0 or pc >= len_mem:
#                 return i
#             val = mem[pc]
#             if strange:
#                 mem[pc], pc = val + (-1 if val > 2 else 1), pc + val
#             else:
#                 mem[pc], pc = val + 1, pc + val
#
#     mem = [int(line) for line in data]
#     len_mem = len(mem)
#     return run(mem.copy()), run(mem.copy(), strange=True)


def p_6(data):
    def step(banks, states, i):
        max_i = i_of_max(banks)
        blocks = banks[max_i]
        banks[max_i] = 0
        i_stream = get_i_stream(banks, max_i)
        next(i_stream)
        for _ in range(blocks):
            banks[next(i_stream)] += 1
        if tuple(banks) in states:
            return i, i - states[tuple(banks)]
        states[tuple(banks)] = i

    def i_of_max(banks):
        return banks.index(max(banks))

    def get_i_stream(banks, i):
        return cycle(chain(range(i, len(banks)), range(0, i)))

    banks = [int(a) for a in data[0].split()]
    states = {}
    for i in count(1):
        out = step(banks, states, i)
        if out:
            return out


def p_7(data):
    def get_weight(weights, relations, node, tower_weights, solution):
        if node not in relations:
            return weights[node]
        children = relations[node]
        children_weights = \
            [get_weight(weights, relations, child, tower_weights, solution)
             for child in children]
        if solution:
            return
        if not len(set(children_weights)) == 1:
            sol = find_solution(weights, zip(children, children_weights))
            solution.append(sol)
        children_weight = sum(children_weights)
        tower_weights[node] += children_weight
        return tower_weights[node]

    def find_solution(weights, children):
        children = list(children)
        children_weights = [child[1] for child in children]
        wrong_weight = [weight for weight in children_weights
                        if children_weights.count(weight) == 1][0]
        right_weights = set(children_weights).difference({wrong_weight})
        right_weight = next(iter(right_weights))
        faulty_child = [child for child in children
                        if child[1] == wrong_weight][0]
        delta = right_weight - wrong_weight
        return weights[faulty_child[0]] + delta

    nodes = [line.replace(',', '').split() for line in data]
    non_leafs = (node for node in nodes if len(node) > 2)
    relations = {node[0]: node[3:] for node in non_leafs}
    children = (c for ccc in relations.values() for c in ccc)
    s = set(relations.keys()).difference(set(children))
    root = next(iter(s))
    weights = {node[0]: int(node[1].replace('(', '').replace(')', ''))
               for node in nodes}
    tower_weights = weights.copy()
    solution = []
    get_weight(weights, relations, root, tower_weights, solution)
    return root, solution[0]


def p_8(data):
    C = namedtuple('C', ['reg_e', 'op_e', 'val_e', 'reg_c', 'op_c', 'val_c'])
    OPS_COND = {'==': op.eq, '!=': op.ne, '>': op.gt, '<': op.lt, '>=': op.ge,
                '<=': op.le}
    OPS_EXEC = {'inc': op.add, 'dec': op.sub}

    def get_command(txt):
        tokens = txt.split()
        tokens.pop(3)
        return C(*tokens)

    def evaluate(regs, c):
        return OPS_COND[c.op_c](regs[c.reg_c], int(c.val_c))

    def execute(regs, c):
        new_val = OPS_EXEC[c.op_e](regs[c.reg_e], int(c.val_e))
        regs[c.reg_e] = new_val
        return new_val

    commands = (get_command(line) for line in data)
    regs = defaultdict(int)
    reg_updates = [execute(regs, command) for command in commands
                   if evaluate(regs, command)]
    return max(regs.values()), max(reg_updates)


def p_9(data):
    def process_ch(s, ch):
        if s.in_garbage:
            process_garbage(s, ch)
        elif ch == '<':
            s.in_garbage = True
        elif ch == '{':
            s.depth += 1
            s.score += s.depth
        elif ch == '}':
            s.depth -= 1

    def process_garbage(s, ch):
        if ch == '!':
            next(s.stream)
        elif ch == '>':
            s.in_garbage = False
        else:
            s.garbage_len += 1

    VARS = {'depth': 0, 'score': 0, 'garbage_len': 0, 'in_garbage': False,
            'stream': iter(data[0])}
    State = type('State', (), VARS)
    s = State()
    for ch in s.stream:
        process_ch(s, ch)
    return s.score, s.garbage_len


def p_10(data):
    def twist(a_list, pc, length):
        a_iter = islice(cycle(a_list), pc, None)
        sub_list = reversed(list(islice(a_iter, length)))
        out = a_list.copy()
        for i, el in enumerate(sub_list):
            j = i + pc
            if j >= len(a_list):
                j -= len(a_list)
            out[j] = el
        return out

    lengths = [int(a) for a in data[0].split(',')]
    a_list = list(range(256))
    a_iter = cycle(range(256))
    pc = next(a_iter)
    for skip, length in enumerate(lengths):
        a_list = twist(a_list, pc, length)
        a_iter = islice(a_iter, length + skip - 1, None)
        pc = next(a_iter)
    return a_list[0] * a_list[1]


def p_11(data):
    S = Enum('S', 'n ne se s sw nw')
    DELTA = {0: {S.n: P(0, -1), S.ne: P(1, -1), S.se: P(1, 0), S.s: P(0, 1),
                 S.sw: P(-1, 0), S.nw: P(-1, -1)},
             1: {S.n: P(0, -1), S.ne: P(1, 0), S.se: P(1, 1), S.s: P(0, 1),
                 S.sw: P(-1, 1), S.nw: P(-1, 0)}}

    def get_path():
        return [S[a] for a in data[0].split(',')]

    def hex_distance(a, b):
        return (abs(a.x - b.x)
                + abs(a.x + a.y - b.x - b.y)
                + abs(a.y - b.y)) / 2

    path = get_path()
    p = P(0, 0)
    for direction in path:
        p = P(*[sum(a) for a in zip(p, DELTA[p.x % 2][direction])])
    return hex_distance(P(0, 0), p)


# def p_12(data):
#     def get_item(line):
#         head, *tail = [int(token) for token in re.findall('\d+', line)]
#         return head, tail
#
#     def get_connected(edges, origin, result):
#         connections = edges[origin]
#         if result.issuperset(connections):
#             return
#         result.update(connections)
#         for connection in connections:
#             get_connected(edges, connection, result)
#
#     def get_groups(edges):
#         out = set()
#         for edge in edges:
#             group = set()
#             get_connected(edges, edge, group)
#             out.add(frozenset(group))
#         return out
#
#     edges = dict([get_item(line) for line in data])
#     for line in data:
#         origin, neighbours = parse_line(line)
#         edges[origin] = neighbours
#     connected = set()
#     get_connected(edges, 0, connected)
#     return len(connected), len(get_groups(edges))


# def p_15(data):
#     def get_start(i):
#         return int(re.search('\d+', data[i]).group())
#
#     def gen(factor, starting_value, mul_filter=1):
#         while True:
#             starting_value = (starting_value * factor) % 2147483647
#             if starting_value % mul_filter == 0:
#                 yield starting_value
#
#     def get_no_matches(gen_a, gen_b, steps):
#         a_sum = 0
#         for i in range(int(steps/100)):
#             a_sum += get_bin(gen_a) == get_bin(gen_b)
#         return a_sum
#
#     def get_bin(gen):
#         return f'{next(gen):0>16b}'[-16:]
#
#     par_a = 16807, get_start(0)
#     par_b = 48271, get_start(1)
#     sum_a = get_no_matches(gen(*par_a), gen(*par_b), 4 * 10 ** 7)
#     sum_b = get_no_matches(gen(*par_a, 4), gen(*par_b, 8), 5 * 10 ** 6)
#     return sum_a, sum_b


def p_16(data):
    def get_commands():
        out = []
        commands = data[0].split(',')
        for command in commands:
            operator = command[0]
            operands = command[1:].split('/')
            operands = [int(a) if a.isnumeric() else a for a in operands]
            out.append((operator, operands))
        return out

    def get_reg():
        return [f'{a:c}' for a in range(97, 113)]

    def dance(reg, commands):
        for command in commands:
            operator = command[0]
            operands = command[1]
            OPERATORS[operator](reg, *operands)

    def move_group(reg, size):
        tmp = reg[-size:] + reg[:-size]
        reg.clear()
        reg.extend(tmp)

    def switch_index(reg, i_a, i_b):
        reg[i_a], reg[i_b] = reg[i_b], reg[i_a]

    def switch_el(reg, e_a, e_b):
        i_a, i_b = reg.index(e_a), reg.index(e_b)
        switch_index(reg, i_a, i_b)

    OPERATORS = {'s': move_group,
                 'x': switch_index,
                 'p': switch_el}

    commands = get_commands()
    reg_1 = get_reg()
    dance(reg_1, commands)
    reg_2 = get_reg()
    ITERATIONS = 10 ** 9
    seen = []
    for i in range(ITERATIONS):
        s = ''.join(reg_2)
        if s in seen:
            return ''.join(reg_1), seen[ITERATIONS % i]
        seen.append(s)
        dance(reg_2, commands)


# def p_17(data):
#     class Node:
#         def __init__(self, val, next_node=None):
#             self.val = val
#             self.next_node = next_node
#
#     def get_buffer(size):
#         node = Node(0)
#         node.next_node = node
#         for i in tqdm(range(1, size)):
#             for _ in range(steps):
#                 node = node.next_node
#             next_node = node.next_node
#             new_node = Node(i, next_node)
#             node.next_node = new_node
#             node = new_node
#         return node
#
#     steps = int(data[0])
#     out_1 = get_buffer(2018).next_node.val
#     node_2 = get_buffer(5 * 10 ** 7)
#     while node_2.val != 0:
#         node_2 = node_2.next_node
#     out_2 = node_2.next_node.val
#     return out_1, out_2


def p_18(data):
    def problem_1(code):
        prg = Program(code)
        while True:
            res_1 = prg.step()
            if res_1:
                return res_1

    def problem_2(code):
        prg_1 = Program(code, 0)
        prg_2 = Program(code, 1)
        prg_1.other = prg_2
        prg_2.other = prg_1
        while True:
            o_1 = prg_1.step()
            o_2 = prg_2.step()
            if o_1 in ['HALT', 'SUS'] and o_2 in ['HALT', 'SUS']:
                return prg_1.sends

    class Program:
        def __init__(s, code, a_id=None):
            s.code = code
            s.pc = 0
            s.regs = defaultdict(int)
            s.OPERATIONS = {'snd': lambda x: s.snd(x),
                            'set': lambda x, y: s.set_r(x, y),
                            'add': lambda x, y: s.opr(x, y, op.add),
                            'mul': lambda x, y: s.opr(x, y, op.mul),
                            'mod': lambda x, y: s.opr(x, y, op.mod),
                            'rcv': lambda x: s.rcv(x),
                            'jgz': lambda x, y: s.get(y) if s.get(
                                x) > 0 else None}
            if a_id is not None:
                s.regs['p'] = a_id
                s.sends = 0
                s.queue = []
                s.other = None

        def get(s, x):
            try:
                return int(x)
            except ValueError:
                return s.regs[x]

        def snd(s, x):
            if hasattr(s, 'sends'):
                s.other.queue.insert(0, s.get(x))
                # If we are counting sends and not receives:
                # s.other.sends += 1
            else:
                s.regs['snd'] = s.get(x)

        def rcv(s, x):
            if hasattr(s, 'sends'):
                if not s.queue:
                    return 'SUS'
                s.regs[x] = s.queue.pop()
                s.other.sends += 1
            else:
                return [s.regs['snd']] if s.get(x) != 0 else None

        def set_r(s, x, y):
            s.regs[x] = s.get(y)

        def opr(s, x, y, operator):
            s.regs[x] = operator(s.regs[x], s.get(y))

        def step(s):
            if s.pc < 0 or s.pc >= len(s.code):
                return 'HALT'
            command = s.code[s.pc]
            operation = command[0]
            operators = command[1:]
            res = s.OPERATIONS[operation](*operators)
            if res == 'SUS':
                return 'SUS'
            if type(res) is list:
                return res[0]
            if res is not None:
                s.pc += res
            else:
                s.pc += 1

    code = [(a.strip().split()) for a in data]
    return problem_1(code), problem_2(code)


def p_19(data):
    class S:
        """State"""
        def __init__(s, y, x, d=None):
            s.y, s.x, s.d = y, x, d

        def __repr__(s):
            return f'{s.__dict__}'

        def move(s, d=None):
            M = {D.e: S(0, 1), D.s: S(1, 0), D.w: S(0, -1), D.n: S(-1, 0)}
            if not d:
                d = s.d
            y, x = s.y + M[d].y, s.x + M[d].x
            return S(y, x, d)

    def walk(dia, s, counter=None):
        while True:
            ch = get_ch(dia, s)
            if ch == ' ':
                return
            if counter:
                counter[0] += 1
            if ch not in list('|-+ '):
                yield ch
            if ch == '+':
                s.d = get_new_dir(dia, s)
            s = s.move()

    def get_ch(dia, s):
        try:
            return dia[s.y][s.x]
        except IndexError:
            print(s)
            sys.exit()

    def get_new_dir(dia, s):
        if s.d in [D.w, D.e]:
            up_is_empty = get_ch(dia, s.move(D.n)) == ' '
            return D.s if up_is_empty else D.n
        else:
            left_is_empty = get_ch(dia, s.move(D.w)) == ' '
            return D.e if left_is_empty else D.w

    starting_state = S(0, data[0].index('|'), D.s)
    counter = [0]
    out = list(walk(data, starting_state, counter))
    return ''.join(out), counter[0]


def p_20(data):
    V = namedtuple('V', 'x y z')
    P = namedtuple('P', 'i p v a')

    def get_particle(i, line):
        tokens = re.findall('<(.*?)>', line)
        vectors = map(get_vector, tokens)
        return P(i, *vectors)

    def get_vector(token):
        scalars = map(int, token.split(','))
        return V(*scalars)

    def manhattan(vector):
        absolute_scalars = map(abs, vector)
        return sum(absolute_scalars)

    def simulate(particles):
        for _ in range(100):
            particles = remove_collisions(particles)
            particles = [move(a) for a in particles]
        return len(particles)

    def remove_collisions(particles):
        collision_counter = Counter([a.p for a in particles])
        collision_points = [k for k, v in collision_counter.items() if v > 1]
        if collision_points:
            print('COLLISION!')
            return [a for a in particles if a.p not in collision_points]
        else:
            return particles

    def move(par):
        v = V(*[sum(a) for a in zip(par.v, par.a)])
        p = V(*[sum(a) for a in zip(par.p, par.v)])
        return P(par.i, p, v, par.a)

    particles = [get_particle(i, a) for i, a in enumerate(data)]
    particles.sort(key=lambda p: (manhattan(p.a), manhattan(p.v),
                                  manhattan(p.p)))
    return particles[0].i, simulate(particles)


# def p_21(data):
#     STARTING_POSITION = '.#./..#/###'
#     Condition = namedtuple('Condition', 'cen on off')

#     def get_rules():
#         out = {}
#         for line in data:
#             condition, consequence = line.split(' => ')
#             condition = get_condition(condition)
#             out[condition] = consequence
#         return out

#     def step(board, rules):
#         factor = 3 if len(board[0]) % 3 == 0 else 2
#         subboards = split(board, factor)
#         subboards = [[expand(subboard, rules) for subboard in subboard_row]
#                      for subboard_row in subboards]
#         return merge(subboards)

#     def split(board, factor):
#         n = factor
#         if len(board) == 3:
#             return [[board]]
#         out = []
#         for i in range(0, len(board), n):
#             rows = board[i:i + n]
#             subboard_rows = []
#             for j in range(0, len(board), n):
#                 subboard = [row[j:j + n] for row in rows]
#                 subboard_rows.append(subboard)
#             out.append(subboard_rows)
#         return out

#     def expand(board, rules):
#         txt_board = get_txt(board)
#         condition = get_condition(txt_board)
#         out_txt = rules[condition]
#         return get_board(out_txt)

#     def merge(subboards):
#         out = []
#         for horizontal in subboards:
#             for i in range(len(horizontal[0])):
#                 line = []
#                 for subboard in horizontal:
#                     line += subboard[i]
#                 out.append(line)
#         return out

#     # UTIL
#     def get_condition(token):
#         if len(token) == 5:
#             counter = Counter(token.replace('/', ''))
#             return Condition(None, counter['#'], counter['.'])
#         token = list(token.replace('/', ''))
#         center = token.pop(4)
#         counter = Counter(token)
#         return Condition(center, counter['#'], counter['.'])

#     def get_board(txt):
#         return [list(line) for line in txt.split('/')]

#     def get_txt(board):
#         lines = [''.join(line) for line in board]
#         return '/'.join(lines)

#     def get_printable(board):
#         return '\n'.join([''.join(line) for line in board])

#     rules = get_rules()
#     board = get_board(STARTING_POSITION)
#     for i in range(2):
#         board = step(board, rules)
#     return get_printable(board)


# def p_23(data):
#     Op = Enum('Op', 'set sub mul jnz')
#     Co = namedtuple('Co', 'o x y')
#
#     class Comp:
#         def __init__(s, code):
#             s.code = code
#             s.reg = defaultdict(int)
#             s.pc = 0
#             s.count = 0
#             s.max_pc = 0
#
#         def step(s):
#             if s.pc > s.max_pc:
#                 s.max_pc = s.pc
#             if s.pc < 0 or s.pc > len(s.code):
#                 return 'HALT'
#             o, x, y = s.code[s.pc]  # if not: y = ?[y]
#             if type(y) != int:
#                 y = s.reg[y]
#             if o == Op.jnz:
#                 if x != 0:
#                     s.pc += y
#                 return
#             if o == Op.set:
#                 s.reg[x] = y
#             elif o == Op.sub:
#                 s.reg[x] -= y
#             elif o == Op.mul:
#                 s.reg[x] *= y
#                 s.count += 1
#             s.pc += 1
#
#     def get_code():
#         return [parse_line(a) for a in data]
#
#     def parse_line(line):
#         c, x, y = line.split()
#         try:
#             y = int(y)
#         except ValueError:
#             pass
#         return Co(Op[c], x, y)
#
#     c = Comp(get_code())
#     while c.step() != 'HALT':
#         pass
#     return c.count


# def p_24(data):
#     def get_max(pin, components):
#         for comp in components:
#             if pin not in comp:
#                 continue
#             other_pin = comp[not comp.index(pin)]
#             remaining = deepcopy(components)
#             remaining.remove(comp)
#             paths = [*get_max(other_pin, remaining)]
#             yield sum(comp) + max(paths)
#         yield 0
#
#     components = [[int(a) for a in line.split('/')] for line in data]
#     return max(get_max(0, components))


# def p_25(data):
#     class Bit:
#         def __init__(s):
#             s.i = 0
#             s.neighbours = {}
#
#         def get(s, side):
#             if side in s.neighbours:
#                 return s.neighbours[side]
#             new_bit = Bit()
#             s.neighbours[side] = new_bit
#             other_side = R.l if side == R.r else R.r
#             new_bit.neighbours[other_side] = s
#             return new_bit
#
#     class State:
#         def __init__(s):
#             s.mappings = {}
#
#     def init_states(lines):
#         states = defaultdict(State)
#         starting_state_id = get_state_id(lines[0])
#         no_of_steps = get_value(lines[1])
#         state_lines = []
#         for line in lines[3:]:
#             if not line:
#                 parse_state(state_lines, states)
#                 state_lines = []
#                 continue
#             state_lines.append(line)
#         parse_state(state_lines, states)
#         return states[starting_state_id], states, no_of_steps
#
#     def get_state_id(line):
#         return re.search('(\S+).$', line).group(1)
#
#     def get_value(line):
#         return int(re.search('\d+', line).group())
#
#     def parse_state(lines, states):
#         state = State()
#         a_id = get_state_id(lines[0])
#         states[a_id] = state
#         value, mapping = get_mapping(lines[1:5], states)
#         state.mappings[value] = mapping
#         value, mapping = get_mapping(lines[5:9], states)
#         state.mappings[value] = mapping
#
#     def get_mapping(lines):
#         value = get_value(lines[0])
#         new_value = get_value(lines[1])
#         side = get_side(lines[2])
#         state_id = get_state_id(lines[3])
#         return value, (new_value, side, state_id)
#
#     def get_side(line):
#         side_name = get_state_id(line)
#         return R.l if side_name == 'left' else R.r
#
#     def step(bit, state):
#         value, side, state_id = state.mappings[bit.value]
#         bit.value = value
#         bit = bit.get(side)
#         return bit, state_id
#
#     def checksum(bit):
#         while R.l in bit.neighbours:
#             bit = bit.get(R.l)
#         out = bit.value
#         while R.r in bit.neighbours:
#             bit = bit.get(R.r)
#             out += bit.value
#         return out
#
#     bit = Bit()
#     state, states, no_of_steps = init_states(data)
#     for _ in tqdm(range(no_of_steps)):
#         bit, state_id = step(bit, state)
#         state = states[state_id]
#     return checksum(bit)





###
##  UTIL
#

def main():
    script_name = sys.argv[0]
    arguments   = sys.argv[1:]
    if len(sys.argv) == 1:
        run_all()
    else:
        fun_name = sys.argv[1]
        fun = globals()[fun_name]
        print(run(fun, FILENAME_TEMPLATE))


def run_all():
    functions = (v for k, v in globals().items()
                 if callable(v) and k.startswith('p_'))
    for fun in functions:
        run_single(fun)


def run_single(fun):
    print(f'{fun.__name__}:')
    start_time = time()
    print(f'Result:   {run(fun, FILENAME_TEMPLATE)}')
    duration = time() - start_time
    print(f'Duration: {duration:.3f}s\n')


if __name__ == '__main__':
    main()
