# Optical-noise TRNG VERSION 2 (plug-in resistor sockets) schematic, derived from optical_trng_sch_v5.py. Connectivity comes only from optical_trng_v2.circuit.
import sys; sys.path.insert(0,'.')
import kisch
from kisch import *
_orig=kisch._custom
def _c(n):   # MCP6022 / LM393: DIP-8 dual, one V+ (pin 8) and one V- / GND (pin 4) on unit A only, unit B = pins 5,6,7
    if n=='MCP6022': return kisch._opamp_text('MCP6022',both=False).replace('(name "V-"','(name "~"').replace('(name "V+"','(name "~"')
    if n=='LM393': return kisch._opamp_text('LM393',both=False).replace('(name "V-"','(name "~"').replace('(name "V+"','(name "~"')
    if n=='PLUG2':    # 2-pin resistor SOCKET: housing with two round contact holes; same pin geometry as Device:R (pins at +-3.81 mm)
        ln=lambda a,b:'(polyline (pts (xy 0 %g) (xy 0 %g)) (stroke (width 0.254) (type default) (color 0 0 0 0)) (fill (type none)))'%(a,b)
        body='(rectangle (start -2.032 2.54) (end 2.032 -2.54) (stroke (width 0.254) (type default) (color 0 0 0 0)) (fill (type background)))'
        hole=lambda y:'(circle (center 0 %g) (radius 0.889) (stroke (width 0.254) (type default) (color 0 0 0 0)) (fill (type outline)))'%y
        pin=lambda y,a,num:'(pin passive line (at 0 %g %d) (length 1.27)\n        (name "~" (effects (font (size 1.27 1.27))))\n        (number "%s" (effects (font (size 1.27 1.27))))\n      )'%(y,a,num)
        return ('(symbol "PLUG2" (pin_names (offset 0) hide) (pin_numbers hide) (in_bom yes) (on_board yes)\n'
          '    (property "Reference" "R" (id 0) (at 2.54 -1.27 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
          '    (property "Value" "PLUG" (id 1) (at 2.54 1.27 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
          '    (property "Footprint" "" (id 2) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
          '    (property "Datasheet" "" (id 3) (at 0 0 0) (effects (font (size 1.27 1.27)) hide))\n'
          '    (symbol "PLUG2_1_1"\n      %s\n      %s\n      %s\n      %s\n      %s\n      %s\n      %s\n    )\n  )')%(body,hole(1.27),hole(-1.27),ln(2.54,2.159),ln(-2.54,-2.159),pin(3.81,270,'1'),pin(-3.81,90,'2'))
    return _orig(n)
kisch._custom=_c
_w=kisch.Sch.wire; _a=kisch.Sch.add; _t=kisch.Sch.text   # round every coordinate to 0.001 mm so float noise cannot break pin coincidence
kisch.Sch.wire=lambda s,*pts:_w(s,*[(round(x,3),round(y,3)) for x,y in pts])
kisch.Sch.add=lambda s,lib,name,ref,val,x,y,*r,**k:_a(s,lib,name,ref,val,round(x,3),round(y,3),*r,**k)
kisch.Sch.text=lambda s,t,x,y,*r:_t(s,t,round(x,3),round(y,3),*r)
# ---- boxes: PICAXE-08M2 DIP-8 (pins as in PICAXE manual 2), connectors ----
BOXES['PICAXE_08M2_OPT']=('U','PICAXE-08M2',
  [('4','C.3_IN','input')],
  [('7','C.0_SER_OUT','output')]+[None]*11+[('2','C.5_SER_IN','input'),None],
  [('1','+V','power_in')],[('3','C.4','bidirectional'),('5','C.2','bidirectional'),('6','C.1','bidirectional'),('8','0V','power_in')],35.56,False,14)
BOXES['CONN_J3']=('J','PICAXE_ALL_8_PINS',[None,None,('1','+5V','passive')],[],
  [('4','C.3','passive'),('3','C.4','passive'),('5','C.2','passive'),('6','C.1','passive'),('2','C.5','passive'),('7','C.0','passive')],
  [('8','GND','passive')],38.1,False,6)
BOXES['CONN_VIN']=('J','VIN_9V',[],[('1','VIN','power_out'),('2','GND','power_out')],[],[],17.78,False,2)
BOXES['CONN_PROG']=('J','PICAXE_PROGRAM',[('3','PICAXE_TX','passive'),('2','PROG_TX','passive'),('1','GND','passive')],[],[],[],22.86,False,3)

