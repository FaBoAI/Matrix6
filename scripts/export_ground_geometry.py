"""Export the filled L2 polygon and GND via locations for independent DC analysis."""
from pathlib import Path
import json,wx,pcbnew as p
app=wx.App(False);ROOT=Path(__file__).resolve().parent.parent
b=p.LoadBoard(str(ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'))
def xy(v):return [p.ToMM(v.x),p.ToMM(v.y)]
layer=p.B_Cu if b.GetCopperLayerCount()==2 else p.In1_Cu
z=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==layer)
ps=z.GetFilledPolysList(layer)
def points(chain):return [xy(chain.CPoint(i)) for i in range(chain.PointCount())]
polygons=[{'shell':points(ps.COutline(i)),'holes':[points(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]} for i in range(ps.OutlineCount())]
vias=[xy(t.GetPosition()) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='/GND']
data={'layer':b.GetLayerName(layer),'copper_mm':.035 if b.GetCopperLayerCount()==2 else .0152,'polygons':polygons,'vias':vias}
if b.GetCopperLayerCount()==2:
    data['layers']={}
    for la in [p.F_Cu,p.B_Cu]:
        zz=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==la);pp=zz.GetFilledPolysList(la)
        data['layers'][b.GetLayerName(la)]=[{'shell':points(pp.COutline(i)),'holes':[points(pp.CHole(i,j)) for j in range(pp.HoleCount(i))]} for i in range(pp.OutlineCount())]
    data['ground_copper']={}
    for la in [p.F_Cu,p.B_Cu]:
        polys=[]
        items=[q for f in b.GetFootprints() for q in f.Pads() if q.GetNetname()=='/GND' and q.IsOnLayer(la)]
        items += [t for t in b.GetTracks() if t.GetNetname()=='/GND' and (isinstance(t,p.PCB_VIA) or t.GetLayer()==la)]
        for item in items:
            pp=p.SHAPE_POLY_SET();item.TransformShapeToPolygon(pp,la,0,p.FromMM(.005),p.ERROR_INSIDE)
            polys += [{'shell':points(pp.COutline(i)),'holes':[points(pp.CHole(i,j)) for j in range(pp.HoleCount(i))]} for i in range(pp.OutlineCount())]
        data['ground_copper'][b.GetLayerName(la)]=polys
    data['ground_holes']=[{'at':xy(q.GetPosition()),'size':xy(q.GetDrillSize()),'angle':q.GetOrientationDegrees()} for f in b.GetFootprints() for q in f.Pads() if q.GetNetname()=='/GND' and q.GetDrillSize().x>0]
    data['ground_holes'] += [{'at':xy(t.GetPosition()),'size':[p.ToMM(t.GetDrillValue())]*2,'angle':0} for t in b.GetTracks() if t.GetNetname()=='/GND' and isinstance(t,p.PCB_VIA)]
    data['stitches']=[{'at':xy(t.GetPosition()),'drill_mm':p.ToMM(t.GetDrillValue())} for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='/GND']
    data['stitches'] += [{'at':xy(q.GetPosition()),'drill_mm':p.ToMM(q.GetDrillSize().x)} for f in b.GetFootprints() for q in f.Pads() if q.GetNetname()=='/GND' and q.GetAttribute()==p.PAD_ATTRIB_PTH]
out=ROOT/'docs/validation/ground-geometry.json';out.write_text(json.dumps(data))
print('Module region GND vias:',[v for v in vias if v[1]<121])
