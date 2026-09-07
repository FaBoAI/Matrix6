"""Migrate the v0.4 snapshot using explicitly specified routes, without autorouting.

KiCad Python with pcbnew + wx is required. Rebuilds from the first git commit;
overwrites the working Matrix6 PCB and schematic. Save GUI edits before use.
"""
from pathlib import Path
import copy, json, math, os, subprocess, tempfile, uuid
from sexpr import *

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'hardware/Matrix6'
BASE_REV = 'ee580b181c5c248c455f0519c6c52200018bf0b3'
def original(ext):
    return subprocess.check_output(['git', 'show', f'{BASE_REV}:hardware/Matrix6/Matrix6.{ext}'], cwd=ROOT).decode()

H1 = ['+3V3','GND','EN','IO0'] + [f'IO{i}' for i in range(1,17)]
H2 = ['VBUS_FUSED','GND','IO17','IO18',None,None,'IO21','IO38','IO39','IO40','IO41','IO42','IO45','IO46','IO47','IO48','IO44_RX','IO43_TX','GND',None]
MAP = {'H1': H1, 'H2': H2}
sch = parse(original('kicad_sch'))
rootid = child(sch,'uuid')[1]
def uid(key): return str(uuid.uuid5(uuid.UUID(rootid), 'matrix6-v05-'+key))
def prop(s,k): return next(x for x in children(s,'property') if x[1]==k)
symbols = {prop(s,'Reference')[2]:s for s in children(sch,'symbol')}
for old,new in [('J2','H1'),('J3','H2')]:
    s = symbols[old]
    lib = next(x for x in children(child(sch,'lib_symbols'),'symbol') if x[1]==child(s,'lib_id')[1])
    sx,sy = map(float,child(s,'at')[1:3])
    for pin in [p for g in children(lib,'symbol') for p in children(g,'pin')]:
        n = int(child(pin,'number')[1]); px,py=map(float,child(pin,'at')[1:3]); point=(sx+px,sy-py)
        wire=next(w for w in children(sch,'wire') if any(math.dist(tuple(map(float,q[1:3])),point)<1e-4 for q in children(child(w,'pts'),'xy')))
        ends=[tuple(map(float,q[1:3])) for q in children(child(wire,'pts'),'xy')]
        label=next(l for l in children(sch,'label') if any(math.dist(tuple(map(float,child(l,'at')[1:3])),q)<1e-4 for q in ends))
        name=MAP[new][n-1]
        if name is None:
            sch.remove(wire); sch.remove(label)
            sch.append(parse(f'(no_connect (at {point[0]} {point[1]}) (uuid "{uid(new+str(n)+"nc")}"))'))
        else: label[1]=name
    prop(s,'Reference')[2]=new
    prop(s,'Value')[2]='Matrix5 '+new
    prop(s,'Footprint')[2]='Connector_PinSocket_2.54mm:PinSocket_1x20_P2.54mm_Vertical'
    inst=child(child(child(s,'instances'),'project'),'path'); child(inst,'reference')[1]=new
for s in children(sch,'symbol'):
    inst=child(s,'instances')
    if inst:
        for pr in children(inst,'project'):pr[1]='Matrix6'
child(child(sch,'title_block'),'title')[1]='Matrix6 - ESP32-S3 / Matrix5 shield interface'
child(child(sch,'title_block'),'rev')[1]='0.5'
for t in children(sch,'text'):
    t[1]={'03  2 x 20 GPIO HEADERS': '03  MATRIX5 SHIELD BUS: 2 x 20 / 33.02 mm', 'GPIO19/20: dedicated native USB D-/D+; no header stubs.': 'H2.5 / H2.6 / H2.20: NC (USB D-/D+ and VBAT are not exposed).', '3V3 header pins are OUTPUT ONLY. Use USB-C or regulated +5V header input.': 'H1.1 = 3V3 OUTPUT; H2.1 = fused USB VBUS OUTPUT. Power the board via USB-C.', '+5V header and USB may coexist: D1 blocks current back into USB VBUS.': 'Do not drive H2.1 from another supply: the fuse does not block backfeed into USB.', '3V3 budget: 500 mA total continuous, ambient 50 C. Verify prototype thermals and USB TDR.': '50 C budget: 3V3 500 mA total incl. MCU + VBUS shield 100 mA. Verify prototype thermals / USB TDR.'}.get(t[1],t[1])
