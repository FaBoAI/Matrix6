# Explicit manual changes applied by redesign_two_layer.py.
# Relocate the reset RC network into the top-left wing to free routing channels.
oldpads={r:[xy(q.GetPosition()) for q in fps[r].Pads()] for r in ['R5','C4','C5']}
for r,at,deg in [('R5',(102.8,100.95),0),('C4',(103.5,103.1),180),('C5',(100,101.3),0)]:
 f=fps[r];f.SetPosition(pt(at));f.SetOrientationDegrees(deg)
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA):continue
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());la=t.GetLayer()
 if n=='/+3V3' and la==p.F_Cu and min(a[1],c[1])>=102.9 and max(a[1],c[1])<110 and max(a[0],c[0])<108:drop(t)
 if n=='/EN' and la==p.F_Cu and max(a[1],c[1])<114 and a!=(109.03,103.78):drop(t)
 if n=='/GND' and any(a in ats or c in ats for ats in oldpads.values()):drop(t)
path('EN',[pad('R5',2),(103.5,101.9),(103.5,104.1)],p.F_Cu,.25);via('EN',(103.5,104.1))
path('EN',[(103.5,104.1),(104.5,104.1),(104.82,103.78),(108.1,103.78)],p.B_Cu,.25)
path('EN',[pad('C5',1),(99.225,103.4),(99.3,103.78)],p.F_Cu,.25)
for ref,at in [('R5',(101.975,102.0)),('C4',(104.275,103.1))]:
 path('+3V3',[pad(ref,1),at],p.F_Cu,.3);via('+3V3',at);path('+3V3',[at,(at[0],102.3)],p.B_Cu,.3)
for r,at in [('C4',(102.725,103.7)),('C5',(100.775,100.55))]:
 path('GND',[pad(r,2),at],p.F_Cu,.25);via('GND',at)
# The module-pad crossing portions of selected old inner-layer escapes are rear-side.
# Outer portions remain front-side, crossing the original vertical rear lanes.
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA) or t.m_Uuid.AsString() not in inner_ids:continue
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd())
 if n in ['/IO2','/IO15','/IO16','/IO12','/IO13','/IO14'] and abs(a[1]-c[1])<.01 and min(a[0],c[0])<107.5 and max(a[0],c[0])>108:
  drop(t);inside=a if a[0]>c[0] else c;outside=c if a[0]>c[0] else a
  path(n,[inside,(107.5,a[1])],p.B_Cu,.2);via(n,(107.5,a[1]));path(n,[(107.5,a[1]),outside],p.F_Cu,.2)
# IO14's source-side horizontal section avoids the module exposed ground pad.
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/IO14' and t.m_Uuid.AsString() in inner_ids and xy(t.GetStart())[0]>108:t.SetLayer(p.B_Cu)
# Wide supply trunks stay separated around the buck-boost and source switch.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/VBUS_FUSED' and (a in [(125.9,143.8),(130.5,144.3),(131.4,144.3),(131.4,145.8),(131.4,150.4),(129.7,150.4)] or (a==(124.6,143.8) and not v)):drop(t)
 if n=='/VSYS':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[0]==124.5 and at[1] in [135.1,140.4]:setter(pt(124.8,at[1]))
 if n=='/+3V3' and not v and t.GetLayer()==p.F_Cu:
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[1]==131.5:setter(pt(at[0],131.4))
 if n=='/VBAT' and not v:
  if a in [(111.5,147.8),(114,147.8),(114,146.8)]:drop(t)
  if a in [(130.649999,154.8),(131.1,154.8)]:t.SetLayer(p.F_Cu)
 if n=='/GND':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   if xy(get())==(130.5,140.4):setter(pt(130.5,139.5))
