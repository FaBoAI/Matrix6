"""Explicit two-layer redesign from the v0.7 source. No autorouting.

Development replay script: overwrites PCB with the specified geometry.
"""
from pathlib import Path
import subprocess, json
from sexpr import parse,child,children,dump,A,node
import wx, pcbnew as p

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'hardware/Matrix6'
BASE='f12c10f'
def original(ext):
    return subprocess.check_output(['git','show',f'{BASE}:hardware/Matrix6/Matrix6.{ext}'],cwd=ROOT).decode()

s=parse(original('kicad_pcb'))
layers=child(s,'layers')
layers[:]=[q for q in layers if not isinstance(q,list) or q[1] not in ['In1.Cu','In2.Cu']]
stack=child(child(s,'setup'),'stackup')
for q in list(children(stack,'layer')):
    if q[1] in ['In1.Cu','In2.Cu','dielectric 2','dielectric 3']:stack.remove(q)
core=next(q for q in children(stack,'layer') if q[1]=='dielectric 1')
child(core,'type')[1]='core';child(core,'thickness')[1]=A('1.53')
child(core,'material')[1]='FR4';child(core,'epsilon_r')[1]=A('4.5')
child(child(s,'general'),'thickness')[1]=A('1.6254')
child(child(s,'title_block'),'rev')[1]='0.8'
for z in list(children(s,'zone')):
    la=child(z,'layer')
    if la and la[1]=='In1.Cu':s.remove(z)
inner_ids={child(t,'uuid')[1] for t in children(s,'segment')+children(s,'arc') if child(t,'layer')[1]=='In2.Cu'}
for t in children(s,'segment')+children(s,'arc'):
    if child(t,'layer')[1]=='In2.Cu':child(t,'layer')[1]='F.Cu'
def fix_layers(n):
    if not isinstance(n,list):return
    if n and n[0]=='layers':n[:]=[q for q in n if q not in ['In1.Cu','In2.Cu']]
    for q in n:fix_layers(q)
fix_layers(s)
(OUT/'Matrix6.kicad_pcb').write_text(dump(s))
app=wx.App(False);b=p.LoadBoard(str(OUT/'Matrix6.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
mm=p.FromMM
def pt(at,y=None):
    if y is not None:at=(at,y)
    return p.VECTOR2I(mm(at[0]),mm(at[1]))
def xy(v):return tuple(round(p.ToMM(q),6) for q in (v.x,v.y))
nets={str(k):v for k,v in b.GetNetInfo().NetsByName().items()}
def net(n):return nets[n if n.startswith('/') else '/'+n]
def pad(ref,num):return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(num)).GetPosition())
removed=[]
def drop(t):removed.append(t);b.Remove(t)
def path(n,points,layer=p.F_Cu,width=.2):
    for a,c in zip(points,points[1:]):
        if a==c:continue
        t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(c));t.SetLayer(layer);t.SetWidth(mm(width));t.SetNet(net(n));b.Add(t)
def via(n,at):
    v=p.PCB_VIA(b);v.SetPosition(pt(at));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net(n));b.Add(v)

# Explicit relayering of branches with clear space on the rear.
for t in list(b.GetTracks()):
    if isinstance(t,p.PCB_VIA):continue
    n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd())
    inner=t.m_Uuid.AsString() in inner_ids
    if inner and n in ['/CC1','/CC2','/VBAT']:
        t.SetLayer(p.B_Cu)
    if inner and n=='/VSYS' and a in [(125.8,133.8),(124.5,135.1)]:t.SetLayer(p.B_Cu)
    if inner and n=='/EN' and a[0]==c[0]==99.3:t.SetLayer(p.B_Cu)
    if inner and n=='/IO0' and a in [(126.8,157.2),(103.0,157.2)]:drop(t)
    if n=='/IO48' and a in [(132.5,115.16),(132.5,141.2)]:t.SetLayer(p.B_Cu)
