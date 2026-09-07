"""Build v0.6 from the archived v0.5 CAD using explicit placements/routes.

No route finding or autorouter is used. Save KiCad GUI edits before running.
The source commit is immutable; reruns deliberately replace this revision.
"""
from pathlib import Path
import copy, json, math, subprocess, tempfile, uuid
from sexpr import *
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'hardware/Matrix6'
BASE='537006a'
SUPPORT=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
def original(ext):
    return subprocess.check_output(['git','show',f'{BASE}:hardware/Matrix6/Matrix6.{ext}'],cwd=ROOT).decode()
sch=parse(original('kicad_sch')); rootid=child(sch,'uuid')[1]
def uid(s):return str(uuid.uuid5(uuid.UUID(rootid),'matrix-six-v06-'+s))
def prop(s,k):return next((q for q in children(s,'property') if q[1]==k),None)
libs=child(sch,'lib_symbols')
def loadlib(libid):
    existing=next((s for s in children(libs,'symbol') if s[1]==libid),None)
    if existing:return existing
    lib,name=libid.split(':'); allsym=children(parse((SUPPORT/'symbols'/f'{lib}.kicad_sym').read_text()),'symbol')
    def resolve(name):
        s=copy.deepcopy(next(q for q in allsym if q[1]==name)); ext=child(s,'extends')
        if ext:
            parent=resolve(ext[1]); oldname=parent[1]
            for q in children(parent,'symbol'):q[1]=q[1].replace(oldname+'_',name+'_',1)
            for q in children(s,'property'):
                old=prop(parent,q[1])
                if old:parent.remove(old)
                parent.append(q)
            parent[1]=name;s=parent
        return s
    s=resolve(name);s[1]=libid;libs.append(s);return s
def pins(lib):return [p for g in children(lib,'symbol') for p in children(g,'pin')]
def point(s,p):
    x,y=map(float,child(s,'at')[1:3]);px,py=map(float,child(p,'at')[1:3]);return (round(x+px,5),round(y-py,5))
def remove_symbol(ref):
    s=next((q for q in children(sch,'symbol') if prop(q,'Reference')[2]==ref),None)
    if not s:return
    for pin in pins(loadlib(child(s,'lib_id')[1])):
        at=point(s,pin)
        for w in list(children(sch,'wire')):
            ends=[tuple(map(float,q[1:3])) for q in children(child(w,'pts'),'xy')]
            if any(math.dist(at,q)<1e-4 for q in ends):
                sch.remove(w)
                for l in list(children(sch,'label')):
                    if any(math.dist(tuple(map(float,child(l,'at')[1:3])),q)<1e-4 for q in ends):sch.remove(l)
        for n in list(children(sch,'no_connect')):
            if math.dist(at,tuple(map(float,child(n,'at')[1:3])))<1e-4:sch.remove(n)
    sch.remove(s)
def wirelabel(at,angle,name,key,length=5.08):
    if name is None:
        sch.append(parse(f'(no_connect (at {at[0]} {at[1]}) (uuid "{uid(key+"nc")}"))'));return
    a=math.radians(angle);end=(round(at[0]-length*math.cos(a),5),round(at[1]+length*math.sin(a),5))
    sch.append(parse(f'(wire (pts (xy {at[0]} {at[1]}) (xy {end[0]} {end[1]})) (stroke (width 0) (type default)) (uuid "{uid(key+"wire")}"))'))
    sch.append(parse(f'(label {json.dumps(name)} (at {end[0]} {end[1]} 0) (effects (font (size 1 1))) (uuid "{uid(key+"label")}"))'))