S=Sch('Optical Noise TRNG - FOD852 MCP6022 LM393 PICAXE-08M2',paper='A3')
S.meta(['FOD852 -> MCP6022 -> LM393 -> PICAXE C.3. VREF 2.5 V.','Version 2: plug-in resistor sockets R1 R2 R13 R20. Not validated.'],'11/26')
p=S.pin
def R(ref,val,x,yc,rot=0,**k): return S.add('Device','R',ref,val,x,yc,rot=rot,**k)
def C(ref,val,x,yc,**k): return S.add('Device','C',ref,val,x,yc,**k)
def PL(ref,val,x,yc,rot=0,**k): return S.add('filter','PLUG2',ref,val,x,yc,rot=rot,**k)
def tp(ref,x,y):
    S.add('Connector','TestPoint',ref,'TESTPOINT',x,y,rp=(2.0,-2.4),vp=(0,0),show=False); S.inst[-1]['hidev']=True
H=3.81
def pwr(name,x,y):    # +5V_OPT gets its own arrow symbol (UP_+5V_OPT) so KiCad keeps it a separate net from +5V
    if name!='+5V_OPT': return S.power(name,x,y)
    S.pw+=1; return S.add('filter','UP_+5V_OPT','#PWR%02d'%S.pw,'+5V_OPT',x,y,0,show=False,rp=(0,0),vp=(0,-4.8))
DX=15.24
J1X,J1Y=30.48,17.78
def hdr(ref,val,name,x,y,mir=False):
    S.add('Connector_Generic',name,ref,val,x,y,mirror=mir,rp=(1.27,-6.2) if name.endswith('03_Odd_Even') else (1.27,-3.4),vp=(1.27,6.4) if name.endswith('03_Odd_Even') else (1.27,6.4))
YB=154.94                     # VREF bus
# =================== power connector ===================
S.add('filter','CONN_VIN','J1','VIN_9V',J1X,J1Y,rp=(-8.89,-6.0),vp=(-8.89,-3.8))
j1=p('J1','1'); S.power('GND',*p('J1','2'))
# =================== regulators: U5 -> +5V_OPT, U6 -> +5V, shared VIN ===================
xb=j1[0]+5.08; xc8=xb+5.08; xr=xc8+12.7
for k,(ref,ci,co,rail,dy) in enumerate((('U5','C8','C9','+5V_OPT',0.0),('U6','C10','C11','+5V',22.86))):
    yU=j1[1]+dy
    S.add('Regulator_Linear','MC78L05_TO92',ref,'WS78L05',xr,yU,rp=(0,-6.4),vp=(0,-4.1))
    vi=p(ref,'3'); vo=p(ref,'1'); g=p(ref,'2')
    assert abs(vi[1]-yU)<.01 and abs(vi[0]-(xc8+5.08))<.01
    S.wire((xb,yU),vi)
    C(ci,'0.33uF',xc8,yU+H,left=True); S.power('GND',*p(ci,'2'))
    S.power('GND',*g)
    xo=vo[0]+5.08; S.wire(vo,(xo+5.08,yU)); C(co,'0.1uF',xo,yU+H); S.power('GND',*p(co,'2'))
    pwr(rail,xo+5.08,yU)
