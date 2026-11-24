#!/usr/bin/env python3
"""Full-scale wire cutting templates, ONE TEMPLATE PER (COLOUR, LENGTH), for one board of the optical TRNG stripboard build.

usage: python3 wire_templates.py B1 [suffix]     (B1..B3; optional suffix, e.g. _r3, goes before .pdf/.csv)

Reads the wire list and hole geometry from fab_layout.py (import only; nothing there is modified).
Writes  boardN_wire_templates<suffix>.pdf  (print at 100 %, check the scale bar on every page)
        boardN_wire_cutlist<suffix>.csv

Geometry (from fab_layout.py, checked against the ElectroCookie product images 2026-11-20, agreement ~0.1 mm):
1 unit = 0.1 in = 2.54 mm hole pitch.
Template model of one wire (drawn left to right, START hole at the left bend line, STOP hole at the right):
    S      = straight distance between the two hole centres
    LEG    = bare conductor beyond the bend axis, pushed through the hole (board 1.6 mm + solder stub)
    BEND   = insulation is stopped this far short of the hole centre (bend radius + insulation OD allowance)
    cut    = S + 2*LEG
    strip  = LEG + BEND at each end
    insulated length = S - 2*BEND
    START bend axis is LEG mm from the left cut end; STOP bend axis is LEG + S mm from the left cut end.
Change the three constants below to suit your wire/board; everything is recomputed.
"""
import sys, os, csv, importlib.util
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages

HERE = os.path.dirname(os.path.abspath(__file__))
PITCH = 2.54          # mm
LEG = 4.0             # mm bare conductor past the bend axis (1.6 mm board + ~2.4 mm solder stub)
BEND = 1.0            # mm bare run between insulation end and bend axis
INS_OD = 1.6          # mm insulation outer diameter drawn (assumed, ~22-24 AWG solid)
COND_D = 0.6          # mm conductor diameter drawn
SHORT_INS = 3.0       # mm: insulated length below this is flagged as a short bare staple

NETCOL = {'GND': ('black', '#222222'), '+5V': ('red', '#d62728'), '+5V_OPT': ('yellow', '#f2d600'),    # only the six wire colours on hand:
          'VREF': ('green', '#2ca02c'), 'VIN_9V': ('white', '#ffffff')}                                 # black red yellow green white blue
def col(net): return NETCOL.get(net, ('blue', '#1f77b4'))

spec = importlib.util.spec_from_file_location('fab_layout', os.path.join(HERE, 'fab_layout.py'))
fl = importlib.util.module_from_spec(spec); spec.loader.exec_module(fl)

bn = sys.argv[1] if len(sys.argv) > 1 else 'B1'
SUF = sys.argv[2] if len(sys.argv) > 2 else ''   # normally empty: one unversioned file per board
b = fl.B[bn]

def colrow(h):
    """(column, row) as printed on the board. Half board: column 1-30, row A-J or rail T-/T+/B-/B+. Mini: column A-J, row 1-17."""
    if b.kind == 'half':
        return (str(h[1]), h[0]) if h[0] in fl.RAILY else (str(h[0]), h[1])
    return (h[0], str(h[1]))
def cr(h): c, r = colrow(h); return 'col %s, row %s' % (c, r)

wires = []
for wi, (net, pts) in enumerate(b.wires):
    assert len(pts) == 2, 'bent wire not supported: %s %s' % (net, pts)
    (x1, y1), (x2, y2) = b.xy(pts[0]), b.xy(pts[1])
    assert x1 == x2 or y1 == y2, 'wire is not horizontal/vertical: %s %s' % (net, pts)
    S = (abs(x2 - x1) + abs(y2 - y1)) * PITCH
    wires.append(dict(net=net, start=cr(pts[0]), stop=cr(pts[1]), sc=colrow(pts[0]), ec=colrow(pts[1]), S=S,
                      side='solder side' if wi in b.bottom else 'top'))