parts={}
def part(ref,libid,value,fp,at,nets,pcb,mpn='',lcsc=''):
    remove_symbol(ref);lib=loadlib(libid);x,y=at
    s=parse(f'(symbol (lib_id "{libid}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid(ref)}"))')
    # Reference/value positions follow the symbol library, with long MPN hidden separately.
    for key,val in [('Reference',ref),('Value',value),('Footprint',fp),('MPN',mpn),('LCSC',lcsc)]:
        old=prop(lib,key); px,py=(map(float,child(old,'at')[1:3]) if old else (0,0))
        if key in ['Reference','Value']:
            effects=copy.deepcopy(child(old,'effects')) if old else parse('(effects (font (size 1.27 1.27)))')
            child(child(effects,'font'),'size')[1:]=[A(1.05),A(1.05)]
            s.append(node('property',key,val,node('at',A(x+px),A(y-py),A(0)),effects))
        else:s.append(parse(f'(property "{key}" {json.dumps(val)} (at {x} {y} 0) (effects (font (size 1 1)) (hide yes)))'))
    seen=set()
    for p in pins(lib):
        n=str(child(p,'number')[1]);s.append(parse(f'(pin "{n}" (uuid "{uid(ref+"-pin"+n)}"))'))
        pos=point(s,p)
        if pos not in seen:wirelabel(pos,float(child(p,'at')[3]),nets[n],ref+'-'+n)
        seen.add(pos)
    s.append(parse(f'(instances (project "Matrix6" (path "/{rootid}" (reference "{ref}") (unit 1))))'))
    sch.append(s);parts[ref]={'symbol':s,'lib':lib,'fp':fp,'nets':nets,'pcb':pcb,'value':value,'mpn':mpn,'lcsc':lcsc}
C='Capacitor_SMD:C_0805_2012Metric';C6='Capacitor_SMD:C_0603_1608Metric';R='Resistor_SMD:R_0603_1608Metric'
part('U2','Regulator_Switching:TPS63001','TPS63001 (3.3V)','Package_SON:Texas_DRC0010J',(101.6,149.86),dict(zip(map(str,range(1,12)),['+3V3','SW_L2','GND','SW_L1','VSYS','VSYS','GND','VINA','GND','+3V3','GND'])),(121.5,138,0,'F'),'TPS63001DRCR','C28060')
part('L1','Device:L','2.2uH / 3A','Inductor_SMD:L_Bourns-SRN4018',(55.88,152.4),{'1':'SW_L1','2':'SW_L2'},(116.9,138,90,'F'),'SRN4018-2R2M','C913207')
for ref,at,net,pcb in [('C1',(25.4,149.86),'VSYS',(120.4,142.2,180,'F')),('C2',(139.7,147.32),'+3V3',(118.6,132.8,0,'F')),('C8',(160.02,147.32),'+3V3',(121.5,144.8,0,'F'))]:
    part(ref,'Device:C','22uF 25V X5R',C,at,{'1':net,'2':'GND'},pcb,'CL21A226MAQNNNE','C45783')
part('C7','Device:C','100nF',C6,(53.34,180.34),{'1':'VINA','2':'GND'},(125.3,135.4,0,'F'))
part('R7','Device:R','10k',R,(256.54,139.7),{'1':'IO45','2':'GND'},(122,128.8,90,'F'),'0603WAF1002T5E','C25804')
part('R12','Device:R','100R',R,(25.4,180.34),{'1':'VSYS','2':'VINA'},(125.7,140,90,'F'),'0603WAF1000T5E','C22775')
part('U4','Battery_Management:MCP73831-2-OT','MCP73831 / 100mA','Package_TO_SOT_SMD:SOT-23-5',(220.98,215.9),{'1':None,'2':'GND','3':'VBAT','4':'VBUS_FUSED','5':'CHG_PROG'},(128.5,147,0,'B'),'MCP73831T-2ACI/OT','C424093')
part('Q1','Transistor_FET:AO3401A','AO3401A','Package_TO_SOT_SMD:SOT-23',(289.56,213.36),{'1':'VBUS_FUSED','2':'VSYS','3':'VBAT'},(123.0,146.0,0,'B'),'AO3401A','C15127')
part('J3','Connector_Generic:Conn_01x02','LiPo 1S / PH2','Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal',(363.22,213.36),{'1':'VBAT','2':'GND'},(108.5,153.5,0,'B'),'S2B-PH-K-S(LF)(SN)','C173752')
part('R13','Device:R','10k / 100mA',R,(193.04,246.38),{'1':'CHG_PROG','2':'GND'},(128.5,143.5,90,'B'),'0603WAF1002T5E','C25804')
part('R14','Device:R','100k',R,(317.5,215.9),{'1':'VBUS_FUSED','2':'GND'},(130.5,142.5,90,'B'),'0603WAF1003T5E','C25803')
for ref,at,net,pcb in [('C9',(185.42,213.36),'VBUS_FUSED',(129.5,151.6,180,'B')),('C10',(259.08,213.36),'VBAT',(129.7,154.8,0,'B'))]:
    part(ref,'Device:C','22uF 25V X5R',C,at,{'1':net,'2':'GND'},pcb,'CL21A226MAQNNNE','C45783')
