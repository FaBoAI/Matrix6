"""Measure actual two-layer copper returns; never route or modify the PCB.

The rear copper is split by a few signals. Front coplanar ground is therefore
checked independently. The connector, pads, bends and length correction remain
local transitions and are not a calibrated impedance measurement.
"""
from pathlib import Path
import json,math,wx,pcbnew as p
app=wx.App(False);ROOT=Path(__file__).resolve().parent.parent
b=p.LoadBoard(str(ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'))
assert b.GetCopperLayerCount()==2
assert all(isinstance(t,p.PCB_VIA) or t.GetLayer() in [p.F_Cu,p.B_Cu] for t in b.GetTracks())
zones={la:next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==la).GetFilledPolysList(la) for la in [p.F_Cu,p.B_Cu]}
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(v):return [p.ToMM(v.x),p.ToMM(v.y)]
results=[]
# Broad GND beside the long straight section, beyond the length correction.
for n,x,sign in [('N',109.2,-1),('P',109.76,1)]:
 missing=[];samples=0
 for i in range(521):
  y=128.5+i*.025
  for off in [.19+.20+.05,.19+.20+.30,.19+.20+.50]:
   xx=x+sign*off;samples+=1
   if not zones[p.F_Cu].Contains(pt(xx,y)):missing.append([round(xx,4),round(y,4)])
 results.append({'side':n,'section_y_mm':[128.5,141.5],'ground_width_checked_mm':.5,'samples':samples,'missing':missing})
report={'status':'PASS' if not any(r['missing'] for r in results) else 'FAIL',
 'copper_layers':2,'front_coplanar_clearance_mm':.20,'uniform_width_mm':.38,'uniform_edge_gap_mm':.18,
 'checked_straight_return_bands':results,
 'rear_ground_regions':zones[p.B_Cu].OutlineCount(),
 'GND_stitch_vias':sum(isinstance(t,p.PCB_VIA) and t.GetNetname()=='/GND' for t in b.GetTracks()),
 'scope':'Saved filled F.Cu GND beside the straight differential pair, including 0.5 mm outward width. Rear is a stitched pour with signal crossings, not an uninterrupted reference plane. Local connector/bend/meander transitions need prototype SI/EMC testing.'}
(ROOT/'docs/validation/two-layer-ground.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'missing_by_side':{r['side']:len(r['missing']) for r in results},'rear_regions':report['rear_ground_regions']},indent=2))
assert report['status']=='PASS'