for w in wires: w['colour'] = col(w['net'])[0]
wires.sort(key=lambda w: (round(w['S'], 2), w['colour'], w['net'], w['start']))
for i, w in enumerate(wires, 1):
    w['id'] = 'W%02d' % i
    w['cut'] = w['S'] + 2 * LEG
    w['ins'] = w['S'] - 2 * BEND
    w['bend1'] = LEG
    w['bend2'] = LEG + w['S']
groups = []                                       # one template per (colour, hole span); wires in a group are interchangeable
for w in wires:
    if groups and groups[-1]['colour'] == w['colour'] and round(groups[-1]['S'], 2) == round(w['S'], 2):
        groups[-1]['wires'].append(w)
    else:
        groups.append(dict(colour=w['colour'], hexc=col(w['net'])[1], S=w['S'], cut=w['cut'], ins=w['ins'], wires=[w]))
for i, g in enumerate(groups, 1):
    g['id'] = 'T%02d' % i
    for w in g['wires']: w['tmpl'] = g['id']

# ---------------- cut list CSV (one row per wire)
with open(os.path.join(HERE, 'board%s_wire_cutlist%s.csv' % (bn[1], SUF)), 'w', newline='') as f:
    wr = csv.writer(f)
    wr.writerow(['board', 'template', 'wire', 'net', 'colour', 'cut_length_mm', 'hole_span_mm', 'strip_each_end_mm',
                 'insulated_mm', 'start_col', 'start_row', 'stop_col', 'stop_row', 'side'])
    for w in wires:
        wr.writerow([bn, w['tmpl'], w['id'], w['net'], col(w['net'])[0], '%.2f' % w['cut'], '%.2f' % w['S'],
                     '%.1f' % (LEG + BEND), '%.2f' % w['ins'], w['sc'][0], w['sc'][1], w['ec'][0], w['ec'][1], w['side']])

