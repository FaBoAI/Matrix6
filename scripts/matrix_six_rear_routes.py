"""Explicit reviewed control points, executed by revise_matrix_six.py."""
# Retire obsolete supply feed and GPIO crossings under the SD contact keepouts.
for t in list(b.GetTracks()):
    n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA);la=t.GetLayer()
    if n== '/+3V3' and ((la==p.B_Cu and a in [(119.4,123),(118.4,124),(118.4,145.9)]) or (v and a in [(118.6,145.5),(119.4,123)]) or (la==p.B_Cu and a==(118.6,145.5)) or (v and a==(119.3,145.5)) or (la==p.F_Cu and a==(120.675,123))):drop(t)
    elif n=='/GND' and (a in [(123.25,145.1),(122.3,144.55),(123.125,130),(123.125,128),(129.5,147.2875),(128.5,147.325)] or c==(123.25,145.1)):drop(t)
    elif n=='/IO21' and not (la==p.F_Cu and a==(120.955,119) and not v) and not (v and a==(120.955,120)):drop(t)
    elif n=='/IO45' and (a in [(121.475,128),(121.475,127.2),(124.2,127.2)]):drop(t)
    elif n=='/IO48' and not (a==(123.495,119) or (v and a in [(123.495,120),(123.495,115.16)]) or (not v and a==(123.495,120) and c==(123.495,115.16)) or (la==p.In2_Cu and a==(123.495,115.16))):drop(t)
    elif n=='/IO0' and (a in [(121.9,123.8),(109.5,125),(109.5,145.64),(127.8,125)] or (la==p.F_Cu and not v and a==(122.325,123))):drop(t)
    elif n=='/IO3' and (a in [(110.795,138.02),(103.0,138.02)] or (not v and a==(110.795,120))):drop(t)
# IO46 shifts 0.3 mm upward to clear the moved BOOT pull-down via.
for t in list(b.GetTracks()):
    if t.GetNetname()=='/IO0' and t.GetLayer()==p.In2_Cu and not isinstance(t,p.PCB_VIA):
        for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
            at=xy(get())
            if at[1]==125:setter(pt(at[0],123.9))
    if t.GetNetname()=='/IO46' and t.GetLayer()==p.F_Cu and not isinstance(t,p.PCB_VIA):
        for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
            at=xy(get())
            if at[1]==122.1:setter(pt(at[0],121.8))
path('IO46',[(126.5,121.8),(126.5,122.1)])
path('IO0',[pad('R6',2),(121.8,122.5)]);via('IO0',(121.8,122.5));path('IO0',[(121.8,122.5),(121.8,123.9),(127.8,123.9),(127.8,124.05),(137,124.05),(137,155.7),(128.3,155.7),(126.8,157)],p.In2_Cu,.25)
path('IO3',[(110.795,120),(109.8,123.0),(109.8,126.1)],p.B_Cu,.2);via('IO3',(109.8,126.1));path('IO3',[(109.8,126.1),(109.8,138.02),pad('H1',7)],p.In2_Cu,.2)
path('IO21',[(120.955,120),(120.955,120.65)],p.B_Cu,.2);via('IO21',(120.955,120.65));path('IO21',[(120.955,120.65),(125.8,120.65)],p.In2_Cu,.2);via('IO21',(125.8,120.65));path('IO21',[(125.8,120.65),(127.2,120.65),(127.2,136.1),(126.1,137.2)],p.B_Cu,.2);via('IO21',(126.1,137.2));path('IO21',[(126.1,137.2),(131.16,137.2),(131.98,138.02),pad('H2',7)],p.In2_Cu,.2)
path('IO45',[pad('R7',1),(122.7,129.625),(124,128.325),(124,123.3),(124.2,122.78)],p.F_Cu,.25)
path('GND',[pad('R7',2),(122.8,128.2)]);via('GND',(122.8,128.2))
path('IO48',[pad('H2',16),(132.5,115.16),(132.5,141.2),(128.5,141.2),pad('R10',1)],p.F_Cu,.25)
# SD mouth toward the antenna edge. SPI is tapped from the existing Matrix5
# header nets, and runs in explicitly assigned front lanes outside the headers.
path('IO10',[(114.605,120.9),(114.605,122.3),(116.125,123.82),(116.125,125.1)],p.B_Cu,.2)
path('IO11',[(115.875,120),(115.875,121.9),(117.225,123.25),(117.225,125.1)],p.B_Cu,.2)
path('IO13',[(118.415,120),(119.9,121.485),(119.9,126.3)],p.B_Cu,.2)
for n,ref,at,points in [
 ('IO10','R16',(116.125,125.1),[(116.125,125.7),(114.475,125.7),(113,127.175)]),
 ('IO11','R17',(117.225,125.1),[(117.225,126.2),(115.975,126.2),(115,127.175)]),
 ('IO13','R18',(119.9,126.3),[(117.875,126.3),(117,127.175)])]:
    via(n,at);path(n,[at]+points+[pad(ref,1)],p.F_Cu,.2)