path('VBUS_FUSED',[(124.6,143.8),(126.3,143.8),(126.6,143.5)],p.B_Cu,.4);via('VBUS_FUSED',(126.6,143.5));path('VBUS_FUSED',[(126.6,143.5),(127,143.9),(127,144.8)],p.F_Cu,.4)
via('VBUS_FUSED',(130.5,144.3));path('VBUS_FUSED',[(130.5,144.3),(131.2,143.6),(131.2,140.3),(127,140.3),(127,144.8)],p.F_Cu,.4)
path('VBAT',[(111.5,147.8),(112.1,148.4),(120.4,148.4),(121,147.8)],p.B_Cu,.8)
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/VBUS_FUSED' and p.ToMM(t.GetWidth())<.8 and not t.GetParentGroup():g.AddItem(t)
# Module-side vertical escapes use free front copper under the module body.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n in ['/IO15','/IO16'] and not v and t.GetLayer()==p.B_Cu and a[0]==c[0] and a[0] in [110.7,111.4]:t.SetLayer(p.F_Cu)
 if n=='/IO1' and not v and t.m_Uuid.AsString() in inner_ids and max(a[1],c[1])<105:drop(t)
 if n=='/IO1':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   if xy(get())==(102.6,104.4):setter(pt(102.6,104.55))
via('IO2',(112.2,108.22))
path('IO1',[(127.4,102.51),(127.4,100.6),(110.0,100.6),(110.0,104.55),(102.6,104.55)],p.B_Cu,.2)
# Cross the right-side module pad row on the rear, then the existing rear lanes on front.
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA) or t.m_Uuid.AsString() not in inner_ids:continue
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd())
 if n in ['/IO17','/IO18','/IO47','/IO48'] and a[0]<127.5 and c[0]>127.5:
  drop(t);path(n,[a,(127.5,a[1])],p.B_Cu,.2);via(n,(127.5,a[1]));path(n,[(127.5,a[1]),c],p.F_Cu,.2)
# BOOT takes the far right rear lane; the left branch uses the rear connector body gap.
for t in list(b.GetTracks()):
 if t.GetNetname()!='/IO0':continue
 a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if not v and a in [(127.8,124.05),(137,124.05),(137,155.7),(128.3,155.7),(126.8,157.2),(125.9,158.1),(125.9,160.1),(103,160.1)]:drop(t)
 if not v and a==(121.8,123.9):t.SetLayer(p.B_Cu)
path('IO0',[(127.8,124.05),(136.9,124.05)],p.F_Cu,.25);via('IO0',(136.9,124.05))
path('IO0',[(136.9,124.05),(136.9,155.7),(126.8,155.7),(126.8,157.2)],p.B_Cu,.25)
path('IO0',[(126.8,157.2),(125.0,157.2),(125,156.6),(111.7,156.6),(111.7,157.1),(103,157.1)],p.B_Cu,.25);via('IO0',(103,157.1))
path('IO0',[(103,157.1),(103,145.64)],p.F_Cu,.25)
via('IO0',(121.8,123.9))
# Keep the LED branch on the front after the rear lane ends.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/IO48' and not isinstance(t,p.PCB_VIA) and xy(t.GetStart())==(132.5,141.2):t.SetLayer(p.F_Cu)
via('IO48',(132.5,141.2))
# Bring the lower module GPIOs out above the USB series resistors.
rows={'IO9':(113.335,122.78,115.2,106.9,103.6,13),
      'IO10':(114.605,120.9,114.4,107.5,103.2,14),
      'IO11':(115.875,117.7,113.6,107.5,102.8,15),
      'IO12':(117.145,114.57,112.7,107.5,None,16),
      'IO13':(118.415,112.1,111.9,107.5,None,17)}
for name,(sx,oldy,y,vx,lane,pin) in rows.items():
 for t in list(b.GetTracks()):
  if t.GetNetname()!='/'+name:continue
  a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
  if v and a in [(sx,oldy),(107.5,oldy)]:drop(t);continue
  if v:continue
  if a[0]==c[0]==sx and set([a[1],c[1]])==set([120,oldy]):drop(t);continue
  if abs(a[1]-oldy)<.001 and abs(c[1]-oldy)<.001 and min(a[0],c[0])>=101.27 and max(a[0],c[0])<=sx:drop(t);continue
  if a==(103.0,oldy) and c==pad('H1',pin):drop(t)
 path(name,[(sx,120),(sx,y),(vx,y)],p.B_Cu,.2);via(name,(vx,y))
 if lane:path(name,[(vx,y),(lane,y),(lane,pad('H1',pin)[1]),pad('H1',pin)],p.F_Cu,.2)
 elif name=='IO12':
  path(name,[(vx,y),(103.1,y),(101.8,114.0),(101.8,114.1)],p.F_Cu,.2);via(name,(101.8,114.1));path(name,[(101.8,114.1),pad('H1',pin)],p.B_Cu,.2)
 else:path(name,[(vx,y),(103.0,y),pad('H1',pin)],p.F_Cu,.2)
