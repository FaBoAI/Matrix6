"""Apply the v0.7 R2 outline to the saved v0.6 board; no routing.

Run with KiCad Python. Refill and validate with verify_project.py afterwards.
"""
from pathlib import Path
import hashlib, json, math
import wx, pcbnew as p
from sexpr import parse, child, children, dump

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / 'hardware/Matrix6/Matrix6.kicad_pcb'
SCH = PCB.with_suffix('.kicad_sch')
app = wx.App(False)
b = p.LoadBoard(str(PCB))
assert b.GetTitleBlock().GetRevision() == '0.6', 'Apply only once to v0.6'
before = parse(PCB.read_text())
before_hash = hashlib.sha256(PCB.read_bytes()).hexdigest()
edges = [g for g in b.GetDrawings() if g.GetLayer() == p.Edge_Cuts]
assert len(edges) == 4 and all(g.GetShape() == p.SHAPE_T_SEGMENT for g in edges)
x0, x1, y0, y1, r = 97.46, 138.10, 100.0, 161.0, 2.0
for g in edges:
    b.Remove(g)
def pt(xy): return p.VECTOR2I(round(xy[0]*1e6), round(xy[1]*1e6))
def line(a, z):
    g = p.PCB_SHAPE(b); g.SetShape(p.SHAPE_T_SEGMENT)
    g.SetStart(pt(a)); g.SetEnd(pt(z)); finish(g)
def arc(a, m, z):
    g = p.PCB_SHAPE(b); g.SetShape(p.SHAPE_T_ARC)
    g.SetArcGeometry(pt(a), pt(m), pt(z)); finish(g)
def finish(g):
    g.SetLayer(p.Edge_Cuts); g.SetWidth(p.FromMM(.05)); b.Add(g)
q = r / math.sqrt(2)
line((x0+r,y0),(x1-r,y0))
arc((x1-r,y0),(x1-r+q,y0+r-q),(x1,y0+r))
line((x1,y0+r),(x1,y1-r))
arc((x1,y1-r),(x1-r+q,y1-r+q),(x1-r,y1))
line((x1-r,y1),(x0+r,y1))
arc((x0+r,y1),(x0+r-q,y1-r+q),(x0,y1-r))
line((x0,y1-r),(x0,y0+r))
arc((x0,y0+r),(x0+r-q,y0+r-q),(x0+r,y0))
b.GetTitleBlock().SetRevision('0.7')
p.SaveBoard(str(PCB), b)
sch_text = SCH.read_text()
assert sch_text.count('(rev "0.6")') == 1
SCH.write_text(sch_text.replace('(rev "0.6")', '(rev "0.7")'))
after = parse(PCB.read_text())
for tag in ['footprint', 'segment', 'arc', 'via']:
    assert sorted(dump(x) for x in children(before,tag)) == sorted(dump(x) for x in children(after,tag)), tag
report = {
    'previous_pcb_sha256': before_hash,
    'corner_radius_mm': r, 'outline_bounds_mm': [x0,y0,x1,y1],
    'straight_edges': 4, 'quarter_circle_arcs': 4,
    'footprints_and_routed_copper_unchanged': True,
    'nominal_area_mm2': (x1-x0)*(y1-y0)-(4-math.pi)*r*r,
    'validation': 'Run verify_project.py for the refilled saved board before fabrication export.'
}
(ROOT/'docs/validation/rounded-corners.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