S.wire(j1,(xb,j1[1]),(xb,j1[1]+22.86))
# =================== optical detector ===================
S.add('Isolator','PC817','U1','FOD852',50.8,101.6,rp=(0,8.6),vp=(0,10.8))
a=p('U1','1'); k=p('U1','2'); e=p('U1','3'); c=p('U1','4')
# R1 = LED current resistor SOCKET: +5V_OPT -> R1 -> LED anode (U1.1)
yb=a[1]-7.62; yt=yb-7.62
S.wire(a,(a[0],yb)); PL('R1','PLUG',a[0],yb-H)
S.wire((a[0],yt),(a[0],yt-5.08)); pwr('+5V_OPT',a[0],yt-5.08)
S.text('R1 plug 7.5k = 0.5 mA',a[0]-31.75,yb-H-2.54)
S.text('R1 plug 3.9k = 1.0 mA *',a[0]-31.75,yb-H)
S.text('R1 plug 2.0k = 1.9 mA',a[0]-31.75,yb-H+2.54)
S.text('R1 empty = LED off',a[0]-31.75,yb-H+5.08)
S.wire(k,(k[0],k[1]+5.08)); S.power('GND',k[0],k[1]+5.08)
S.wire(e,(e[0],e[1]+5.08)); S.power('GND',e[0],e[1]+5.08)
# R2 = collector LOAD resistor SOCKET: +5V_OPT -> R2 -> DETECTOR (U1.4)
yb2=c[1]-7.62; yt2=yb2-7.62
S.wire(c,(c[0],yb2)); PL('R2','PLUG',c[0],yb2-H)
S.wire((c[0],yt2),(c[0],yt2-5.08)); pwr('+5V_OPT',c[0],yt2-5.08)
S.text('R2 plug 68R *',c[0]+10.16,yb2-H-2.54)
S.text('R2 plug 220R / 680R',c[0]+10.16,yb2-H)
S.text('R2 empty = no signal',c[0]+10.16,yb2-H+2.54)
Ys=c[1]                                           # signal row of the first stage (DETECTOR)
tp('TP1',c[0]+5.08,Ys)
C('C1','100nF',c[0]+10.16,Ys+H,left=True)
S.wire((c[0],Ys),p('C1','1'))
b=p('C1','2'); jx=b[0]+5.08; S.wire(b,(jx,b[1]),(jx,Ys))
N1=(jx+5.08,Ys); S.wire((jx,Ys),N1)
# =================== stage A (U2 unit 1): gain 1+47k/1k ===================
ux,uy=114.3,101.6
S.add('filter','MCP6022','U2','MCP6022',ux,uy,unit=1,rp=(2.54,-11.5),vp=(2.54,-9.2))
S.wire(N1,p('U2','3',1))
# R5 : AMP_A_PLUS -> VREF, lies sideways below the node
yR5=Ys+12.7; S.wire(N1,(N1[0],yR5)); R('R5','100k',N1[0]+H,yR5,rot=90)
# - input network
mp=p('U2','2',1); xm=mp[0]-5.08; S.wire(mp,(xm,mp[1]))
oA=p('U2','1',1); xo=oA[0]+5.08; S.wire(oA,(xo,oA[1]))
y1=uy+12.7; xr=ux+5.08
R('R7','47k',xr,y1+H); S.wire((xo,oA[1]),(xo,y1),p('R7','1'))
yfb=y1+2*H; S.wire(p('R7','2'),(xm,yfb)); S.wire((xm,mp[1]),(xm,yfb))
yR6=yfb+5.08; S.wire((xm,yfb),(xm,yR6)); R('R6','1k',xm+H,yR6,rot=90)
# power pins: V+ up, V- down; 100 nF straight on the V+ node
vp_=p('U2','8',1); vm_=p('U2','4',1)
S.wire(vp_,(vp_[0],vp_[1]-15.24)); S.power('+5V',vp_[0],vp_[1]-15.24)
cx=vp_[0]-8.89; C('C5','100nF',cx,vp_[1]-12.7+H+0.0)
S.wire((vp_[0],p('C5','1')[1]),p('C5','1')); S.power('GND',*p('C5','2'))
S.wire(vm_,(vm_[0],vm_[1]+5.08)); S.power('GND',vm_[0],vm_[1]+5.08)
tp('TP3',xo+5.08,oA[1])
# =================== coupling A -> B, stage B (U2 unit 2): gain 1+22k/1k ===================
Yb=oA[1]                                          # row y=100.0
S.wire((xo,Yb),(xo+5.08,Yb))
cb=xo+15.24
S.wire((xo+5.08,Yb),(cb,Yb)); C('C4','100nF',cb,Yb+H,left=True)
b4=p('C4','2'); jx4=b4[0]+5.08; S.wire(b4,(jx4,b4[1]),(jx4,Yb))
N2=(jx4+5.08,Yb); S.wire((jx4,Yb),N2)
ux2=175.26; uy2=104.14
S.add('filter','MCP6022','U2','MCP6022',ux2,uy2,unit=2,rp=(2.54,-6.5),vp=(2.54,-4.2))
S.wire(N2,p('U2','5',2))
yR8=Yb+12.7; S.wire(N2,(N2[0],yR8)); R('R8','100k',N2[0]+H,yR8,rot=90)
mp2=p('U2','6',2); xm2=mp2[0]-5.08; S.wire(mp2,(xm2,mp2[1]))
oB=p('U2','7',2); xo2=oB[0]+5.08; S.wire(oB,(xo2,oB[1]))
y1b=uy2+12.7; xr2=ux2+5.08
R('R10','100k',xr2,y1b+H); S.wire((xo2,oB[1]),(xo2,y1b),p('R10','1'))
yfb2=y1b+2*H; S.wire(p('R10','2'),(xm2,yfb2)); S.wire((xm2,mp2[1]),(xm2,yfb2))
yj=yfb2+7.62
xe5=xo2-12.7
PL('R20','PLUG',xm2+H,yj,rot=270); S.wire((xo2,y1b),(xo2,yj),p('R20','1'))   # R20 = gain SOCKET, in parallel with R10
assert p('R20','2')==(round(xm2,3),round(yj,3))
R('R9','1k',xm2,YB-H); S.wire((xm2,yfb2),p('R9','1'))
S.text('R20 plug 28.0k = x23 *',xm2+2.54,yj+6.35)
S.text('R20 plug 88.7k = x48',xm2+2.54,yj+8.89)
S.text('R20 empty = x101',xm2+2.54,yj+11.43)
tp('TP4',xo2+5.08,oB[1])
# =================== comparator U3 unit 1 : AMP_B_OUT on -, hysteresis on + ===================
uc=223.52
S.add('filter','LM393','U3','LM393',uc,101.6,unit=1,rp=(2.54,-11.5),vp=(2.54,-9.2))
m3=p('U3','2',1); S.wire((xo2,oB[1]),m3)                  # AMP_B_OUT row straight into the - pin
p3=p('U3','3',1); xp=p3[0]-5.08; S.wire(p3,(xp,p3[1]))
o3=p('U3','1',1); xoc=o3[0]+5.08; S.wire(o3,(xoc,o3[1]))
w3_=p('U3','4',1); yh=w3_[1]+15.24
PL('R13','PLUG',xp+H,yh-5.08,rot=270)   # R13 = hysteresis SOCKET: CMP_A_OUT -> R13 -> CMP_A_PLUS
S.wire((xoc,o3[1]),(xoc,yh-5.08),p('R13','1'))
assert p('R13','2')==(round(xp,3),round(yh-5.08,3))
yR11=yh+17.78; S.wire((xp,p3[1]),(xp,yR11)); R('R11','1.0k',xp+H,yR11,rot=270)   # pin 1 (VREF) on the right
S.text('R13: 1M=5mV',xp+2.54,yh-5.08+6.35)
S.text('R13: 330k=15mV',xp+2.54,yh-5.08+8.89)
S.text('R13: 100k=47mV *',xp+2.54,yh-5.08+11.43)
S.text('R13: empty=none',xp+2.54,yh-5.08+13.97)
R('R12','4.7k',xoc,o3[1]-H); S.power('+5V',xoc,o3[1]-2*H)
v3=p('U3','8',1); w3=p('U3','4',1)
S.wire(v3,(v3[0],v3[1]-15.24)); S.power('+5V',v3[0],v3[1]-15.24)
C('C6','100nF',v3[0]-8.89,v3[1]-12.7+H); S.wire((v3[0],p('C6','1')[1]),p('C6','1')); S.power('GND',*p('C6','2'))
S.wire(w3,(w3[0],w3[1]+5.08)); S.power('GND',w3[0],w3[1]+5.08)
tp('TP5',xoc+10.16,o3[1])
# comparator unit 2 : + to GND, - to VREF, output NC
ub=(259.08,128.27)
S.add('filter','LM393','U3','LM393',ub[0],ub[1],unit=2,rp=(2.54,-6.5),vp=(2.54,-4.2))
q5=p('U3','5',2); q6=p('U3','6',2); q7=p('U3','7',2)
S.wire(q5,(q5[0]-7.62,q5[1])); S.power('GND',q5[0]-7.62,q5[1])
xv=q6[0]-2.54; S.wire(q6,(xv,q6[1]),(xv,YB))
S.nc(*q7)
# =================== VREF generator at the left end of the bus ===================
xg=25.4
R('R3','10k',xg,YB-H); S.power('+5V',xg,YB-2*H)
R('R4','10k',xg,YB+H); S.power('GND',xg,YB+2*H)
C('C2','10uF',xg+10.16,YB+H) if False else S.add('Device','C_Polarized','C2','10uF',xg+10.16,YB+H)
S.power('GND',*p('C2','2'))
C('C3','100nF',xg+22.86,YB+H); S.power('GND',*p('C3','2'))
tp('TP2',xg+33.02,YB)
S.wire((xg,YB),(xv,YB))                                    # the VREF bus, with the drops from every VREF pin
for pt in (p('R5','2'),p('R6','2'),p('R8','2'),p('R9','2'),p('R11','1')):
    S.wire(pt,(pt[0],YB))