(OUT/'Matrix6.kicad_sch').write_text(dump(sch))

import pcbnew as p, wx
app=wx.App(False)
tmp=Path(tempfile.mkdtemp(prefix='matrix6-source-'))/'baseline.kicad_pcb';tmp.write_text(original('kicad_pcb'));tmp.with_suffix('.kicad_pro').write_text(original('kicad_pro'));tmp.with_suffix('.kicad_dru').write_text(original('kicad_dru'))
b=p.LoadBoard(str(tmp)); b.SetFileName(str(OUT/'Matrix6.kicad_pcb'))
mm=p.FromMM
def pt(x,y=None):
    if y is None:x,y=x
    return p.VECTOR2I(mm(x),mm(y))
def xy(v):return tuple(round(p.ToMM(q),6) for q in (v.x,v.y))
fps={f.GetReference():f for f in b.GetFootprints()}; removed=[]
def drop(t):removed.append(t);b.Remove(t)
nets={str(k):v for k,v in b.GetNetInfo().NetsByName().items()}
def net(name):
    n=name if name.startswith('unconnected-') else '/'+name
    if n not in nets:nets[n]=p.NETINFO_ITEM(b,n);b.Add(nets[n])
    return nets[n]
def pad(ref,n):return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(n)).GetPosition())
def path(name,points,layer=p.B_Cu,width=.20):
    for a,c in zip(points,points[1:]):
        if a==c:continue
        t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(c));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(net(name));b.Add(t)
def via(name,at,size=.6,drill=.3):
    v=p.PCB_VIA(b);v.SetPosition(pt(at));v.SetWidth(mm(size));v.SetDrill(mm(drill));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net(name));b.Add(v)
LIB=Path(os.environ.get('KICAD_FOOTPRINT_DIR','/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'))
for old,new,x in [('J2','H1',101.27),('J3','H2',134.29)]:
    f0=fps[old];f=p.FootprintLoad(str(LIB/'Connector_PinSocket_2.54mm.pretty'),'PinSocket_1x20_P2.54mm_Vertical');b.Add(f)
    f.SetReference(new);f.SetValue('Matrix5 '+new);f.SetFPID(p.LIB_ID('Connector_PinSocket_2.54mm','PinSocket_1x20_P2.54mm_Vertical'))
    f.SetPath(f0.GetPath());f.SetPosition(pt(x,153.26));f.SetOrientationDegrees(180)
    for q in f.Pads():
        n=int(q.GetNumber());name=MAP[new][n-1]
        q.SetNet(net(name if name else f'unconnected-({new}-Pin_{n}-Pad{n})'));q.SetPinType('passive' if name else 'no_connect')
    f.Value().SetVisible(False);f.Reference().SetVisible(True);f.Reference().SetPosition(pt(x,156.0));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));f.Reference().SetTextSize(pt(.8,.8));f.Reference().SetTextThickness(mm(.12))
    drop(f0);del fps[old];fps[new]=f

# Remove old GPIO routing, keeping the short module pad escapes and EN RC network.
fanouts={}
for t in list(b.GetTracks()):
    name=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd())
    if name.startswith('/IO') or name=='/EN':
        if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu:
            if name=='/EN':continue
            if (a[0] in [109.03,126.53] and a[1]<119) or (a[1]==119 and c[1]==120):
                fanouts[name[1:]]=c;continue
            if name=='/IO0' and a in [(122.325,123),(126.8,158)]:continue
        if isinstance(t,p.PCB_VIA) and (a in [(108.1,103.78),(105.8,156.5),(121.9,123.8),(126.8,157)]):continue
        drop(t)

