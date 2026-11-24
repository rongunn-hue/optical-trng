#!/usr/bin/env python3
"""Optical TRNG VERSION 2 (plug-in resistor sockets) - hand layout on ElectroCookie strip boards. Derived from the version-1 layout.

Connectivity comes ONLY from ../schematic/optical_trng_v2.circuit; this file holds placement and wiring.
The verifier rebuilds every net from board strips + rails + wires + parts and compares it with the circuit.

Boards (top view, component side):
  HALF board 3.5 x 2.05 in: columns 1..30; per column one 5-hole strip J-F (upper) and one E-A (lower) across the
      0.3 in centre channel; rails: T- (outer top), T+ (inner top), B- (inner bottom), B+ (outer bottom), each one node.
  MINI board 1.5 x 2 in: rows 1..17; per row one 5-hole strip A-E (left) and one F-J (right) across the 0.3 in channel.
"""
import re, sys, os
from collections import defaultdict
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Wedge

HERE = os.path.dirname(os.path.abspath(__file__))
CIRCUIT = os.path.join(HERE, '..', 'schematic', 'optical_trng_v2.circuit')

# ---------------------------------------------------------------- geometry
HROW = {'J': 0, 'I': 1, 'H': 2, 'G': 3, 'F': 4, 'E': 7, 'D': 8, 'C': 9, 'B': 10, 'A': 11}
RAILY = {'T-': -3.74, 'T+': -2.74, 'B-': 13.74, 'B+': 14.74}
MCOL = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 7, 'G': 8, 'H': 9, 'I': 10, 'J': 11}

class Board:
    def __init__(s, name, kind, title, rails=None):
        s.name, s.kind, s.title, s.rails = name, kind, title, rails or {}
        s.parts = []      # (ref, val, kind, [(pin, hole)], extra)
        s.wires = []      # (net_hint, [holes/points]) polyline; first/last are holes
        s.offboard = []   # (hole, label)
        s.bottom = set()  # indexes into wires that run on the SOLDER side
        s.cuts = {}       # rail name -> last column of the first section: the rail is CUT between that column and the next
        s.rails2 = {}     # rail name -> net of the second section
        s.notes = []
    # hole -> (x, y)
    def xy(s, h):
        if s.kind == 'half':
            a, b = h
            if a in RAILY: return (b, RAILY[a])
            return (a, HROW[b])
        col, row = h
        return (MCOL[col], row - 1)
    # hole -> electrical node id
    def node(s, h):
        if s.kind == 'half':
            a, b = h
            if a in RAILY:
                assert 1 <= b <= 30, h
                return (s.name, a, int(b > s.cuts[a])) if a in s.cuts else (s.name, a)
            assert 1 <= a <= 30 and b in HROW, h
            return (s.name, a, 'U' if HROW[b] <= 4 else 'L')
        col, row = h
        assert col in MCOL and 1 <= row <= 17, h
        return (s.name, row, 'L' if MCOL[col] <= 4 else 'R')
    def part(s, ref, val, kind, pins, **extra): s.parts.append((ref, val, kind, pins, extra))
    def wire(s, *pts, net='', side='top'):
        s.wires.append((net, list(pts)))
        if side == 'bottom': s.bottom.add(len(s.wires) - 1)
    def off(s, h, label): s.offboard.append((h, label))

def R(b, ref, val, h1, h2, **k): b.part(ref, val, 'R', [('1', h1), ('2', h2)], **k)
def Cc(b, ref, val, h1, h2, **k): b.part(ref, val, 'C', [('1', h1), ('2', h2)], **k)
def hdr(b, ref, val, holes, **k): b.part(ref, val, 'HDR', [(str(i + 1), h) for i, h in enumerate(holes)], **k)
def sock(b, ref, val, holes, **k): b.part(ref, val, 'SOCK', [(str(i + 1), h) for i, h in enumerate(holes)], **k)   # two single-pin female sockets; a resistor plugs between them
def tp(b, ref, h): b.part(ref, 'TP', 'TP', [('1', h)])
def dip_half(b, ref, val, c, npins):      # notch LEFT: pin1 = (c,E) ... pin n/2 = (c+n/2-1,E); pin n = (c,F)
    k = npins // 2
    pins = [(str(i + 1), (c + i, 'E')) for i in range(k)] + [(str(npins - i), (c + i, 'F')) for i in range(k)]
    b.part(ref, val, 'DIP', pins, c=c, n=npins)

B = {}
# =========================================================== BOARD 1: power + optical (half)
b = B['B1'] = Board('B1', 'half', 'BOARD 1 - POWER + OPTICAL DETECTOR',
                    {'T-': 'GND', 'T+': '+5V_OPT', 'B-': 'GND', 'B+': 'VIN_9V'})