# =================== PICAXE U4 (rev 0.2) ===================
S.add('filter','PICAXE_08M2_OPT','U4','PICAXE-08M2',297.18,101.6,rp=(-17.78,-21.5),vp=(-17.78,-19.2))
dy=o3[1]-p('U4','4')[1]
for I in S.inst:
    if I['ref']=='U4': I['y']=round(I['y']+dy,3)
X=lambda d:round(p('U4','4')[0]+20.32+d,3)          # x relative to U4 centre
U4x=X(0); y0=p('U4','7')[1]; y5=p('U4','2')[1]
pv=p('U4','1'); S.wire(pv,(pv[0],pv[1]-17.78)); S.power('+5V',pv[0],pv[1]-17.78)
C('C7','100nF',pv[0]+7.62,pv[1]-15.24+H); S.wire((pv[0],p('C7','1')[1]),p('C7','1')); S.power('GND',*p('C7','2'))
S.power('GND',*p('U4','8'))
# J3 breakout under U4: C.4 / C.2 / C.1 straight down
S.add('filter','CONN_J3','J3','PICAXE_ALL_8_PINS',U4x,0,rp=(-19.05,13.0),vp=(-19.05,15.3))
dj=p('U4','3')[1]+17.78-p('J3','3')[1]
for I in S.inst:
    if I['ref']=='J3': I['y']=round(I['y']+dj,3)