part('J2','Connector:Micro_SD_Card_Det_Hirose_DM3AT','microSD (rear)','Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5',(149.86,241.3),{'1':'SD_DAT2','2':'IO10','3':'IO11','4':'+3V3','5':'IO12','6':'GND','7':'IO13','8':'SD_DAT1','9':None,'10':None,'SH':'GND'},(117.8,132.0,180,'B'),'DM3AT-SF-PEJM5','C114218')
for i,(net,x,px) in enumerate([('SD_DAT2',25.4,115.025),('IO10',45.72,116.125),('IO11',66.04,117.225),('IO13',86.36,121.625),('SD_DAT1',106.68,122.725)],15):
    part(f'R{i}','Device:R','10k',R,(x,218.44),{'1':net,'2':'+3V3'},((120.6,142.7,-90,'B') if i==15 else (117.5,130.4,0,'F') if i==19 else (111.0+2*(i-15),128.0,-90,'F')),'0603WAF1002T5E','C25804')
part('C11','Device:C','22uF 25V X5R',C,(25.4,246.38),{'1':'+3V3','2':'GND'},(105.8,141.2,90,'B'),'CL21A226MAQNNNE','C45783')
part('C12','Device:C','100nF',C6,(83.82,246.38),{'1':'+3V3','2':'GND'},(117.275,142.4,-90,'B'))
remove_symbol('#FLG04')
part('#FLG05','power:PWR_FLAG','PWR_FLAG','',(76.2,180.34),{'1':'VINA'},None)
part('#FLG06','power:PWR_FLAG','PWR_FLAG','',(124.46,180.34),{'1':'VBUS_FUSED'},None)
# Rename old power labels and attach the Matrix5 battery bus pin.
for l in children(sch,'label'):
    if l[1]=='+5V':l[1]='VSYS'
h2=next(s for s in children(sch,'symbol') if prop(s,'Reference')[2]=='H2')
p20=next(p for p in pins(loadlib(child(h2,'lib_id')[1])) if child(p,'number')[1]=='20');at=point(h2,p20)
for n in list(children(sch,'no_connect')):
    if math.dist(at,tuple(map(float,child(n,'at')[1:3])))<1e-4:sch.remove(n)
wirelabel(at,float(child(p20,'at')[3]),'VBAT','H2-20')
for t in list(children(sch,'text')):
    x,y=map(float,child(t,'at')[1:3])
    if y>=200:sch.remove(t)
    elif t[1].startswith('04 '):t[1]='04  USB / BATTERY TO REGULATED 3.3V'
def note(text,x,y,size=1.2):sch.append(parse(f'(text {json.dumps(text)} (at {x} {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid "{uid(text)}"))'))
note('07  REAR microSD / MATRIX5 SPI',17.78,198.12,1.8)
note('08  1S LiPo / USB CHARGING / AUTOMATIC SOURCE SELECTION',177.8,190.5,1.8)
note('J3: pin 1 = BAT+, pin 2 = GND. Use a protected 3.7V / 4.2V pack.',208.28,238.76)
note('100mA charge; >=500mAh, >=1A discharge. No cell temperature sensor.',208.28,243.84)
note('H2.20 = VBAT. H2.1 = fused USB output; no 5V output on battery.',208.28,248.92)
note('SD: CS=10, MOSI=11, CLK=12, MISO=13; 20MHz maximum bring-up.',17.78,266.7)
note('SD shares shield SPI pins. Remove card for conflicting GPIO / I2C use.',17.78,271.78)
note('3V3 budget: 500mA total including MCU, SD and shields. Prototype load / thermal / USB TDR tests required.',17.78,276.86)
note('Designed By GPT-6 Astra',17.78,281.94)
# Position new fields beside passives, keeping symbol bodies and labels readable.
for ref,d in parts.items():
    sym=d['symbol'];libid=child(sym,'lib_id')[1];x,y=map(float,child(sym,'at')[1:3])
    if libid in ['Device:R','Device:C','Device:L','Transistor_FET:AO3401A']:
        for key,dy in [('Reference',-1.27),('Value',1.27)]:
            q=prop(sym,key);child(q,'at')[1:]=[A(x+(4.5 if libid.startswith('Transistor') else 2.54)),A(y+dy),A(0)]
            effects=child(q,'effects');j=child(effects,'justify')
            if j:effects.remove(j)
            effects.append(node('justify',A('left')))