# Open the rear crossing above the IO8 escape, and clear space for IO9's via.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/IO7':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[0]==106.5:setter(pt(106.2,at[1]))
 if n=='/IO8' and (a==(109.03,115.21) or (v and a==(108.1,115.21)) or (not v and a==(108.1,115.21)) or (not v and a==(107.85,115.21))):drop(t)
path('IO8',[(109.03,115.21),(110.5,115.21),(110.5,116.1)],p.F_Cu,.2);via('IO8',(110.5,116.1));path('IO8',[(110.5,116.1),(110.5,116.9),(107.85,116.9),(107.85,125.32)],p.B_Cu,.2)
# USB: explicitly drawn 0.36/0.20 mm coplanar pair. The connector fan-out is retained.
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA):continue
 if t.GetNetname() in ['/USB_N','/USB_P'] and p.ToMM(t.GetWidth())==.28:drop(t)
ug=next(g for g in b.Groups() if g.GetName()=='USB_90OHM_TRUNK')
path('USB_N',[pad('R3',1),(104.2,116.3),(104.2,118.6),(108.8,123.2),(108.8,141.85),(114.15,147.2)],p.F_Cu,.36)
path('USB_P',[pad('R4',1),(104.76,117.9),(104.76,118.368041),(109.36,122.968041),(109.36,141.618041),(114.46196,146.72),(116.05,146.72),(116.05,147.8625)],p.F_Cu,.36)
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname() in ['/USB_N','/USB_P'] and p.ToMM(t.GetWidth())==.36:ug.AddItem(t)
# Move the IO46 pull-down clear of the USB diagonal.
oldr8=[xy(q.GetPosition()) for q in fps['R8'].Pads()]
fps['R8'].SetPosition(pt(112.5,123.6));fps['R8'].SetOrientationDegrees(0)
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA):continue
 a,c=xy(t.GetStart()),xy(t.GetEnd())
 if t.GetNetname()=='/IO46' and a in [tuple(oldr8[0]),(107.675,123.3),(108.6,122.375),(108.6,121.8)]:drop(t)
 if t.GetNetname()=='/GND' and (a in oldr8 or c in oldr8):drop(t)
path('IO46',[pad('R8',1),(111.675,122.6),(112.065,122.21),(112.065,121.8)],p.F_Cu,.25)
path('GND',[pad('R8',2),(113.325,124.4)],p.F_Cu,.25);via('GND',(113.325,124.4))
# IO3 crosses to the left before the SD fan-out begins.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/IO3' and (xy(t.GetStart()) in [(109.8,126.1),(109.8,138.02)]):drop(t)
path('IO3',[(109.8,126.1),(109.8,128.7),(108.4,130.1),(107.6,130.1)],p.B_Cu,.2);via('IO3',(107.6,130.1))
path('IO3',[(107.6,130.1),(107.6,138.02),pad('H1',7)],p.F_Cu,.2)
# Explicitly nested SD branches. The clock crosses onto front between the regulator pads.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/IO10' and (a in [(106.7,131.669999),(106.7,137.4),(106.7,138.65),(107.4,140.0),(118.775,140.0),(119.475,140.7)]):drop(t)
 if n=='/IO11' and a in [(107.8,134.21),(107.8,144.2),(118.375,144.2)]:drop(t)
 if n=='/IO12' and a in [(109.2,136.75),(109.2,141.2)]:drop(t)
 if not v and n in ['/IO10','/IO11','/IO12'] and a[0]<100 and a[1] in [131.669999,134.21,136.75]:drop(t)