# End transitions and the button branch below the connector shell pads.
via('VSYS',(124.5,140.4))
via('EN',(99.3,148.18))
via('IO48',(132.5,115.16));via('IO48',(128.5,141.2))
path('IO0',[(126.8,157.2),(125.9,158.1),(125.9,160.1),(103,160.1),(103,145.64)],p.B_Cu,.25)
via('IO0',(103,145.64))
# The source-switch gate supply crosses VSYS on the rear at the drain.
for t in list(b.GetTracks()):
    if isinstance(t,p.PCB_VIA):continue
    if t.GetNetname()=='/VBUS_FUSED' and xy(t.GetStart()) in [(124.6,143.8),(130.5,144.3),(129,144.3)]:drop(t)
path('VBUS_FUSED',[(124.6,143.8),(125.9,143.8)],p.B_Cu,.4);via('VBUS_FUSED',(125.9,143.8))
path('VBUS_FUSED',[(125.9,143.8),(127,144.8)],p.F_Cu,.4)
path('VBUS_FUSED',[(130.5,144.3),(131.4,144.3),(131.4,145.8)],p.F_Cu,.4);via('VBUS_FUSED',(131.4,145.8))
path('VBUS_FUSED',[(131.4,145.8),(131.4,150.4),(129.7,150.4),(128.8,150.5)],p.B_Cu,.4)
# Mark the new narrow low-current charger branches consistently with v0.7.
g=next(g for g in b.Groups() if g.GetName()=='CHARGER_BRANCH')
for t in b.GetTracks():
    if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/VBUS_FUSED' and p.ToMM(t.GetWidth())<.8 and not t.GetParentGroup():g.AddItem(t)


exec((ROOT/'scripts/two_layer_routes.py').read_text())
from move_r8_for_branding import move_r8
move_r8(b)
from set_matrix_branding import apply_branding
apply_branding(b)
p.SaveBoard(str(OUT/'Matrix6.kicad_pcb'),b)
sch=(original('kicad_sch').replace('(rev "0.7")','(rev "0.8")')
     .replace('N8R8 / 3.3V GPIO / 4-layer PCB','N8R8 / 3.3V GPIO / 2-layer PCB')
     .replace('(date "2026-09-07")','(date "2026-09-08")'))
(OUT/'Matrix6.kicad_sch').write_text(sch)
dru=original('kicad_dru')
a=dru.index('(rule "L2 ground plane only"');z=dru.index('(rule "USB top layer without vias"')
dru='# Two-layer prototype: nominal 90-ohm coplanar USB; see electrical review.\n'+dru[z:]
dru=dru.replace('0.28mm','0.38mm').replace('0.50mm','0.20mm')
dru=dru.replace("A.memberOfGroup('USB_90OHM_TRUNK') && A.Origin_Y >= 122mm && A.End_Y <= 145.85mm","A.memberOfGroup('USB_90OHM_TRUNK') && A.Origin_Y >= 128mm && A.End_Y <= 142mm")
dru=dru.replace("A.fromTo('L1-2','U1-2')","A.fromTo('C2-1','U1-2')").replace("A.NetName == '/BUCK_SW'","(A.NetName == '/SW_L1' || A.NetName == '/SW_L2')")
dru=dru.replace("A.memberOfGroup('USB_90OHM_TRUNK') && B.NetName == '/GND'","(A.memberOfGroup('USB_90OHM_TRUNK') && B.NetName == '/GND') || (B.memberOfGroup('USB_90OHM_TRUNK') && A.NetName == '/GND')")
dru=dru.replace('diff_pair_gap (min 0.19mm) (opt 0.20mm) (max 0.21mm)','diff_pair_gap (min 0.17mm) (opt 0.18mm) (max 0.19mm)')
(OUT/'Matrix6.kicad_dru').write_text(dru)
pro=json.loads((OUT/'Matrix6.kicad_pro').read_text())
for c in pro['net_settings']['classes']:
    if c['name']=='USB':c['track_width']=.38;c['diff_pair_width']=.38;c['diff_pair_gap']=.18
(OUT/'Matrix6.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
print('Two-layer development board saved. Run DRC before review/export.')