for ref,n,x in [('#FLG01','VBUS',95.25),('#FLG02','VSYS',111.76),('#FLG03','GND',128.27),('#FLG05','VINA',144.78),('#FLG06','VBUS_FUSED',161.29)]:
    part(ref,'power:PWR_FLAG','PWR_FLAG','',(x,190.5),{'1':n},None)
    for key in ['Reference','Value']:
        effects=child(prop(parts[ref]['symbol'],key),'effects')
        if not child(effects,'hide'):effects.append(node('hide',A('yes')))
note('SD opening faces the antenna edge. Keep rear card withdrawal corridor clear.',17.78,261.62)
title=child(sch,'title_block');child(title,'title')[1]='Matrix Six - ESP32-S3 / microSD / LiPo';child(title,'rev')[1]='0.6'
(OUT/'Matrix6.kicad_sch').write_text(dump(sch))

import pcbnew as p, wx
app=wx.App(False);tmp=Path(tempfile.mkdtemp(prefix='matrix-six-v06-'))/'Matrix6.kicad_pcb';tmp.write_text(original('kicad_pcb'));tmp.with_suffix('.kicad_pro').write_text(original('kicad_pro'));tmp.with_suffix('.kicad_dru').write_text(original('kicad_dru'))
b=p.LoadBoard(str(tmp));b.SetFileName(str(OUT/'Matrix6.kicad_pcb'));mm=p.FromMM
def pt(x,y=None):
    if y is None:x,y=x
    return p.VECTOR2I(mm(x),mm(y))
def xy(v):return (round(p.ToMM(v.x),6),round(p.ToMM(v.y),6))
fps={f.GetReference():f for f in b.GetFootprints()};dead=[]
def drop(q):dead.append(q);b.Remove(q)
nets={str(k):v for k,v in b.GetNetInfo().NetsByName().items()}
def net(n):
    n=n if n.startswith('unconnected-') else '/'+n
    if n not in nets:nets[n]=p.NETINFO_ITEM(b,n);b.Add(nets[n])
    return nets[n]
def pad(ref,num):return xy(next(q for q in fps[ref].Pads() if q.GetNumber()==str(num)).GetPosition())
def path(n,points,layer=p.F_Cu,width=.25):
    for a,c in zip(points,points[1:]):
        if a==c:continue
        t=p.PCB_TRACK(b);t.SetStart(pt(a));t.SetEnd(pt(c));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(net(n));b.Add(t)
def via(n,at,size=.6,drill=.3):
    v=p.PCB_VIA(b);v.SetPosition(pt(at));v.SetWidth(mm(size));v.SetDrill(mm(drill));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net(n));b.Add(v)
# Remove only the superseded converter copper. USB copper is never touched.
for t in list(b.GetTracks()):
    n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd())
    if n in ['/+5V','/BUCK_SW','/BUCK_BST']:drop(t)
    elif n=='/+3V3' and t.GetLayer()==p.F_Cu and min(a[0],c[0])>113 and min(a[1],c[1])>133:
        if isinstance(t,p.PCB_VIA) and a in [(119.3,145.5),(118.6,145.5)]:continue
        drop(t)
    elif n=='/GND' and 114.5<min(a[0],c[0]) and max(a[0],c[0])<125.2 and 134<min(a[1],c[1]) and max(a[1],c[1])<144:drop(t)