path('IO10',[(99.46,131.67),(105.8,131.67)],p.F_Cu,.2);via('IO10',(105.8,131.67))
path('IO10',[(105.8,131.67),(105.8,133.7),(105,134.5),(105,143.3),(115.7,143.3)],p.B_Cu,.2);via('IO10',(115.7,143.3))
path('IO10',[(115.7,143.3),(115.7,141),(119.475,141),(119.475,140.9)],p.F_Cu,.2);via('IO10',(119.475,140.9));path('IO10',[(119.475,140.9),pad('J2',2)],p.B_Cu,.2)
path('IO11',[(98.96,134.21),(106.3,134.21)],p.F_Cu,.2);via('IO11',(106.3,134.21));path('IO11',[(106.3,134.21),(106.3,142.5),(118.375,142.5),pad('J2',3)],p.B_Cu,.2)
path('IO12',[(98.46,136.75),(107.0,136.75)],p.F_Cu,.2);via('IO12',(107.0,136.75));path('IO12',[(107.0,136.75),(107.0,141.2),(116.175,141.2)],p.B_Cu,.2)
# Clearance refinements around the right header and button pull-up.
for t in b.GetTracks():
 if t.GetNetname() in ['/IO17','/IO18','/IO48']:
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[0]==127.5:setter(pt(127.8,at[1]))
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/IO48' and not v and a==(123.495,120) and c==(123.495,115.16):t.SetLayer(p.F_Cu)
 if n=='/IO18' and not v and a==(122.0,116.43) and c==(124.5,116.43):t.SetLayer(p.B_Cu)
 if n=='/IO47' and (a in [(122.225,118.55),(127.5,118.55)]):drop(t)
via('IO18',(122.0,116.43))
path('IO47',[(122.225,118.55),(125.8,118.55),(125.8,119.4)],p.B_Cu,.2);via('IO47',(125.8,119.4));path('IO47',[(125.8,119.4),(126.65,118.55),(133.44,118.55)],p.F_Cu,.2)
# The BOOT pull-up moves onto the rear below the LED, clear of the SD mechanism.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/IO0' and a in [(122.325,123),(121.8,122.5),(121.8,123.9),(127.8,123.9)]:drop(t)
 if n=='/+3V3' and a in [(120.675,123),(120.8,125.5),(120.8,127.5),(120.5,128.6)]:drop(t)
 if n=='/IO0' and a in [(127.8,124.05),(136.9,124.05),(136.9,155.7),(126.8,155.7)]:drop(t)
 if n=='/IO0':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[1]==157.1:setter(pt(at[0],157.3))
fps['R6'].Flip(fps['R6'].GetPosition(),False);fps['R6'].SetPosition(pt(108.5,149.9));fps['R6'].SetOrientationDegrees(0)
path('IO0',[(127.8,123.6),(127.8,124.05),(135.9,124.05),(135.9,151.2)],p.F_Cu,.25);via('IO0',(135.9,151.2));path('IO0',[(135.9,151.2),(135.9,152.8)],p.B_Cu,.25);via('IO0',(135.9,152.8));path('IO0',[(135.9,152.8),(135.9,155.9),(126.8,155.9),(126.8,157.2)],p.F_Cu,.25)
path('IO0',[pad('R6',2),(109.325,150.5)],p.B_Cu,.25);via('IO0',(109.325,150.5));path('IO0',[(109.325,150.5),(103,150.5)],p.F_Cu,.25)
path('+3V3',[pad('R6',1),(107.675,150.3),(103.7,150.3)],p.B_Cu,.25)
# RESET changes side before the two bottom 3V3 branches.
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/EN' and xy(t.GetStart())==(99.3,103.78) and xy(t.GetEnd())==(99.3,156.5):drop(t)
path('EN',[(99.3,103.78),(99.3,149.5)],p.B_Cu,.25);via('EN',(99.3,149.5));path('EN',[(99.3,149.5),(99.3,156.5)],p.F_Cu,.25)
# CC1 goes below the left VBUS take-off, outside the connector metal.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/CC1' and not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.B_Cu:drop(t)
path('CC1',[(110.3,151.8),(110.3,153.2),(115.3,153.2),(115.95,152.75)],p.B_Cu,.2)
# Parallel battery/3V3 trunks are separated before the ESD VBUS tap.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/VBAT' and not v and a in [(111.5,147.8),(112.1,148.4),(120.4,148.4)]:drop(t)
 if n=='/+3V3' and not v and t.GetLayer()==p.B_Cu:
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[1]==146.9:setter(pt(at[0],146.5))
path('VBAT',[(111.5,147.8),(114,147.8),(114.4,147.5),(120.7,147.5),(121,147.8)],p.B_Cu,.8)
# Move the SD bypass capacitor clear of the signal lanes and the POWER resistor inward.
oldc11=[xy(q.GetPosition()) for q in fps['C11'].Pads()]
oldr9=[xy(q.GetPosition()) for q in fps['R9'].Pads()]
fps['C11'].SetPosition(pt(104.5,148.7));fps['C11'].SetOrientationDegrees(0)
fps['R9'].Move(pt(-.6,0))
newr9=[xy(q.GetPosition()) for q in fps['R9'].Pads()]
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if a in oldc11 or c in oldc11:drop(t);continue
 for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  at=xy(get())
  if at in oldr9:setter(pt(newr9[oldr9.index(at)]))