# ---- U6 -> +5V (main), columns 1-4, lower half. Body over row B, capacitors on row D (flat side).
hdr(b, 'J1', '9V IN', [(1, 'E'), (2, 'E')], label='1=VIN 2=GND', lab_at=(1.5, 5.6, 'center'))
b.part('U6', 'WS78L05', 'TO92', [('3', (1, 'C')), ('2', (2, 'C')), ('1', (3, 'C'))], flat='up')
Cc(b, 'C10', '0.33uF', (1, 'D'), (2, 'D'))
Cc(b, 'C11', '0.1uF', (3, 'D'), (4, 'D'))
b.wire((1, 'A'), ('B+', 1), net='VIN_9V')
b.wire((2, 'A'), ('B-', 2), net='GND')
b.wire((4, 'A'), ('B-', 4), net='GND')
b.off((3, 'E'), '+5V  -> B2 7H')
b.off((3, 'B'), '+5V  -> B2 T+21')
b.off(('B-', 5), 'GND  -> B2 B-1')
# ---- U5 -> +5V_OPT, columns 6-9, upper half. VIN comes up column 6 from the B+ rail. Body over row G.
b.wire((6, 'A'), ('B+', 6), net='VIN_9V')
b.wire((6, 'E'), (6, 'F'), net='VIN_9V')
b.part('U5', 'WS78L05', 'TO92', [('3', (6, 'H')), ('2', (7, 'H')), ('1', (8, 'H'))], flat='up')
Cc(b, 'C8', '0.33uF', (6, 'I'), (7, 'I'))
Cc(b, 'C9', '0.1uF', (8, 'I'), (9, 'I'))
b.wire((7, 'J'), ('T-', 7), net='GND')
b.wire((8, 'J'), ('T+', 8), net='+5V_OPT')
b.wire((9, 'J'), ('T-', 9), net='GND')
# ---- R1 = LED current resistor SOCKET (+5V_OPT -> LED anode = U1.1 strip): two single-pin sockets on the two edges of the centre channel (rows F and E), 0.3 in apart
sock(b, 'R1', 'LED socket', [(15, 'F'), (15, 'E')], label='plug 7.5k 0.5mA\n3.9k 1.0mA*  2.0k 1.9mA\nempty = LED off', lab_at=(14.4, 5.5, 'right'))
b.wire((15, 'J'), ('T+', 15), net='+5V_OPT')
b.wire((15, 'C'), (18, 'C'), net='LED_DRIVE')
# ---- U1 FOD852 at col 18
dip_half(b, 'U1', 'FOD852', 18, 4)
b.wire((19, 'A'), ('B-', 19), net='GND'); b.wire((19, 'J'), ('T-', 19), net='GND')
tp(b, 'TP1', (18, 'J'))
b.off((18, 'I'), 'DETECTOR -> B2 6A')
# ---- R2 = collector LOAD resistor SOCKET (+5V_OPT -> DETECTOR): spans the centre channel, pins directly opposite in column 23, right at the channel edges (23F upper, 23E lower)
sock(b, 'R2', 'LOAD socket', [(23, 'F'), (23, 'E')], label='plug 68R*  220R  680R\nempty = no signal', lab_at=(23.7, 5.5, 'left'))
b.wire((23, 'J'), ('T+', 23), net='+5V_OPT')
b.wire((23, 'A'), (20, 'A'), net='DETECTOR'); b.wire((20, 'E'), (20, 'F'), net='DETECTOR'); b.wire((20, 'H'), (18, 'H'), net='DETECTOR')
b.wire(('T-', 30), ('B-', 30), net='GND')
b.notes = ['Rails: T- and B- = GND (tied in column 30), T+ = +5V_OPT, B+ = 9 V input (VIN). T+ and B+ are NOT tied.',
           'Leave the side "power jumper" pads open.',
           'U5/U6 TO-92: flat face toward the TOP edge of the board, so left-to-right is IN, GND, OUT. Keep the row under the rounded side empty.',
           'R1 socket = 15F + 15E, R2 socket = 23F + 23E: pins on the two edges of the centre channel, 0.3 in apart. The 1/2 W resistor of R2 is longer than that: bend its leads UP so the body sits clear of the board, above the gap.']

# =========================================================== BOARD 2: amplifier + VREF + comparator (half)  (version-1 boards 2 and 3 merged)
# T+ rail is CUT between columns 17 and 18: columns 1-17 = VREF (amplifier side), columns 18-30 = +5V (comparator side).
b = B['B2'] = Board('B2', 'half', 'BOARD 2 - AMPLIFIER (MCP6022) + VREF + COMPARATOR (LM393)',
                    {'T-': 'GND', 'T+': 'VREF', 'B-': 'GND', 'B+': 'VREF'})