# ---------------- printable PDF (US Letter, 1:1)
PW, PH = 215.9, 279.4
M = 14
ROWH = 19.0
def page():
    fig = plt.figure(figsize=(PW / 25.4, PH / 25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, PW); ax.set_ylim(0, PH); ax.axis('off')
    return fig, ax

def draw_header(ax, pg, first):
    def T(x, y, s, **k): return ax.text(x, PH - y, s, va='top', **k)
    def rect(x, y, w, h, **k): ax.add_patch(Rectangle((x, PH - y - h), w, h, **k))
    T(M, M, b.title, fontsize=11, fontweight='bold')                       # board title on its own line so a long title cannot run off the page
    title = T(M, M + 5.5, 'WIRE CUTTING TEMPLATES   (page %d of NPG)' % pg, fontsize=11, fontweight='bold')
    T(M, M + 11, 'PRINT AT 100 % (no fit-to-page). The bar below must measure exactly 50.0 mm.', fontsize=7)
    y = M + 15
    if first:
        T(M, y, 'Assumed: LEG %.1f mm, BEND %.1f mm, strip %.1f mm each end, insulation OD %.1f mm.' % (LEG, BEND, LEG + BEND, INS_OD), fontsize=7)
        T(M, y + 4, 'Lay real wire on its template (one template serves every wire listed beside it), cut at the end of the bare copper,', fontsize=7)
        T(M, y + 8, 'strip to the insulation, bend 90 deg at each dashed BEND line, push the bare end through the hole from the top (component', fontsize=7)
        T(M, y + 12, 'side), solder underneath.  S = START hole, E = STOP hole (ends are interchangeable until installed).', fontsize=7)
        y += 16
    rect(M, y + 1, 50, 1.2, facecolor='black'); T(M + 52, y + 0.5, '50.0 mm', fontsize=7)
    for k in range(0, 51, 10): ax.plot([M + k, M + k], [PH - (y + 4.5), PH - (y + 1)], color='black', lw=0.4)
    return y + 10, title

def group_h(g): return max(19.0, 9.0 + 3.5 * len(g['wires']))

def draw_group(ax, y, g):
    def T(x, yy, s, **k): ax.text(x, PH - yy, s, va='top', **k)
    def rect(x, yy, ww, h, **k): ax.add_patch(Rectangle((x, PH - yy - h), ww, h, **k))
    x0 = M + 2
    cy = y + 8.5
    cut, S = g['cut'], g['S']
    rect(x0, cy - COND_D / 2, cut, COND_D, facecolor='#d9a066', edgecolor='#8a5a2b', lw=0.3, zorder=2)
    rect(x0 + LEG + BEND, cy - INS_OD / 2, max(S - 2 * BEND, 0), INS_OD, facecolor=g['hexc'], edgecolor='black', lw=0.3, zorder=3)
    for bx in (x0 + LEG, x0 + LEG + S):
        ax.plot([bx, bx], [PH - (cy - 3.4), PH - (cy + 3.4)], color='black', lw=0.5, ls=(0, (3, 2)), zorder=5)
    for ex in (x0, x0 + cut):
        ax.plot([ex, ex], [PH - (cy - 3.4), PH - (cy + 3.4)], color='black', lw=0.5, zorder=5)
    T(x0 + LEG, cy + 3.6, 'S', fontsize=6.5, fontweight='bold', ha='center')
    T(x0 + LEG + S, cy + 3.6, 'E', fontsize=6.5, fontweight='bold', ha='center')
    for k in range(0, int(cut) + 1, 5):           # mm ruler ticks under the wire, from the left cut end
        ax.plot([x0 + k, x0 + k], [PH - (cy + 1.6), PH - (cy + 2.3)], color='#666666', lw=0.3)
    T(x0, y, '%s   %d x %s   cut %.1f mm   hole span %.2f mm   strip %.1f mm each end' %
      (g['id'], len(g['wires']), g['colour'].upper(), cut, S, LEG + BEND), fontsize=7.5, fontweight='bold')
    tx = x0 + max(cut, 22) + 8
    for i, w in enumerate(g['wires']):
        T(tx, y + 4.8 + 3.5 * i, '%s  %-9s  S: %-18s  E: %s%s' % (w['id'], w['net'], w['start'], w['stop'], '   [SOLDER SIDE]' if w['side'] != 'top' else ''), fontsize=6.5, family='monospace')
    if g['ins'] < SHORT_INS:
        T(x0, cy + 6.0, 'SHORT: insulation only %.1f mm. Use bare tinned wire (sleeve if needed).' % g['ins'], fontsize=6, color='#b00000')

pages = []                                        # (fig, ax, title_text)
def newpage():
    fig, ax = page(); y0, title = draw_header(ax, len(pages) + 1, not pages); pages.append((fig, ax, title)); return y0
y = newpage()
placed = []
for g in groups:
    h = group_h(g)
    if y + h > PH - M - 8:
        y = newpage()
    placed.append((len(pages) - 1, y, g)); y += h
npg = len(pages)
for fig, ax, title in pages:
    title.set_text(title.get_text().replace('NPG', str(npg)))
for pi, yy, g in placed:
    draw_group(pages[pi][1], yy, g)
if b.offboard:
    pages[-1][1].text(M, 14, 'Off-board connections (%d pins on this board) are standard Dupont pins with Dupont jumpers - nothing to cut. See BUILD_GUIDE.txt.' % len(b.offboard),
                      fontsize=6.5, va='bottom')
OUT = os.path.join(HERE, 'board%s_wire_templates%s.pdf' % (bn[1], SUF))
TMP = os.path.join(os.environ.get('TMPDIR', '/tmp'), os.path.basename(OUT) + '.tmp')   # render off the share first
with PdfPages(TMP) as pdf:
    for fig, ax, _ in pages: pdf.savefig(fig)
import shutil
try:
    shutil.copyfile(TMP, OUT + '.new'); os.replace(OUT + '.new', OUT)   # never truncate the live file in place
except OSError as e:
    print('COULD NOT REPLACE %s (%s). New PDF left at %s and %s.new - close the old PDF in any viewer and re-run.' % (OUT, e, TMP, OUT))
    sys.exit(2)

print('%d wires, %d templates, %d pages' % (len(wires), len(groups), npg))
for g in groups:
    print('%s %d x %-6s cut %6.2f span %6.2f  %s' % (g['id'], len(g['wires']), g['colour'], g['cut'], g['S'],
          ', '.join('%s %s > %s' % (w['id'], w['start'], w['stop']) for w in g['wires'])))