via('+3V3',pad('C11',1));path('+3V3',[pad('C11',1),(104.5,147.75),(104.5,142),(105.325,141.175),pad('R9',1)],p.F_Cu,.4)
path('+3V3',[pad('C11',1),(103.7,148.7)],p.B_Cu,.4)
path('GND',[pad('C11',2),(105.45,149.5)],p.B_Cu,.3);via('GND',(105.45,149.5))
# A short front bridge lets SD command pass over the rear clock branch.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/IO11' and not isinstance(t,p.PCB_VIA) and xy(t.GetStart()) in [(106.3,134.21),(106.3,142.5),(118.375,142.5)]:drop(t)
path('IO11',[(106.3,134.21),(106.3,142.4)],p.B_Cu,.2);via('IO11',(106.3,142.4));path('IO11',[(106.3,142.4),(106.3,144)],p.F_Cu,.2);via('IO11',(106.3,144));path('IO11',[(106.3,144),(106.3,144.4),(118.375,144.4),pad('J2',3)],p.B_Cu,.2)
for t in list(b.GetTracks()):
 if t.GetNetname()=='/IO10' and not isinstance(t,p.PCB_VIA) and xy(t.GetStart()) in [(115.7,143.3),(115.7,141)]:drop(t)
path('IO10',[(115.7,143.3),(118.3,143.3),(118.3,141),(119.475,141)],p.F_Cu,.2)
path('IO10',[(114.605,120),(114.605,120.9)],p.B_Cu,.2)
# SD data tap changes sides before the USB corridor.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/IO13' and xy(t.GetStart()) in [(97.96,139.29),(110,139.29)]:drop(t)
path('IO13',[(97.96,139.29),(108.0,139.29)],p.F_Cu,.2);via('IO13',(108,139.29));path('IO13',[(108,139.29),(108,140),(111.4,140.7)],p.B_Cu,.2)
# Remove obsolete stitching points and unneeded module escape vias.
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA) and ((t.GetNetname()=='/GND' and xy(t.GetPosition()) in [(108.7,126),(100.775,100.55),(102.725,103.7),(107.4,103.17)]) or (t.GetNetname()=='/IO16' and xy(t.GetPosition())==(111.4,111.4))):drop(t)
# Finalize the reset RC placement with complete courtyard clearance.
prior={r:[xy(q.GetPosition()) for q in fps[r].Pads()] for r in ['R5','C4','C5']}
fps['R5'].SetPosition(pt(102.4,101.0));fps['C4'].SetPosition(pt(105.2,103.9));fps['C5'].SetPosition(pt(98.7,102.0));fps['C5'].SetOrientationDegrees(90)
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if any(a in prior[r] or c in prior[r] for r in ['C4','C5']):drop(t);continue
 if n=='/EN' and a in [(103.5,101.9),(103.5,104.1),(104.5,104.1),(104.82,103.78)]:drop(t);continue
 for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  at=xy(get())
  if at in prior['R5']:setter(pt(pad('R5',prior['R5'].index(at)+1)))
path('EN',[(103.5,101.9),(103.3,103.4)],p.F_Cu,.25);via('EN',(103.3,103.4));path('EN',[(103.3,103.4),(103.7,103.78)],p.B_Cu,.25)
path('EN',[pad('C5',1),(99.3,103.4),(99.3,103.78)],p.F_Cu,.25)
path('+3V3',[pad('C4',1),(106.75,103.9),(106.75,102.9)],p.F_Cu,.3)
path('GND',[pad('C4',2),(104.8,103.525),(104.8,103.1)],p.F_Cu,.25);via('GND',(104.8,103.1))
path('GND',[pad('C5',2),(99.2,101.1)],p.F_Cu,.25);via('GND',(99.2,101.1))
# Raise IO1 by 0.15 mm alongside the IO4 via.
for t in b.GetTracks():
 if t.GetNetname()=='/IO1':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[1]==104.55:setter(pt(at[0],104.4))