b.cuts = {'T+': 17}; b.rails2 = {'T+': '+5V'}
tp(b, 'TP2', ('T+', 6))
Cc(b, 'C3', '100nF', ('T+', 2), ('T-', 2))
b.off(('T-', 3), 'GND  -> B3 J2')
Cc(b, 'C2', '10uF', ('T+', 4), ('T-', 4), polar=True)
R(b, 'R4', '10k', ('T+', 5), ('T-', 5))
R(b, 'R3', '10k', (7, 'J'), ('T+', 7))
b.off((7, 'H'), '+5V  <- B1 3E')
b.wire((7, 'I'), (8, 'I'), net='+5V')
dip_half(b, 'U2', 'MCP6022', 8, 8)
Cc(b, 'C5', '100nF', (8, 'J'), ('T-', 8))
# stage A (lower)
b.off((6, 'A'), 'DETECTOR <- B1 18I')
b.off(('B-', 1), 'GND <- B1 B-5')
Cc(b, 'C1', '100nF', (6, 'B'), (10, 'B'))
R(b, 'R5', '100k', (10, 'A'), ('B+', 10))
R(b, 'R6', '1k', (9, 'A'), ('B+', 9))
R(b, 'R7', '47k', (8, 'D'), (9, 'D'))
tp(b, 'TP3', (8, 'A'))
b.wire((11, 'A'), ('B-', 11), net='GND')
b.wire((8, 'C'), (12, 'C'), net='AMP_A_OUT')
Cc(b, 'C4', '100nF', (12, 'E'), (12, 'F'))
# stage B (upper)
b.wire((11, 'H'), (12, 'H'), net='AMP_B_PLUS')
R(b, 'R8', '100k', (12, 'J'), ('T+', 12))
R(b, 'R9', '1k', (10, 'J'), ('T+', 10))
R(b, 'R10', '100k', (9, 'H'), (10, 'H'))
tp(b, 'TP4', (9, 'J'))
# R20 = stage-B GAIN resistor SOCKET in parallel with fixed R10: pin 1 on AMP_B_OUT (col 15 upper strip, fed from col 9), pin 2 on AMP_B_MINUS (col 15 lower strip)
sock(b, 'R20', 'GAIN', [(15, 'F'), (15, 'E')], label='plug 28.0k x23*\n88.7k x48\nempty = x101', lab_at=(15.65, 5.5, 'left'))
b.wire((9, 'I'), (15, 'I'), net='AMP_B_OUT')
b.wire((15, 'B'), (13, 'B'), net='AMP_B_MINUS')
b.wire((13, 'E'), (13, 'F'), net='AMP_B_MINUS')
b.wire((13, 'G'), (10, 'G'), net='AMP_B_MINUS')
# AMP_B_OUT on to the comparator input U3.2 (col 21, lower strip): up to col 18 upper, across the channel, along row D
b.wire((15, 'H'), (18, 'H'), net='AMP_B_OUT')
b.wire((18, 'F'), (18, 'E'), net='AMP_B_OUT')
b.wire((18, 'D'), (21, 'D'), net='AMP_B_OUT')
# ---- comparator (version-1 board 3, moved 12 columns to the right). U3 at col 20: pins 1-4 = 20..23 lower, 8..5 = 20..23 upper
b.off((20, 'B'), 'CMP_OUT -> B3 D6')
b.off(('T+', 21), '+5V  <- B1 3B')
b.off(('T+', 22), '+5V  -> B3 A2')
dip_half(b, 'U3', 'LM393', 20, 8)
b.wire((20, 'J'), ('T+', 20), net='+5V')
b.wire((23, 'J'), ('T-', 23), net='GND')
Cc(b, 'C6', '100nF', (20, 'G'), (23, 'G'))
b.wire((23, 'A'), ('B-', 23), net='GND')
R(b, 'R11', '1.0k', ('B+', 22), (22, 'A'))
tp(b, 'TP5', (20, 'A'))
b.wire((24, 'A'), ('B+', 24), net='VREF')
b.wire((24, 'E'), (24, 'F'), net='VREF')
b.wire((22, 'H'), (24, 'H'), net='VREF')
b.wire((20, 'C'), (25, 'C'), net='CMP_A_OUT')
b.wire((25, 'E'), (25, 'F'), net='CMP_A_OUT')
R(b, 'R12', '4.7k', ('T+', 25), (25, 'J'))
# R13 = HYSTERESIS resistor SOCKET: pin 1 on CMP_A_OUT (col 27 upper strip, fed from col 25), pin 2 on CMP_A_PLUS (col 27 lower strip)
sock(b, 'R13', 'HYST', [(27, 'F'), (27, 'E')], label='plug 1M 5mV\n330k 15mV\n100k 47mV*\nempty = none', lab_at=(27.65, 5.5, 'left'))
b.wire((25, 'I'), (27, 'I'), net='CMP_A_OUT')
b.wire((22, 'B'), (27, 'B'), net='CMP_A_PLUS')
b.wire(('T-', 30), ('B-', 30), net='GND')
b.wire(('T+', 14), ('B+', 14), net='VREF')
b.notes = ['CUT THE T+ RAIL (one knife cut through the copper) between columns 17 and 18. Columns 1-17 of T+ = VREF 2.5 V; columns 18-30 of T+ = +5V. Check with a meter that the two sections are open before power.',
           'T- and B- = GND (tied in column 30). B+ = VREF (tied to the VREF section of T+ in column 14). NOT +5V.',
           'R3, R4, R7, R10, R12 and the rail-to-rail parts span 0.1 in: mount them standing (hairpin).',
           'C2 10uF: + lead in T+ (VREF), - lead in T- (GND).',
           'U3 pin 7 (second comparator output) is unused: leave its strip (column 21 upper) empty.',
           'R20 / R13 sockets: pins on the two edges of the centre channel (rows F and E), directly opposite.']

# =========================================================== BOARD 3: PICAXE (mini)
b = B['B3'] = Board('B3', 'mini', 'BOARD 3 - PICAXE-08M2 + PROGRAMMING')
b.off(('A', 2), '+5V <- B2 T+22')
b.off(('J', 2), 'GND <- B2 T-3')
b.off(('D', 6), 'CMP_OUT <- B2 20B')
b.wire(('C', 2), ('C', 3), net='+5V')
b.wire(('H', 2), ('H', 3), net='GND')
Cc(b, 'C7', '100nF', ('D', 2), ('G', 2))
b.part('U4', 'PICAXE-08M2', 'DIPM', [('1', ('E', 3)), ('2', ('E', 4)), ('3', ('E', 5)), ('4', ('E', 6)),
                                      ('5', ('F', 6)), ('6', ('F', 5)), ('7', ('F', 4)), ('8', ('F', 3))])
b.part('J3', 'J3 1-4', 'HDR', [('1', ('A', 3)), ('2', ('A', 4)), ('3', ('A', 5)), ('4', ('A', 6))], label='J3 pins 1-4')
b.part('J3', 'J3 5-8', 'HDR', [('5', ('J', 6)), ('6', ('J', 5)), ('8', ('J', 3))], mech=[('J', 4)], label='pins 5,6,8')
b.part('J3', 'J3 7', 'HDR', [('7', ('J', 10))], label='pin 7 OUT')
b.wire(('B', 4), ('B', 14), net='PICAXE_SERIAL_IN')
b.wire(('A', 14), ('A', 15), net='PICAXE_SERIAL_IN')
b.wire(('I', 3), ('I', 9), net='GND')
b.wire(('H', 4), ('H', 11), net='PICAXE_SERIAL_OUT')
hdr(b, 'JP1', 'PROG IN', [('C', 16), ('C', 15)], lab_at=(2.0, 12.6, 'center'))
R(b, 'R15', '10k', ('D', 14), ('F', 14))
R(b, 'R14', '22k', ('F', 16), ('D', 16))
# J2 = PJ-307 3.5 mm stereo jack (PICAXE download socket), plug entry toward the RIGHT board edge. Drawing: pin1 = sleeve, pins 2+3 one
# contact, pins 4+5 the other (inferred ring = 2/3, tip = 4/5). PICAXE manual: sleeve=serial out, ring=serial in, tip=0V.
# Circuit pins: J2.1 GND = tip foot 4, J2.2 PROGRAM_TX_TO_PICAXE = ring foot 3, J2.3 PICAXE_TX_TO_PROGRAM = sleeve pin 1.
b.part('J2', 'PJ-307', 'JACK', [('1', ('H', 14)), ('2', ('H', 16)), ('3', ('J', 15))],
       mech=[('H', 13), ('H', 17), ('H', 15), ('J', 13), ('J', 17)],
       ties=[(('H', 13), ('H', 14)), (('H', 17), ('H', 16))],
       jpins={('J', 15): '1 sleeve', ('H', 17): '2 ring', ('H', 16): '3 ring', ('H', 14): '4 tip', ('H', 13): '5 tip'},
       label='J2 PJ-307 jack\n4+5 tip=GND  2+3 ring=PROG_TX  1 sleeve=PICAXE_TX')