# Remove obsolete header power branches; the regulator and USB remain in place.
for t in list(b.GetTracks()):
    if isinstance(t,p.PCB_VIA):continue
    n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());la=t.GetLayer()
    if n=='/+3V3' and la==p.B_Cu:
        if a in [(104.5,102.3),(108.1,102.51),(107.7,102.3),(102.54,104.26),(100.8,105),(100.8,146.3),(101.4,146.9),(103.7,146.9),(120.58,148.18)] or c in [(133.02,148.18),(120.58,148.18)]:drop(t)
    if n=='/+5V' and la==p.In2_Cu and (max(a[0],c[0])>129 or min(a[0],c[0])<=114.2):drop(t)

# Extend board width symmetrically, maintaining the USB and antenna locations.
for d in b.GetDrawings():
    if d.GetLayer()==p.Edge_Cuts:
        for getter,setter in [('GetStart','SetStart'),('GetEnd','SetEnd')]:
            x,y=xy(getattr(d,getter)());x={100:97.46,135.56:138.10}.get(x,x);getattr(d,setter)(pt(x,y))
for z in b.Zones():
    if z.GetIsRuleArea():continue
    poly=z.Outline()
    for i in range(poly.OutlineCount()):
        line=poly.Outline(i)
        for j in range(line.PointCount()):
            q=line.CPoint(j);x,y=xy(q)
            if x in [100.35,135.21]:line.SetPoint(j,pt({100.35:97.81,135.21:137.75}[x],y))

# Move two ground stitching vias away from the new signal exits.
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA) and t.GetNetname()=='/GND':
        at=xy(t.GetPosition())
        if at==(107.0,121.0):t.SetPosition(pt(108.7,120.2))
        if at==(107.0,125.0):t.SetPosition(pt(108.7,126.0))

# Module IO15/16/17/18 escape inward, leaving room for the reversed header order.
for name,new_at in [('IO15',(110.7,110.13)),('IO16',(111.4,111.4)),('IO17',(124.5,113.89)),('IO18',(124.5,116.43))]:
    for t in list(b.GetTracks()):
        if t.GetNetname()=='/'+name:drop(t)
    source=next(xy(q.GetPosition()) for q in fps['U1'].Pads() if q.GetNetname()=='/'+name)
    points=[source,new_at]
    if name=='IO17':points=[source,(109.31,112.95),(123.56,112.95),new_at]
    if name=='IO18':points=[source,(120,113.94),(121,114.94),(121,115.43),(122,116.43),new_at]
    path(name,points,p.F_Cu,.25);fanouts[name]=new_at
for name,at in fanouts.items():via(name,at)

# Left column: explicit lane assignments. L2 is never used for signals.
for name,lane,source_y,pin in [('IO1',102.6,104.4,5),('IO2',103.25,108.22,6)]:
    s=fanouts[name];points=[s,(110,102.51),(110,104.4),(lane,source_y)] if name=='IO1' else [s,(112.2,103.78),(112.2,108.22),(lane,source_y)];path(name,points,p.In2_Cu);via(name,(lane,source_y))
    y=pad('H1',pin)[1];path(name,[(lane,source_y),(lane,y)]);via(name,(lane,y));path(name,[(lane,y),pad('H1',pin)],p.In2_Cu)
for name,lane,pin in [('IO4',103.95,8),('IO5',104.65,9),('IO6',105.35,10),('IO7',106.5,11),('IO8',107.85,12)]:
    s=fanouts[name];y=pad('H1',pin)[1];path(name,[s,(lane,s[1]),(lane,y)]);via(name,(lane,y));path(name,[(lane,y),pad('H1',pin)],p.In2_Cu)
for name,pin in [('IO3',7),('IO9',13),('IO10',14),('IO11',15),('IO12',16),('IO13',17)]:
    s=fanouts[name];y={'IO10':120.9,'IO12':114.57,'IO13':112.1,'IO15':106.96,'IO16':105.7}.get(name,pad('H1',pin)[1]);path(name,[s,(s[0],y)]);via(name,(s[0],y));path(name,[(s[0],y),(103.0,y),pad('H1',pin)],p.In2_Cu)