# The rear LED capacitor is the only required feed to the POWER resistor.
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/+3V3' and xy(t.GetStart())==(107,141.175) and xy(t.GetEnd())==(107,146.9):drop(t)
# Shift the far-right supply and route BOOT around the header escape vias.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/VBAT':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[0]==137.2:setter(pt(137.5,at[1]))
 if n=='/IO0' and a in [(127.8,124.05),(135.9,124.05),(135.9,151.2),(135.9,152.8)]:drop(t);continue
 if n=='/IO0':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[0]==103:setter(pt(102.8,at[1]))
 if n=='/IO0' and not v and a==(109.325,150.5):drop(t)
path('IO0',[(127.8,124.05),(136.85,124.05),(136.85,150.05),(136.3,150.6)],p.F_Cu,.25);via('IO0',(136.3,150.6));path('IO0',[(136.3,150.6),(136.3,153.0)],p.B_Cu,.25);via('IO0',(136.3,153.0));path('IO0',[(136.3,153),(136.3,155.5),(135.9,155.9)],p.F_Cu,.25)
path('IO0',[(109.325,150.5),(109.325,149.6),(102.8,149.6)],p.F_Cu,.25)
# CC1's resistor escape joins the connector from beneath the VBUS branch.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if n=='/CC1':
  if not v and t.GetLayer()==p.B_Cu:drop(t);continue
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   if xy(get())==(106,150.5):setter(pt(106,151.0))
 if n=='/+3V3' and not v and a in [(107.675,149.9),(107.675,150.3)]:drop(t)
 if n=='/GND':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   if xy(get())==(105.45,149.5):setter(pt(105.45,147.8))
path('+3V3',[pad('R6',1),(103.7,149.9)],p.B_Cu,.25)
path('CC1',[(106,151.0),(106.7,151.7),(110.3,152.5),(115.3,153.2),(115.95,152.75)],p.B_Cu,.2)
# Move the two right-side signal crossings onto the rear locally.
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd())
 if not isinstance(t,p.PCB_VIA) and ((n=='/IO48' and a==(132.5,141.2)) or (n=='/IO21' and a==(126.1,137.2) and c==(131.16,137.2))):drop(t)
path('IO48',[(132.5,141.2),(131.8,140.5),(128.5,140.5),(128.5,141.2)],p.B_Cu,.2)
path('IO21',[(126.1,137.2),(128.3,137.2)],p.B_Cu,.2);via('IO21',(128.3,137.2));path('IO21',[(128.3,137.2),(131.16,137.2)],p.F_Cu,.2)
for d in b.GetDrawings():
 if not isinstance(d,p.PCB_TEXT):continue
 if d.GetText()=='Matrix Six':d.SetPosition(pt(118.4,124.3))
 if d.GetLayer()==p.B_SilkS and d.GetText()=='EN':d.SetPosition(pt(104.1,146.5))
 if d.GetText()=='LiPo 1S':d.SetPosition(pt(108.0,151.8))
# Delete the abandoned low-current branch stub.
for t in list(b.GetTracks()):
 if t.GetNetname()=='/VBUS_FUSED' and not isinstance(t,p.PCB_VIA) and xy(t.GetStart())==(129.699999,150.4):drop(t)
# Remove obsolete vias identified after all nets are connected.
obsolete={
 '/VSYS':[(125,141.5),(122,141.4)], '/VBUS_FUSED':[(124.6,143.8)],
 '/IO18':[(124.5,116.43)], '/IO21':[(126.1,137.2)], '/IO45':[(124.2,122.78)],
 '/IO46':[(126.5,122.1)], '/IO48':[(123.495,120),(132.5,141.2)],
 '/VBAT':[(121,147.8)], '/+3V3':[(117.65,132.8),(101,101),(107,146.9)],
 '/IO0':[(102.8,145.64)], '/IO1':[(102.6,104.4)], '/IO2':[(127.4,103.78)],
 '/IO14':[(119.685,111)], '/IO15':[(110.7,110.13)]}