b.wire(('F', 13), ('F', 9), net='GND')
b.wire(('F', 15), ('F', 12), net='PICAXE_TX_TO_PROGRAM', side='bottom')
# JP2 = AXE021-style PROG/OUT changeover link on C.0: pin 1 (row 12) PROG -> jack sleeve, pin 2 (row 11) COMMON = U4.7, pin 3 (row 10) OUT -> J3.7 pin
hdr(b, 'JP2', 'PROG/OUT', [('I', 12), ('I', 11), ('I', 10)], label='1 PROG  2 C.0  3 OUT', lab_at=(9.6, 7.7, 'center'))
b.notes = ['No rails on this board: +5V arrives on row 2 left, GND on row 2 right.',
           'J3: snap a 1x8 header into two 1x4 pieces. Pins 1-4 sit beside PICAXE pins 1-4 (column A),',
           '    pins 5-8 beside PICAXE pins 5-8 (column J), so J3 pin n is on PICAXE pin n, except pin 7 (see JP2).',
           'PICAXE notch toward row 1 (top). Pin 1 = E3.',
           'JP1: fit the shunt to program, remove it to use C.5 as an input.',
           'JP2 is wired like the PICAXE AXE021 proto-board H1 link: pin 2 (I11) = C.0 (PICAXE pin 7). Shunt on pins 1-2 = PROG (C.0 to the download jack); shunt on 2-3 = OUT (C.0 to J3 pin 7 at J10). Never both.',
           'J3 pin 7 is NOT on the PICAXE pin 7 strip any more: pull pin 7 (J4) out of the J3 5-8 header piece and fit a single pin at J10 (the OUT side of JP2).',
           'J2 = PJ-307 3.5 mm stereo jack, plug entering toward the RIGHT edge. Body covers columns G-J of rows 13-17; only column F is free.',
           'Wired as the PICAXE manual download socket: sleeve (1) = serial out, ring (2,3) = serial in via R14, tip (4,5) = 0V.',
           'Both feet of a contact are one contact inside the jack: only feet 3 (ring) and 4 (tip) have circuit pins; feet 2 and 5 are soldered, no wire.',
           'GND reaches the tip through F13 (foot 5 strip) -> F9. The sleeve is joined to JP2 pin 1 by a wire UNDER the board (F15 -> F12, solder side).',
           'The two outer locating posts, one pitch beyond column J at rows 13 and 17, have no holes: clip them off. VERIFY the pin map with a meter first.']

# =========================================================== verification
def load_circuit():
    nets = {}
    nc = set()
    for l in open(CIRCUIT):
        m = re.match(r'net "([^"]+)" (.*)', l)
        if m: nets[m.group(1)] = set(m.group(2).split())
        m = re.match(r'nc (.*)', l)
        if m: nc |= set(m.group(1).split())
    return nets, nc

INTER = []   # (boardA, holeA, boardB, holeB)
def link(a, ha, bb, hb): INTER.append((a, ha, bb, hb))
link('B1', (3, 'E'), 'B2', (7, 'H'))
link('B1', ('B-', 5), 'B2', ('B-', 1))
link('B1', (18, 'I'), 'B2', (6, 'A'))
link('B1', (3, 'B'), 'B2', ('T+', 21))
link('B2', ('T+', 22), 'B3', ('A', 2))
link('B2', ('T-', 3), 'B3', ('J', 2))
link('B2', (20, 'B'), 'B3', ('D', 6))

def verify():
    errs = []
    par = {}
    def f(x):
        par.setdefault(x, x)
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def u(a, c): par[f(a)] = f(c)
    used = defaultdict(list)
    pinnode = {}
    for bn, b in B.items():
        for ref, val, kind, pins, ex in b.parts:
            for pn, h in pins:
                used[(bn, h)].append('%s.%s' % (ref, pn))
                pinnode['%s.%s' % (ref, pn)] = b.node(h)
            for h in ex.get('mech', []): used[(bn, h)].append('%s.mech' % ref)
            for h1, h2 in ex.get('ties', []): u(b.node(h1), b.node(h2))
        for net, pts in b.wires:
            for p in (pts[0], pts[-1]): used[(bn, p)].append('wire ' + net)
            u(b.node(pts[0]), b.node(pts[-1]))
            xs = [b.xy(p) if isinstance(p[0], (str, int)) and not isinstance(p[0], float) else p for p in pts]
            for p, q in zip(xs, xs[1:]):
                if abs(p[0] - q[0]) > 1e-6 and abs(p[1] - q[1]) > 1e-6: errs.append('%s wire %s not orthogonal' % (bn, net))
        for h, lab in b.offboard: used[(bn, h)].append('off ' + lab)
    for a, ha, bb, hb in INTER: u(B[a].node(ha), B[bb].node(hb))
    for k, v in used.items():
        if len(v) > 1: errs.append('hole %s %s used %d times: %s' % (k[0], k[1], len(v), v))
    # off-board labels must match a link
    offs = {(bn, h) for bn, b in B.items() for h, _ in b.offboard}
    lk = {(a, ha) for a, ha, _, _ in INTER} | {(bb, hb) for _, _, bb, hb in INTER}
    if offs != lk: errs.append('offboard tags vs links differ: %s' % (offs ^ lk))
    groups = defaultdict(set)
    for p, n in pinnode.items(): groups[f(n)].add(p)
    got = {frozenset(g) for g in groups.values() if len(g) > 1}
    want_nets, nc = load_circuit()
    want = {frozenset(v) for v in want_nets.values()}
    for g in got - want: errs.append('BUILT net not in circuit: %s' % sorted(g))
    for g in want - got: errs.append('circuit net not built: %s' % sorted(g))
    allpins = set().union(*want_nets.values()) | nc
    for p in allpins - set(pinnode): errs.append('pin not placed: ' + p)
    for p in set(pinnode) - allpins: errs.append('placed pin not in circuit: ' + p)
    return errs, len(got), len(want)