path('IO14',[fanouts['IO14'],(119.685,111.0)]);via('IO14',(119.685,111.0));path('IO14',[(119.685,111.0),(112.5,111.0),(112.2,110.7),(110.9,110.7),(110.9,111.0),(103.0,111.0),pad('H1',18)],p.In2_Cu)
for name,pin in [('IO15',19),('IO16',20)]:
    s=fanouts[name];y={'IO10':120.9,'IO12':114.57,'IO13':112.1,'IO15':106.96,'IO16':105.7}.get(name,pad('H1',pin)[1]);path(name,[s,(s[0],y)]);via(name,(s[0],y));path(name,[(s[0],y),(103.0,y),pad('H1',pin)],p.In2_Cu)

# Right column: nested source fan-outs on B.Cu and separate horizontal exits.
for name,lane,pin in [('IO38',128.4,8),('IO39',129.3,9),('IO40',130.0,10),('IO41',130.7,11),('IO42',131.4,12),('IO44_RX',132.1,17),('IO43_TX',132.8,18)]:
    s=fanouts[name];y=pad('H2',pin)[1];path(name,[s,(lane,s[1]),(lane,y)]);via(name,(lane,y));path(name,[(lane,y),pad('H2',pin)],p.In2_Cu)
for name,lane,pin in [('IO17',136.2,3),('IO18',135.5,4)]:
    s=fanouts[name];y=pad('H2',pin)[1];path(name,[s,(lane,s[1])],p.In2_Cu);via(name,(lane,s[1]));path(name,[(lane,s[1]),(lane,y)]);via(name,(lane,y));path(name,[(lane,y),pad('H2',pin)],p.In2_Cu)
path('IO45',[fanouts['IO45'],(125.0,120),(125.0,122.78)]);via('IO45',(125.0,122.78));path('IO45',[(125.0,122.78),pad('H2',13)],p.In2_Cu)
for t in list(b.GetTracks()):
    if t.GetNetname()=='/IO46':drop(t)
path('IO46',[pad('U1',16),(112.065,122.1),(126.5,122.1)],p.F_Cu,.25);via('IO46',(126.5,122.1));path('IO46',[(126.5,122.1),(132.43,122.1),pad('H2',14)],p.In2_Cu)
path('IO47',[fanouts['IO47'],(122.225,118.55)]);via('IO47',(122.225,118.55));path('IO47',[(122.225,118.55),(133.44,118.55),pad('H2',15)],p.In2_Cu)
path('IO48',[fanouts['IO48'],(123.495,115.16)]);via('IO48',(123.495,115.16));path('IO48',[(123.495,115.16),pad('H2',16)],p.In2_Cu)
path('IO48',[fanouts['IO48'],(123.495,124)]);via('IO48',(123.495,124));path('IO48',[(123.495,124),(127.1,124)],p.In2_Cu);via('IO48',(127.1,124));path('IO48',[(127.1,124),(127.1,139.8),(128.5,141.2)]);via('IO48',(128.5,141.2));path('IO48',[(128.5,141.2),pad('R10',1)],p.F_Cu,.25)
path('IO21',[fanouts['IO21'],(120.955,126)]);via('IO21',(120.955,126));path('IO21',[(120.955,126),(126,126)],p.In2_Cu);via('IO21',(126,126));path('IO21',[(126,126),(125.25,126.75),(125.25,136.1)]);via('IO21',(125.25,136.1));path('IO21',[(125.25,136.1),(130,136.1),(131.92,138.02),pad('H2',7)],p.In2_Cu)