for t in list(b.GetTracks()):
 n=t.GetNetname();a,c=xy(t.GetStart()),xy(t.GetEnd());v=isinstance(t,p.PCB_VIA)
 if v and a in obsolete.get(n,[]):drop(t);continue
 if n=='/+3V3' and not v and a==(106.8,103.725):drop(t);continue
 if n=='/CC1' and not v and a==(110.3,152.5):drop(t);continue
 if n=='/GND' and not v and a==pad('R14',2):drop(t);continue
 if n=='/GND':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   if xy(get())==(104.8,103.1):setter(pt(104.8,103.18))
path('CC1',[(110.3,152.5),(110.8,153.25),(115.3,153.25),(115.3,153.2)],p.B_Cu,.2)
path('GND',[pad('R14',2),(130.5,142.5)],p.B_Cu,.3);via('GND',(130.5,142.5))
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT):
  if d.GetLayer()==p.B_SilkS and d.GetText()=='EN':d.SetPosition(pt(103.7,147.2));d.SetTextSize(pt(.7,.7))
  if d.GetText()=='LiPo 1S':d.SetPosition(pt(108.0,147.2))
# Make room for a continuous front coplanar ground strip beside the USB trunk.
for t in b.GetTracks():
 if t.GetNetname() in ['/USB_N','/USB_P']:
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at in [(108.8,123.2),(108.8,141.85),(109.36,122.968041),(109.36,141.618041)]:setter(pt(at[0]+.4,at[1]+.4))
 if t.GetNetname()=='/IO13':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[0]==108 and at[1] in [139.29,140]:setter(pt(107.7,at[1]))
for z in b.Zones():
 if not z.GetIsRuleArea() and z.GetLayer()==p.F_Cu:z.SetLocalClearance(mm(.20))
# Stitches beside, never on, the differential pair.
for at in [(108.4,127.8),(110.55,128.1),(108.4,131.3),(110.55,131.3),
           (108.4,134.0),(110.55,133.8),(108.4,137.2),(110.55,137.2),
           (108.4,138.5),(110.55,138.2),(108.4,142.1),(111.0,142.1)]:via('GND',at)
# Keep stitching outside the SD manufacturer's mechanical keepouts.
for t in list(b.GetTracks()):
 n=t.GetNetname();a=xy(t.GetStart());v=isinstance(t,p.PCB_VIA)
 if n=='/GND':
  repl={(110.55,131.3):(113,131.3),(110.55,133.8):(111.75,134),
        (110.55,137.2):(111.75,137.2),(110.55,138.2):(111.75,138.2),
        (130.5,142.5):(129.8,141.9)}
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at in repl:setter(pt(repl[at]))
 if n=='/+3V3' and ((v and abs(a[0]-101)<1e-4 and abs(a[1]-101)<1e-4) or (not v and abs(a[0]-106.8)<1e-4 and abs(a[1]-103.725)<1e-4)):drop(t)
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT) and d.GetText()=='EN' and d.GetLayer()==p.B_SilkS:d.SetTextSize(pt(.8,.8))
# One explicitly dimensioned D+ length correction, separate from the uniform trunk.
import math
amplitude=.751025/(2*(math.sqrt(2)-1));x=109.76;y0=125.2;y1=126.9
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/USB_P' and xy(t.GetStart())==(109.76,123.368041):drop(t)
path('USB_P',[(x,123.368041),(x,y0)],p.F_Cu,.36)
path('USB_P',[(x,y1+amplitude),(x,142.018041)],p.F_Cu,.36)
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='/USB_P' and p.ToMM(t.GetWidth())==.36 and not t.GetParentGroup():ug.AddItem(t)
mg=p.PCB_GROUP(b);mg.SetName('USB_LENGTH_MATCH_TRANSITION');b.Add(mg)
start_ids={t.m_Uuid.AsString() for t in b.GetTracks()}
path('USB_P',[(x,y0),(x+amplitude,y0+amplitude),(x+amplitude,y1),(x,y1+amplitude)],p.F_Cu,.36)
for t in b.GetTracks():
 if t.m_Uuid.AsString() not in start_ids:mg.AddItem(t)