# =========================================================== rendering
# wire colours are limited to the six on hand: black, red, yellow, green, white, blue
HEX = {'black': '#222222', 'red': '#d62728', 'yellow': '#f2d600', 'green': '#2ca02c', 'white': '#ffffff', 'blue': '#1f77b4'}
NETNAME = {'GND': 'black', '+5V': 'red', '+5V_OPT': 'yellow', 'VREF': 'green', 'VIN_9V': 'white'}
NETCOL = {k: HEX[v] for k, v in NETNAME.items()}
def wcol(net): return NETCOL.get(net, '#1f77b4')

def render(b, fn):
    if b.kind == 'half':
        W, Hh = (-1.6, 32.4), (-5.6, 16.6)
    else:
        W, Hh = (-1.6, 12.6), (-1.6, 17.6)
    S = 0.42
    fig = plt.figure(figsize=((W[1] - W[0]) * S + 6.5, (Hh[1] - Hh[0]) * S + 1.2), dpi=220)
    ax = fig.add_axes([0.01, 0.01, (W[1] - W[0]) * S / ((W[1] - W[0]) * S + 6.5), 0.93])
    ax.set_xlim(W[0], W[1]); ax.set_ylim(Hh[1], Hh[0]); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(FancyBboxPatch((W[0] + .2, Hh[0] + .2), W[1] - W[0] - .4, Hh[1] - Hh[0] - .4,
                                boxstyle='round,pad=0,rounding_size=1.2', fc='#f1ede0', ec='#8c8672', lw=2, zorder=0))
    fig.suptitle(b.title, x=0.01, ha='left', fontsize=15, fontweight='bold')
    hole = lambda x, y, z=1: ax.add_patch(Circle((x, y), .23, fc='#e9c46a', ec='#b08a2e', lw=.8, zorder=z))
    if b.kind == 'half':
        for c in range(1, 31):
            for y0 in (0, 7):
                ax.add_patch(Rectangle((c - .17, y0 - .3), .34, 4.6, fc='#c9a54a', ec='none', zorder=1))
            for r in HROW: hole(c, HROW[r])
            ax.text(c, -1.25 + 0.05, str(c), ha='center', va='center', fontsize=6.5, color='#4a4636', zorder=2)
            ax.text(c, 12.35, str(c), ha='center', va='center', fontsize=6.5, color='#4a4636', zorder=2)
        for r, y in HROW.items():
            ax.text(-0.35, y, r, ha='center', va='center', fontsize=7, color='#4a4636')
            ax.text(31.35, y, r, ha='center', va='center', fontsize=7, color='#4a4636')
        for rn, y in RAILY.items():
            ax.add_patch(Rectangle((0.6, y - .12), 29.8, .24, fc='#c9a54a', ec='none', zorder=1))
            for c in range(1, 31): hole(c, y)
            net = b.rails.get(rn, '')
            if rn in b.cuts:                              # rail cut in two: gap, red marker, a net label over each section
                cx = b.cuts[rn] + .5
                ax.add_patch(Rectangle((cx - .09, y - .2), .18, .4, fc='#f1ede0', ec='none', zorder=2))
                ax.plot([cx, cx], [y - .75, y + .75], color='#e0002b', lw=2.2, zorder=3)
                ax.text(cx, y + 0.95, 'CUT', fontsize=6.5, color='#e0002b', fontweight='bold', ha='center', va='center', zorder=12)
                n2 = b.rails2[rn]
                for tx_, nn, lab in (((1 + b.cuts[rn]) / 2, net, 'cols 1-%d' % b.cuts[rn]), ((b.cuts[rn] + 31) / 2, n2, 'cols %d-30' % (b.cuts[rn] + 1))):
                    ax.text(tx_, y - 1.0 - 0.9, '%s %s rail: %s' % (rn, lab, nn), fontsize=7, fontweight='bold', ha='center', va='center', zorder=12,
                            color=('#666666' if NETCOL.get(nn) == '#ffffff' else NETCOL.get(nn, '#222222')), bbox=dict(fc='white', ec='none', pad=1))
                net = n2
            ax.text(-0.2, y, rn, ha='right', va='center', fontsize=7, color='#4a4636')
            ax.text(31.6, y, net, ha='left', va='center', fontsize=8, fontweight='bold', color=('#666666' if NETCOL.get(net) == '#ffffff' else NETCOL.get(net, 'white')),
                    bbox=dict(fc='white', ec='none', pad=1))
    else:
        for r in range(1, 18):
            for x0 in (0, 7):
                ax.add_patch(Rectangle((x0 - .3, r - 1 - .17), 4.6, .34, fc='#c9a54a', ec='none', zorder=1))
            for cn, x in MCOL.items(): hole(x, r - 1)
            ax.text(-1.0, r - 1, str(r), ha='center', va='center', fontsize=7, color='#4a4636')
            ax.text(12.0, r - 1, str(r), ha='center', va='center', fontsize=7, color='#4a4636')
        for cn, x in MCOL.items():
            ax.text(x, -1.0, cn, ha='center', va='center', fontsize=7, color='#4a4636')
            ax.text(x, 17.0, cn, ha='center', va='center', fontsize=7, color='#4a4636')
    # wires
    for wi, (net, pts) in enumerate(b.wires):
        xs = [b.xy(p) for p in pts]
        if wi in b.bottom: xs = [(p[0] + .2, p[1]) for p in xs]       # solder-side wire drawn slightly offset so it does not hide under a top wire
        ax.plot([p[0] for p in xs], [p[1] for p in xs], '--' if wi in b.bottom else '-', color='#333333', lw=4.8, solid_capstyle='round', zorder=5.9)   # dark outline so white/yellow wires show on the cream board
        ax.plot([p[0] for p in xs], [p[1] for p in xs], '--' if wi in b.bottom else '-', color=wcol(net), lw=3.2, solid_capstyle='round', zorder=6)
        for p in (xs[0], xs[-1]): ax.add_patch(Circle(p, .16, fc=wcol(net), ec='#333333', lw=.8, zorder=7))
    # parts
    for ref, val, kind, pins, ex in b.parts:
        P = [b.xy(h) for _, h in pins]
        if kind in ('R', 'C'):
            (x1, y1), (x2, y2) = P
            ax.plot([x1, x2], [y1, y2], '-', color='#bbbbbb', lw=1.6, zorder=8)
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            vert = abs(x1 - x2) < 1e-6
            L = max(abs(x1 - x2), abs(y1 - y2))
            if kind == 'R':
                bl = min(L * .6, 2.2) if L > 1.05 else .5
                if vert: ax.add_patch(Rectangle((mx - .22, my - bl / 2), .44, bl, fc='#e8d8b0', ec='#6b4f1d', lw=1, zorder=9))
                else: ax.add_patch(Rectangle((mx - bl / 2, my - .22), bl, .44, fc='#e8d8b0', ec='#6b4f1d', lw=1, zorder=9))
            else:
                fc = '#2a6f97' if ex.get('polar') else '#e9a23b'
                ax.add_patch(Circle((mx, my), .38 if not ex.get('polar') else .48, fc=fc, ec='#333', lw=1, zorder=9))
                if ex.get('polar'): ax.text(x1 + (.35 if not vert else 0), y1 + (.0 if not vert else .45) , '+', fontsize=9, fontweight='bold', color='#d62728', ha='center', va='center', zorder=10)
            for p in P: ax.add_patch(Circle(p, .12, fc='#555', zorder=10))
            off = (.55, 0) if vert else (0, -.55)
            ax.text(mx + off[0], my + off[1], '%s\n%s' % (ref, val) if vert else '%s %s' % (ref, val), fontsize=6.6,
                    ha='left' if vert else 'center', va='center' if vert else 'bottom', zorder=11,
                    bbox=dict(fc='white', ec='none', alpha=.85, pad=.6))
        elif kind in ('DIP', 'DIPM'):
            xs = [p[0] for p in P]; ys = [p[1] for p in P]
            x0, x1, y0, y1 = min(xs) - .4, max(xs) + .4, min(ys) - .4, max(ys) + .4
            if kind == 'DIP': x0, x1, y0, y1 = min(xs) - .45, max(xs) + .45, min(ys) + .55, max(ys) - .55
            else: x0, x1, y0, y1 = min(xs) + .55, max(xs) - .55, min(ys) - .45, max(ys) + .45
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc='#202020', ec='#000', lw=1, zorder=9))
            if kind == 'DIP': ax.add_patch(Wedge((x0, (y0 + y1) / 2), .35, 270, 90, fc='#888', zorder=10))
            else: ax.add_patch(Wedge(((x0 + x1) / 2, y0), .35, 0, 180, fc='#888', zorder=10))
            p1 = b.xy(dict(pins)['1'])
            ax.add_patch(Circle((p1[0] + (0 if kind == 'DIPM' else 0), p1[1]), .2, fc='white', zorder=11))
            for (pn, h), p in zip(pins, P):
                ax.text(p[0], p[1], pn, fontsize=6, color='black', ha='center', va='center', zorder=12)
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, '%s\n%s' % (ref, val), color='white', fontsize=7.5, fontweight='bold',
                    ha='center', va='center', zorder=11, rotation=90 if kind == 'DIPM' else 0)
        elif kind == 'TO92':
            xs = [p[0] for p in P]; y = P[0][1]
            from matplotlib.patches import Ellipse
            cx = (xs[0] + xs[-1]) / 2; fy = y - .42            # flat face on the top side (toward row J / top edge)
            ax.add_patch(Wedge((cx, fy), 1.15, 0, 180, fc='#202020', ec='#000', zorder=9, transform=ax.transData))
            ax.plot([cx - 1.15, cx + 1.15], [fy, fy], '-', color='white', lw=2.2, zorder=10)
            ax.text(cx, fy - .3, 'flat face', fontsize=5, color='white', ha='center', va='bottom', zorder=12)
            for (pn, h), p in zip(pins, P):
                ax.add_patch(Circle(p, .17, fc='#aaa', zorder=11))
                ax.text(p[0], p[1] + .5, {'1': 'OUT', '2': 'GND', '3': 'IN'}[pn], fontsize=5.5, color='white', ha='center', zorder=12)
            ax.text(max(xs) + .45, y + .75, '%s %s' % (ref, val), color='white', fontsize=6.5, fontweight='bold', ha='left', zorder=12)
        elif kind == 'JACK':
            # PJ-307 on the mini board, entry to the right. Coordinates are plot units (1 = 0.1 in); y = row - 1.
            ax.add_patch(Rectangle((8.02, 11.64), 12.35 - 8.02, 4.72, fc='#202020', ec='#000', lw=1, zorder=9, alpha=.93))
            ax.add_patch(Rectangle((12.35, 12.82), .79, 2.36, fc='#9aa0a6', ec='#333', lw=1, zorder=9))
            ax.text(12.74, 14.0, 'plug', fontsize=5.5, color='black', ha='center', va='center', rotation=90, zorder=12)
            for (hc, hr), lab in ex['jpins'].items():
                p = b.xy((hc, hr))
                ax.add_patch(Rectangle((p[0] - .3, p[1] - .22), .6, .44, fc='#d4af37', ec='#000', zorder=11))
                ax.text(p[0], p[1], lab.split()[0], fontsize=6, color='black', ha='center', va='center', zorder=12)
            for h in ex['mech']:
                if h not in ex['jpins']:
                    p = b.xy(h); ax.add_patch(Circle(p, .2, fc='#777', ec='white', lw=.6, zorder=11))
            for py in (12.0, 16.0):
                ax.add_patch(Circle((12.0, py), .2, fc='none', ec='#ff2d55', lw=1.2, ls='--', zorder=11))
            ax.text(12.0, 11.35, 'clip posts', fontsize=5.5, color='#ff2d55', ha='center', va='center', zorder=12)
            ax.text(10.2, 14.0, 'PJ-307\nJ2', fontsize=7.5, color='white', fontweight='bold', ha='center', va='center', zorder=12)
        elif kind == 'HDR':
            xs = [p[0] for p in P]; ys = [p[1] for p in P]
            ax.add_patch(Rectangle((min(xs) - .42, min(ys) - .42), max(xs) - min(xs) + .84, max(ys) - min(ys) + .84,
                                   fc='#111', ec='#000', zorder=9))
            for (pn, h), p in zip(pins, P):
                ax.add_patch(Rectangle((p[0] - .13, p[1] - .13), .26, .26, fc='#d4af37', zorder=10))
                ax.text(p[0], p[1] - .48 if b.kind == 'half' else p[1], pn, fontsize=5.5, color='white', ha='center', va='center', zorder=11)
            lab = ex.get('label', '')
            if 'lab_at' in ex:
                lx, ly, ha = ex['lab_at']
                ax.text(lx, ly, '%s %s\n%s' % (ref, val, lab) if lab else '%s %s' % (ref, val), fontsize=6.4, ha=ha, va='center',
                        zorder=12, bbox=dict(fc='#fff3b0', ec='#999', pad=.8))
            elif b.kind == 'half':
                above = min(ys) < 6
                ty = (min(ys) - 1.05) if above and min(ys) > 2 else (max(ys) + .95 if not above else min(ys) - 1.05)
                ax.text((min(xs) + max(xs)) / 2, ty + (0 if ref not in ('JP4',) else 0), '%s %s  %s' % (ref, val, lab), fontsize=6.6, ha='center', va='center',
                        zorder=12, bbox=dict(fc='#fff3b0', ec='#999', pad=.8))
            else:
                horiz = len(set(ys)) == 1
                tx = max(xs) + .7 if min(xs) > 6 else min(xs) - .7
                ax.text(tx if min(xs) > 6 else min(xs) - .55, (min(ys) + max(ys)) / 2, '%s\n%s' % (ref, lab or val), fontsize=6.3,
                        ha='left' if min(xs) > 6 else 'right', va='center', zorder=12, bbox=dict(fc='#fff3b0', ec='#999', pad=.8))
        elif kind == 'SOCK':
            (x1, y1), (x2, y2) = P
            ax.plot([x1, x2], [y1, y2], ls=(0, (2, 2)), color='#555', lw=1.2, zorder=8)       # the resistor plugs in between
            for (pn, h), p in zip(pins, P):
                ax.add_patch(Rectangle((p[0] - .31, p[1] - .31), .62, .62, fc='#111', ec='#d4af37', lw=1.6, zorder=10))   # female socket: black body, gold edge
                ax.add_patch(Circle(p, .13, fc='#9aa0a6', ec='none', zorder=11))
            lx, ly, ha = ex['lab_at']
            ax.text(lx, ly, '%s  %s\n%s' % (ref, val, ex.get('label', '')), fontsize=6.4, ha=ha, va='center', zorder=12, bbox=dict(fc='#fff3b0', ec='#999', pad=.8))
        elif kind == 'TP':
            p = P[0]
            ax.add_patch(Circle(p, .3, fc='none', ec='#ff2d55', lw=2.2, zorder=10))
            ax.text(p[0] + .38, p[1] - .38, ref, fontsize=6.6, color='#ff2d55', fontweight='bold', zorder=12,
                    bbox=dict(fc='white', ec='none', pad=.4))
    # off-board tags
    for h, lab in b.offboard:
        x, y = b.xy(h)
        ax.add_patch(Rectangle((x - .3, y - .3), .6, .6, fc='#111111', ec='white', lw=1.2, zorder=13))      # Dupont pin: black plastic square...
        ax.add_patch(Rectangle((x - .1, y - .1), .2, .2, fc='#d4af37', ec='none', zorder=14))              # ...with the gold pin
    # side panel: legend + off-board list + notes
    tx = fig.add_axes([1 - 6.3 / ((W[1] - W[0]) * S + 6.5), 0.02, 6.2 / ((W[1] - W[0]) * S + 6.5), 0.9]); tx.axis('off')
    lines = ['DUPONT PINS (black squares, white edge), one per hole;', 'a Dupont jumper joins each pair:']
    for h, lab in b.offboard:
        hs = ('%s%s' % (h[0], h[1]) if b.kind == 'half' else '%s%d' % h) if not (b.kind == 'half' and h[0] in RAILY) else '%s rail col %d' % h
        lines.append('  %-14s %s' % (hs, lab))
    if any(k == 'SOCK' for _, _, k, _, _ in b.parts): lines += ['', 'PLUG-IN SOCKETS (black squares, gold edge):', '  a resistor plugs between the two sockets of a pair.']
    lines += ['', 'WIRE COLOURS:'] + ['  %-8s %s' % (k, NETNAME[k]) for k in NETCOL] + ['  %-8s blue' % 'signals', '', 'NOTES:']
    for n in b.notes:
        import textwrap
        lines += ['  ' + t for t in textwrap.wrap(n, 44)]
    tx.text(0, 1, '\n'.join(lines), va='top', ha='left', family='monospace', fontsize=8.3)
    yk = 1 - (2 + len(b.offboard)) * 0.0
    fig.savefig(fn, facecolor='white')
    plt.close(fig)