for ref,d in parts.items():
    if d['pcb'] is None:continue
    old=fps.get(ref)
    if old:drop(old)
    lib,name=d['fp'].split(':');f=p.FootprintLoad(str(SUPPORT/'footprints'/f'{lib}.pretty'),name);b.Add(f)
    f.SetReference(ref);f.SetValue(d['value']);f.SetFields({'MPN':d['mpn'],'LCSC':d['lcsc']});f.SetFPID(p.LIB_ID(lib,name));f.SetPosition(pt(d['pcb'][:2]));f.SetOrientationDegrees(d['pcb'][2])
    if d['pcb'][3]=='B':f.Flip(f.GetPosition(),p.FLIP_DIRECTION_LEFT_RIGHT)
    kp=p.KIID_PATH();kp.push_back(p.KIID(rootid));kp.push_back(p.KIID(uid(ref)));f.SetPath(kp)
    pp={str(child(q,'number')[1]):q for q in pins(d['lib'])}
    for q in f.Pads():
        n=q.GetNumber()
        if not n:continue
        sn=n
        val=d['nets'][sn];q.SetNet(net(val if val is not None else f'unconnected-({ref}-{child(pp[sn],"name")[1]}-Pad{n})'))
        if val is None:q.SetPinType('no_connect')
        else:q.SetPinType(str(pp[sn][1]));q.SetPinFunction(str(child(pp[sn],'name')[1]))

    for field in f.GetFields():field.SetVisible(False)
    f.Value().SetVisible(False);f.Reference().SetVisible(False);f.Reference().SetTextSize(pt(.8,.8));f.Reference().SetTextThickness(mm(.1));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
    fps[ref]=f
for q in fps['D1'].Pads():
    if q.GetNumber()=='1':q.SetNet(net('VSYS'))
for q in fps['H2'].Pads():
    if q.GetNumber()=='20':q.SetNet(net('VBAT'));q.SetPinType('passive')

# Explicit converter switch loops: both switching nets remain on F.Cu.
path('SW_L1',[pad('U2',4),(119.65,138.5),(118.625,139.525),pad('L1',1)],width=.3)
path('SW_L2',[pad('U2',2),(119.65,137.5),(118.625,136.475),pad('L1',2)],width=.3)
path('VSYS',[pad('U2',5),(120.1,139.5)],width=.3);path('VSYS',[(120.1,139.5),(120.1,139.7),(121.35,140.95),pad('C1',1)],width=.6)
path('+3V3',[pad('U2',1),(120.1,136.8),(119.8,136.5),(119.8,135.1),(117.65,135.1),pad('C2',1)],width=.3)
path('+3V3',[pad('C2',1),(117.65,131.5),(119.5,131.5),(122.0,131.5),(122.0,133.9)],width=.6)
path('+3V3',[pad('U2',10),(122.9,134.8),(122.0,133.9),(122.0,131.5)],width=.25)
via('+3V3',pad('C2',1));path('+3V3',[pad('C2',1),(117.65,131.5),(122.1,131.5),(122.1,133.5)],p.In2_Cu,.8);via('+3V3',(122.1,133.5));path('+3V3',[(122.1,133.5),(122.1,135.5),(123.6,137.0),(123.6,141.6),(122.4,142.8),(121.3,143.9),(120,143.8),(119.3,144.5),(119.3,145.5)],p.B_Cu,.8)
via('VSYS',(122,141.4));path('VSYS',[pad('C1',1),(122,141.4)],width=.6)
path('VSYS',[pad('D1',1),(125.8,133.5),(125.8,133.8)],width=.6);via('VSYS',(125.8,133.8))
path('VSYS',[(125.8,133.8),(124.5,135.1),(124.5,140.4),(123.5,141.4),(122,141.4)],p.In2_Cu,.8)
path('VSYS',[pad('U2',6),(122.7,139.2),(125.0,141.5)],width=.25);via('VSYS',(125.0,141.5))
path('VSYS',[(125.0,141.5),(125,142.2),(122,142.2),(122,141.4)],p.In2_Cu,1.2)
path('VSYS',[pad('R12',1),(125.7,142.5)],width=.3);path('VSYS',[(125.7,142.5),(125.0,141.5)],width=.6)
path('VINA',[pad('R12',2),(124.5,139.175),(124.5,136.075),pad('C7',1)],width=.25)
path('VINA',[pad('U2',8),(124.5,138)],width=.25)
for num in [3,7,9]:
    a=pad('U2',num);path('GND',[a,(121.5,a[1])],width=.25)