# Prevent a floating ground tongue inside the length-matching loop.
k=p.ZONE(b);k.SetLayer(p.F_Cu);k.SetIsRuleArea(True);k.SetZoneName('USB_LENGTH_MATCH_NO_INNER_POUR');k.SetDoNotAllowTracks(False);k.SetDoNotAllowVias(False);k.SetDoNotAllowPads(False);k.SetDoNotAllowFootprints(False);k.SetDoNotAllowZoneFills(True)
poly=k.Outline();poly.NewOutline()
for at in [(109.38,125.0),(109.65,125.0),(110.8,126.106555),(110.8,126.9),(109.65,128.0),(109.38,128.0)]:poly.Append(pt(at))
b.Add(k)
# Two old unconnected ground items can be re-netted by KiCad during refill;
# remove them by their persistent source UUID rather than by their transient net.
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString() in ['f48ee5cb-d1aa-4243-9c09-7c06fa0ae22c','5a3cd5ee-8b71-4bbe-95c7-fb465f4aa50b']:drop(t);continue
 if t.GetNetname()=='/GND':
  if isinstance(t,p.PCB_VIA) and xy(t.GetPosition())==(129.8,141.9):drop(t);continue
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   if xy(get())==(129.8,141.9):setter(pt(130,142.1))
# Avoid the 0.2 mm drill price tier on two-layer fabrication.
# Preserve the thermal array locations, increasing annulus to 0.25 mm.
for q in fps['U1'].Pads():
 if q.GetNumber()=='41' and q.GetAttribute()==p.PAD_ATTRIB_PTH:
  q.SetDrillSize(pt(.3,.3));q.SetSize(pt(.8,.8))
libfile=OUT/'DevBoard.pretty/ESP32-S3-WROOM-1_Edge.kicad_mod'
lib=parse(libfile.read_text())
for q in children(lib,'pad'):
 if q[1]=='41' and q[2]=='thru_hole':
  child(q,'size')[1:]=[A('.8'),A('.8')];child(q,'drill')[1]=A('.3')
libfile.write_text(dump(lib)+'\n')
# Split (without changing geometry) the long straight lines so the local
# differential-gap rule applies exactly to the reviewed 128.5..141.5 mm region.
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA) or t.GetNetname() not in ['/USB_N','/USB_P']:continue
 a,c=xy(t.GetStart()),xy(t.GetEnd())
 if abs(a[0]-c[0])<1e-6 and min(a[1],c[1])<128.5 and max(a[1],c[1])>141.5:
  n=t.GetNetname();drop(t);path(n,[a,(a[0],128.5),(a[0],141.5),c],p.F_Cu,.36)
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname() in ['/USB_N','/USB_P'] and p.ToMM(t.GetWidth())==.36 and not t.GetParentGroup():ug.AddItem(t)
# Added thermal annulus needs 0.08 mm more space at the lower module edge.
for t in b.GetTracks():
 if t.GetNetname()=='/IO14':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   at=xy(get())
   if at[1]==111:setter(pt(at[0],111.08))
# Put the SD bulk bypass next to its VDD take-off on the front. The existing
# rear 100 nF remains at the connector; the old left-side via now feeds POWER.
fps['C11'].Flip(fps['C11'].GetPosition(),False);fps['C11'].SetPosition(pt(116,142.2));fps['C11'].SetOrientationDegrees(0)
for t in list(b.GetTracks()):
 if t.GetNetname()=='/GND' and not isinstance(t,p.PCB_VIA) and xy(t.GetStart())==(105.45,148.7):drop(t);continue
 if t.GetNetname()=='/IO10':
  for get,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
   if xy(get())==(115.7,143.3):setter(pt(115.7,143.5))
path('+3V3',[pad('C11',1),(114.9,142.2)],p.F_Cu,.4)
path('GND',[pad('C11',2),(116.5,142.7)],p.F_Cu,.3)
# Final sensitivity screen centres the nominal impedance near 90 ohm while
# keeping the already matched centreline geometry: 0.38 width / 0.18 edge gap.
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) and t.GetNetname() in ['/USB_N','/USB_P'] and abs(p.ToMM(t.GetWidth())-.36)<1e-6:t.SetWidth(mm(.38))
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT):
  if d.GetLayer()==p.B_SilkS and d.GetText()=='EN':d.SetPosition(pt(104.1,148.18))
  if d.GetText()=='LiPo 1S':d.SetPosition(pt(108.0,151.2))
p.FootprintSave(str(OUT/'DevBoard.pretty'),p.FootprintLoad(str(OUT/'DevBoard.pretty'),'ESP32-S3-WROOM-1_Edge'))