for n,ref,lane,level,end in [
 ('IO13',17,97.96,139.29,(110,139.29)),
 ('IO12',16,98.46,136.75,(109.2,136.75)),
 ('IO11',15,98.96,134.21,(107.8,134.21)),
 ('IO10',14,99.46,131.67,(106.7,131.67))]:
    at=pad('H1',ref);path(n,[at,(lane,at[1]),(lane,level),end],p.F_Cu,.2);via(n,end)
path('IO13',[(110,139.29),(111.4,140.7),(113.975,140.7),pad('J2',7)],p.B_Cu,.2)
path('IO12',[(109.2,136.75),(109.2,141.2),(116.175,141.2),pad('J2',5)],p.B_Cu,.2)
path('IO11',[(107.8,134.21),(107.8,144.2),(118.375,144.2),pad('J2',3)],p.B_Cu,.2)
path('IO10',[(106.7,131.67),(106.7,137.4)],p.In2_Cu,.2);via('IO10',(106.7,137.4));path('IO10',[(106.7,137.4),(106.7,138.65)],p.F_Cu,.2);via('IO10',(106.7,138.65));path('IO10',[(106.7,138.65),(107.4,140.0),(118.775,140.0),(119.475,140.7)],p.In2_Cu,.2);via('IO10',(119.475,140.7));path('IO10',[(119.475,140.7),pad('J2',2)],p.B_Cu,.2)
path('SD_DAT2',[pad('J2',1),pad('R15',1)],p.B_Cu,.2)
path('SD_DAT1',[pad('J2',8),(112.875,135.1),(115.7,135.1)],p.B_Cu,.2);via('SD_DAT1',(115.7,135.1));path('SD_DAT1',[(115.7,135.1),(115.7,131.1),(116.1,130.4),pad('R19',1)],p.F_Cu,.2)
path('+3V3',[pad('R16',2),pad('R17',2),pad('R18',2),(120,128.825),(120,131.5),(117.65,131.5)],p.F_Cu,.4)
path('+3V3',[pad('R19',2),(119.5,130.4),(119.5,131.5)],p.F_Cu,.3)
path('+3V3',[pad('R15',2),(120.6,144),(120,143.8)],p.B_Cu,.3)
path('+3V3',[pad('J2',4),pad('C12',1)],p.B_Cu,.3)
# SD VDD joins the output at the right of the contact row using L3, avoiding
# crossovers through neighbouring SD pads on the rear surface.
via('+3V3',(117.275,140.8));path('+3V3',[(117.275,140.8),(114.9,140.8),(114.9,145.7),(120.55,145.7),pad('C8',1)],p.In2_Cu,.4)
path('+3V3',[pad('R6',1),(120.8,125.5)],p.F_Cu,.4);via('+3V3',(120.8,125.5));path('+3V3',[(120.8,125.5),(120.8,127.5),(120.5,128.6)],p.B_Cu,.4);via('+3V3',(120.5,128.6));path('+3V3',[(120.5,128.6),(120,128.825)],p.F_Cu,.4)
via('+3V3',pad('C11',1));path('+3V3',[pad('C11',1),(106.775,141.175),pad('R9',1)],p.F_Cu,.6)
for ref,num,at in [('J2',6,(115.075,137.9)),('C12',2,(116.5,142.7)),('C11',2,(105.8,140.25)),('C9',2,(129.95,151.6)),('C10',2,(128.75,154.8)),('U4',2,(131.0,147.0)),('R13',2,(130.0,142.1)),('R14',2,(130.5,140.4))]:
    path('GND',[pad(ref,num),at],p.B_Cu,.3);via('GND',at)