# EN and BOOT retain both the module pull network and the USB-adjacent buttons.
path('EN',[(108.1,103.78),(99.3,103.78)]);via('EN',(99.3,103.78));path('EN',[(99.3,103.78),(99.3,156.5)],p.In2_Cu,.25);via('EN',(99.3,156.5));path('EN',[(99.3,156.5),(105.8,156.5)],p.B_Cu,.25);path('EN',[(99.3,148.18),pad('H1',3)],p.In2_Cu,.25)
path('IO0',[fanouts['IO0'],(127.8,118.15),(127.8,123.6)]);via('IO0',(127.8,123.6));path('IO0',[(127.8,123.6),(127.8,125.0),(109.5,125.0)],p.In2_Cu,.25);path('IO0',[(121.9,123.8),(121.9,125.0)],p.In2_Cu,.25);via('IO0',(109.5,125.0));path('IO0',[(109.5,125.0),(109.5,145.64)]);via('IO0',(109.5,145.64));path('IO0',[(109.5,145.64),pad('H1',4)],p.In2_Cu,.25)
path('IO0',[(126.8,157),(126.8,157.2),(103.0,157.2),(103.0,145.64),pad('H1',4)],p.In2_Cu,.25)
path('IO46',[pad('R8',1),(107.675,123.3),(108.6,122.375),(108.6,122.1),(112.065,122.1)],p.F_Cu,.25)
path('IO45',[pad('R7',1),(121.475,127.2)],p.F_Cu,.25);via('IO45',(121.475,127.2));path('IO45',[(121.475,127.2),(124.2,127.2),(124.2,122.78)]);via('IO45',(124.2,122.78));path('IO45',[(124.2,122.78),(125,122.78)],p.In2_Cu)

# 3V3 at H1.1; fused USB VBUS (before the buck input diode) at H2.1.
path('+3V3',[(108.1,102.51),(107.7,102.3),(104.5,102.3)],p.B_Cu,.6);path('+3V3',[(104.5,102.3),(98.3,102.3),(98.3,153.26),pad('H1',1)],p.B_Cu,.8)
path('+3V3',[(103.7,146.9),(103.7,154.9),(98.3,154.9),(98.3,153.26)],p.B_Cu,.8)
via('VBUS_FUSED',(128.8,150.5));path('VBUS_FUSED',[pad('F1',2),(128.8,150.5)],p.F_Cu,.8);path('VBUS_FUSED',[(128.8,150.5),(131.55,153.26),pad('H2',1)],p.B_Cu,.8)

for d in list(b.GetDrawings()):
    if isinstance(d,p.PCB_TEXT):
        x,y=xy(d.GetPosition())
        if d.GetLayer()==p.B_SilkS and x in [105.4,130.1]:drop(d)
        elif d.GetText()=='S3 DEV':d.SetText('MATRIX6')
        elif d.GetText()=='N8R8  v0.4':d.SetText('N8R8  v0.5')
for ref,x in [('H1',104.1),('H2',131.45)]:
    for i,name in enumerate(MAP[ref],1):
        label={'VBUS_FUSED':'VBUS','+3V3':'3V3','IO44_RX':'44R','IO43_TX':'43T'}.get(name,name or 'NC')
        if label.startswith('IO'):label=label[2:]
        t=p.PCB_TEXT(b);t.SetText(label);t.SetPosition(pt(x,pad(ref,i)[1]));t.SetLayer(p.B_SilkS);t.SetMirrored(True);t.SetTextSize(pt(.8,.8));t.SetTextThickness(mm(.12));b.Add(t)
b.GetTitleBlock().SetTitle('Matrix6 - ESP32-S3 / Matrix5 shield interface');b.GetTitleBlock().SetRevision('0.5')
p.SaveBoard(str(OUT/'Matrix6.kicad_pcb'),b)
pro=json.loads(original('kicad_pro'));pro['meta']['filename']='Matrix6.kicad_pro'
for sh in pro.get('schematic',{}).get('top_level_sheets',[]):sh['filename']='Matrix6.kicad_sch';sh['name']='Matrix6'
(OUT/'Matrix6.kicad_pro').write_text(json.dumps(pro,indent=2)+'\n')
print('Matrix6 v0.5 manual routing saved')
