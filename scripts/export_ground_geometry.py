"""Export the filled L2 polygon and GND via locations for independent DC analysis."""
from pathlib import Path
import json,wx,pcbnew as p
app=wx.App(False);ROOT=Path(__file__).resolve().parent.parent
b=p.LoadBoard(str(ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'))
def xy(v):return [p.ToMM(v.x),p.ToMM(v.y)]
z=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==p.In1_Cu)
ps=z.GetFilledPolysList(p.In1_Cu)
def points(chain):return [xy(chain.CPoint(i)) for i in range(chain.PointCount())]
polygons=[{'shell':points(ps.COutline(i)),'holes':[points(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]} for i in range(ps.OutlineCount())]
vias=[xy(t.GetPosition()) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='/GND']
out=ROOT/'docs/validation/ground-geometry.json';out.write_text(json.dumps({'polygons':polygons,'vias':vias}))
print('Module region GND vias:',[v for v in vias if v[1]<121])