# Charger and its bypass capacitors sit behind the SD slot, outside its opening.
for t in list(b.GetTracks()):
    if t.GetNetname()=='/VBUS_FUSED' and t.GetLayer()==p.B_Cu and not isinstance(t,p.PCB_VIA) and xy(t.GetStart()) in [(128.8,150.5),(131.55,153.26)]:drop(t)
path('VBUS_FUSED',[(128.8,150.5),pad('C9',1),(128.2,152.4),(129.3,153.3),pad('H2',1)],p.B_Cu,.8)
via('VBUS_FUSED',pad('U4',4));path('VBUS_FUSED',[pad('U4',4),(127,148.7),(128.8,150.5)],p.In2_Cu,.4)
path('VBUS_FUSED',[pad('Q1',1),(124.6,143.8)],p.B_Cu,.3);via('VBUS_FUSED',(124.6,143.8));path('VBUS_FUSED',[(124.6,143.8),(127,144.8),(127,148.7),(128.8,150.5)],p.In2_Cu,.4)
path('VBUS_FUSED',[pad('R14',1),(130.5,144.3)],p.B_Cu,.25);via('VBUS_FUSED',(130.5,144.3));path('VBUS_FUSED',[(130.5,144.3),(129,144.3),(127,146.3)],p.In2_Cu,.4)
path('CHG_PROG',[pad('U4',5),(127.0,145.5),(128.5,144.325),pad('R13',1)],p.B_Cu,.25)
path('VBAT',[pad('U4',3),(130.45,148.6),(131.1,148.6)],p.B_Cu,.6)
via('VBAT',pad('C10',1));path('VBAT',[pad('C10',1),(131.1,154.8),(131.1,148.6)],p.In2_Cu,.6)
path('VBAT',[pad('Q1',3),(121,147.0625),(121,147.8),(122,148.9),(125.6,148.9)],p.B_Cu,.6);path('VBAT',[(125.6,148.9),(129.9,148.9),(130.45,148.6),(131.1,148.6)],p.B_Cu,.6);via('VBAT',(131.1,148.6));path('VBAT',[(131.1,148.6),(131.1,151.99),(137.2,151.99)],p.F_Cu,.4);path('VBAT',[(137.2,151.99),(137.2,105),pad('H2',20)],p.F_Cu,.6)
path('VBAT',[pad('J3',1),(111.5,153.5),(111.5,147.8)],p.F_Cu,.8);via('VBAT',(111.5,147.8));path('VBAT',[(111.5,147.8),(114,147.8),(114,146.8),(121,146.8),(121,147.8)],p.In2_Cu,1.2);via('VBAT',(121,147.8))
path('VSYS',[pad('Q1',2),(124.8,147.4)],p.B_Cu,.6);via('VSYS',(124.8,147.4));path('VSYS',[(124.8,147.4),(125.8,146.4),(125.8,144.3),(125.7,142.5)],p.F_Cu,.6)
# Identify the low-current charger/gate branches for their narrower pad escapes.
g=p.PCB_GROUP(b);g.SetName('CHARGER_BRANCH');b.Add(g)
for t in b.GetTracks():
    if t.GetNetname()=='/VBUS_FUSED' and not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetWidth())<.8:g.AddItem(t)

keep=p.ZONE(b);keep.SetLayer(p.B_Cu);keep.SetIsRuleArea(True);keep.SetZoneName('SD_CARD_WITHDRAWAL_AND_FINGER_CLEARANCE');keep.SetDoNotAllowFootprints(True);keep.SetDoNotAllowTracks(False);keep.SetDoNotAllowVias(False);keep.SetDoNotAllowPads(False);keep.SetDoNotAllowZoneFills(False)
poly=keep.Outline();poly.NewOutline()
for at in [(109.9,100.5),(125.7,100.5),(125.7,123.0),(109.9,123.0)]:poly.Append(int(mm(at[0])),int(mm(at[1])))
b.Add(keep)

seen=set()
for t in list(b.GetTracks()):
    if isinstance(t,p.PCB_VIA):
        key=(t.GetNetname(),xy(t.GetPosition()))
        if key in seen:drop(t)
        seen.add(key)