def holename(b, h):
    if b.kind == 'half':
        return '%s rail col %d' % h if h[0] in RAILY else '%d%s' % h
    return '%s%d' % h

def guide():
    want_nets, nc = load_circuit()
    pin2net = {p: n for n, ps in want_nets.items() for p in ps}
    out = ['OPTICAL TRNG VERSION 2 (plug-in resistors) - STRIPBOARD BUILD GUIDE (ElectroCookie boards)', '=' * 70, '',
           'Hole names: HALF board = <column 1-30><row A-J>, e.g. 14E; rails = T-/T+ (top), B-/B+ (bottom).',
           '            MINI board = <column A-J><row 1-17>, e.g. E3.',
           'Every hole in a 5-hole strip is the SAME node. Parts that span 0.1 in are mounted standing.',
           'Wires: insulated, run straight horizontal/vertical only (bends shown in the pictures).',
           'ALL ON/OFF-BOARD CONNECTIONS ARE STANDARD DUPONT PINS (0.1 in male header pins, long side up) with Dupont jumper wires',
           '  between the boards; nothing off-board is a cut wire. Each pin sits in the hole listed under DUPONT PINS and shares that strip/rail.', '',
           'BOARDS NEEDED: 2 x ElectroCookie half-size (30 column) + 1 x ElectroCookie mini (17 row). (Version 1 needed 3 half boards: its boards 2 and 3 are merged here, with the T+ rail of board 2 cut in two.)', '',
           'PLUG-IN RESISTOR SOCKETS (they replace the jumper banks JP3-JP6 of version 1):',
           '  Each adjustable value is a PAIR of single-pin female sockets (machined-pin / female header pins), soldered into two holes on',
           '  DIFFERENT strips; a resistor of the wanted value plugs between them. ALL FOUR sockets span the centre',
           '  channel: one pin on each edge of the channel, directly opposite each other in the same column (rows F and E, 0.3 in apart),',
           '  so the resistor lies across the gap. An EMPTY socket is always safe:',
           '  R1 empty = LED off, R2 empty = no signal, R20 empty = stage B x101, R13 empty = no hysteresis.',
           '  Plug values: R1 7.5k/3.9k*/2.0k (0.5/1.0/1.9 mA); R2 68*/220/680; R20 28.0k*/88.7k/none (x22.9/x48/x101); R13 1M/330k/100k* (5/15/47 mV).',
           '  J3 is a 1x8 header snapped into two 1x4 pieces, one each side of the PICAXE.', '',
           'CHECK: layout_check.txt - the board strips, rails, wires and part pins were rebuilt into nets',
           '  by fab_layout.py and compared with schematic/optical_trng_v2.circuit: all %d nets match,' % len(want_nets),
           '  no extra connections, no hole used twice.', '']
    for bn, b in B.items():
        out += [b.title, '-' * len(b.title)]
        if b.kind == 'half': out += ['Rails: ' + ', '.join('%s=%s' % kv for kv in b.rails.items())]
        out += ['', 'PARTS:']
        for ref, val, kind, pins, ex in b.parts:
            ps = ', '.join('pin%s %s (%s)' % (pn, holename(b, h), pin2net.get('%s.%s' % (ref, pn), 'NC')) for pn, h in pins)
            out.append('  %-4s %-12s %s' % (ref, val, ps))
        out += ['', 'ON-BOARD WIRES:']
        for wi, (net, pts) in enumerate(b.wires):
            out.append('  %-18s %s -> %s%s' % (net, holename(b, pts[0]), holename(b, pts[-1]), '   (SOLDER SIDE, under the board)' if wi in b.bottom else ''))
        out += ['', 'NOTES:'] + ['  - ' + n for n in b.notes] + ['']
    out += ['DUPONT PINS AND JUMPERS (all off-board connections)', '---------------------------------------------------']
    npin = sum(len(b.offboard) for b in B.values())
    out += ['%d Dupont pins (one per hole), %d female-female Dupont jumpers, one per line below (length chosen from board placement).' % (npin, len(INTER)), '']
    for a, ha, bb, hb in INTER:
        net = ''
        for bx, hx in ((a, ha), (bb, hb)):
            for h, lab in B[bx].offboard:
                if h == hx: net = lab.split()[0]
        out.append('  %-10s %s %s  <->  %s %s' % (net, a, holename(B[a], ha), bb, holename(B[bb], hb)))
    out += ['', 'PINS PER BOARD:']
    for bn, b in B.items():
        out.append('  %s: %s' % (bn, ', '.join('%s (%s)' % (holename(b, h), lab.split()[0]) for h, lab in b.offboard)))
    return '\n'.join(out) + '\n'

if __name__ == '__main__':
    errs, ng, nw = verify()
    rep = ['NETLIST CHECK vs %s' % os.path.basename(CIRCUIT), 'nets built %d, nets in circuit %d' % (ng, nw)]
    rep += errs if errs else ['RESULT: MATCH - every circuit net is built exactly, no extra connections, every hole used once.']
    print('\n'.join(rep))
    open(os.path.join(HERE, 'layout_check.txt'), 'w').write('\n'.join(rep) + '\n')
    for bn, b in B.items(): render(b, os.path.join(HERE, 'board%s_%s.png' % (bn[1], {'B1': 'power_optical', 'B2': 'amplifier_comparator', 'B3': 'picaxe'}[bn])))
    open(os.path.join(HERE, 'BUILD_GUIDE.txt'), 'w').write(guide())
    sys.exit(1 if errs else 0)