for at in [(121.2,137.6),(121.8,138.4)]:via('GND',at)
for ref,num,at in [('C1',2,(119.4,143.1)),('C2',2,(120.3,132.8)),('C8',2,(122.45,144.8)),('C7',2,(126.075,135.4))]:
    path('GND',[pad(ref,num),at],width=.25);via('GND',at)

via('+3V3',pad('C8',1));path('+3V3',[(120,143.8),(120.55,144.35),pad('C8',1)],p.B_Cu,.6)
# The remaining explicitly planned rear routes are in a separate file so that
# review/fix iterations do not obscure the schematic and placement definitions.
routefile=ROOT/'scripts/matrix_six_rear_routes.py'
if routefile.exists():exec(compile(routefile.read_text(),str(routefile),'exec'))
for t in list(b.GetDrawings()):
    if not isinstance(t,p.PCB_TEXT):continue
    if t.GetText()=='MATRIX6':t.SetText('Matrix Six');t.SetPosition(pt(116.4,124.0));t.SetTextSize(pt(1.1,1.1))
    elif t.GetText()=='N8R8  v0.5':drop(t)
    elif t.GetText()=='Designed By GPT-6 Astra':t.SetLayer(p.B_SilkS);t.SetMirrored(True);t.SetPosition(pt(117.8,102.5));t.SetTextSize(pt(.8,.8))
    elif t.GetLayer()==p.B_SilkS and t.GetText() in ['N8R8 / USB-JTAG','ESP32-S3','3V3 GPIO ONLY']:drop(t)
    elif t.GetLayer()==p.B_SilkS and xy(t.GetPosition())==(131.449999,105.0):t.SetText('BAT')
    elif t.GetLayer()==p.B_SilkS and xy(t.GetPosition())==(104.1,153.26):t.SetPosition(pt(102.9,154.65))
    elif t.GetLayer()==p.B_SilkS and xy(t.GetPosition())==(131.449999,150.72):t.SetPosition(pt(131.45,149.5))
    elif t.GetLayer()==p.B_SilkS and xy(t.GetPosition())==(131.449999,143.1):t.SetPosition(pt(132,143.1))
def silk(s,at,layer=p.B_SilkS,size=.8):
    t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(pt(at));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);t.SetTextSize(pt(size,size));t.SetTextThickness(mm(.12));b.Add(t)
silk('microSD',(117.8,121.8));silk('LiPo 1S',(108.5,150.3));silk('+',(108.5,154.8));silk('-',(106.5,154.8))
b.GetTitleBlock().SetTitle('Matrix Six - ESP32-S3 / microSD / LiPo');b.GetTitleBlock().SetRevision('0.6')
p.SaveBoard(str(OUT/'Matrix6.kicad_pcb'),b)
(OUT/'Matrix6.kicad_pro').write_text(original('kicad_pro'))
rules=original('kicad_dru').replace("A.NetName == '/VBUS_FUSED'\"","A.NetName == '/VBUS_FUSED' && !A.memberOfGroup('CHARGER_BRANCH')\"")
rules += "\n(rule \"Charger branch minimum\" (condition \"A.memberOfGroup('CHARGER_BRANCH')\") (constraint track_width (min 0.25mm)))\n"
(OUT/'Matrix6.kicad_dru').write_text(rules)
(ROOT/'docs/reference/v0.6-parts.json').write_text(json.dumps({r:{k:v for k,v in d.items() if k not in ['symbol','lib']} for r,d in parts.items()},indent=2)+'\n')
print('Matrix Six v0.6 schematic and explicit PCB revision saved')