for n in ('3','5','6'):
    assert abs(p('U4',n)[0]-p('J3',n)[0])<.01; S.wire(p('U4',n),p('J3',n))
yb=p('U4','3')[1]; ym1=yb+6.35; ym2=yb+8.89; ym3=yb+6.35
# C.3 / comparator row -> J3.4 (lane left of U4)
xl=X(-22.86); S.wire((xoc,o3[1]),(xl,o3[1]),p('U4','4'))
S.wire((xl,o3[1]),(xl,ym3),(p('J3','4')[0],ym3),p('J3','4'))
# J3.1 +5V, J3.8 GND
j31=p('J3','1'); S.wire(j31,(j31[0]-2.54,j31[1])); S.power('+5V',j31[0]-2.54,j31[1])
S.power('GND',*p('J3','8'))
# C.5 chain: U4.2 row -> J3.2 node, R15 node, JP1 (pin 2 bottom, pin 1 top) <- R14 <- J2.2
xjp1=X(40.64); xr14=X(50.8); xjp2=X(58.42); xj=X(68.58)
S.add('filter','CONN_PROG','J2','PICAXE_PROGRAM',xj+11.43+2.54,0,rp=(-11.43,7.5),vp=(-11.43,9.8))
dj2=(y0+10.16)-p('J2','3')[1]
for I in S.inst:
    if I['ref']=='J2': I['y']=round(I['y']+dj2,3)
j3_=p('J2','3'); j2_=p('J2','2'); j1_=p('J2','1')
# rev 0.5: JP2 = PICAXE AXE021 proto-board style changeover link on C.0 (leg 7): pin 2 (side) = COMMON = U4.7, pin 1 (top) = PROG -> J2.3 (download jack),
# pin 3 (bottom) = OUT -> J3.7. Shunt 1-2 = PROG, shunt 2-3 = OUT.
S.add('Jumper','Jumper_3_Open','JP2','3PIN_PROG_OUT',xjp2,y0,rot=270,rp=(8.5,-1.27),vp=(8.5,1.27))
assert abs(p('JP2','2')[1]-y0)<.01 and p('JP2','1')[0]==p('JP2','3')[0]
S.wire(p('U4','7'),p('JP2','2'))
xp=round(p('JP2','1')[0]+5.08,3)
S.wire(p('JP2','1'),(xp,p('JP2','1')[1]),(xp,j3_[1]),j3_)
R('R14','22k',xr14,j2_[1]+H); S.wire(j2_,p('R14','1'))
S.add('Jumper','Jumper_2_Open','JP1','2PIN_SHUNT',xjp1,p('R14','2')[1]+5.08,rot=270,rp=(3.0,-1.27),vp=(3.0,1.27))
assert abs(p('JP1','2')[1]-y5)<.01, (p('JP1','2'),y5)
S.wire(p('R14','2'),p('JP1','1'))
S.wire(p('U4','2'),(X(22.86),y5),(X(33.02),y5),p('JP1','2'))
R('R15','10k',X(33.02),y5+H); S.power('GND',*p('R15','2'))
S.wire((X(22.86),y5),(X(22.86),ym1),(p('J3','2')[0],ym1),p('J3','2'))      # C.5 -> J3.2
S.wire(p('JP2','3'),(p('JP2','3')[0],ym2),(p('J3','7')[0],ym2),p('J3','7'))      # JP2 OUT -> J3.7 (crosses the R14 row, no junction)
S.wire(j1_,(j1_[0]-5.08,j1_[1])); S.power('GND',j1_[0]-5.08,j1_[1])
S.center(205.74,150.0); S._centered=True
S.check_bodies(); S.check_overlaps()
S.write('optical_trng_v2.kicad_sch'); S.write('optical_trng_v2_render.kicad_sch',noflags=True)
print('written')
