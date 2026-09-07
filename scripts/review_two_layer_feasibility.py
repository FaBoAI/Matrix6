"""Read the current PCB and report what a two-layer redesign must address.

Does not edit, refill, or route the board. Run with KiCad Python.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, math
import wx, pcbnew as p

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / 'hardware/Matrix6/Matrix6.kicad_pcb'
OUT = ROOT / 'docs/analysis'
OUT.mkdir(exist_ok=True)
before = CAD.read_bytes()
app = wx.App(False)
b = p.LoadBoard(str(CAD))
tracks = defaultdict(lambda: {'segments': 0, 'length_mm': 0, 'nets': set()})
vias = Counter()
for t in b.GetTracks():
    if isinstance(t, p.PCB_VIA):
        vias[(p.ToMM(t.GetDrillValue()), p.ToMM(t.GetWidth(p.F_Cu)))]+=1
        continue
    entry = tracks[b.GetLayerName(t.GetLayer())]
    entry['segments'] += 1
    entry['length_mm'] += p.ToMM(t.GetLength())
    entry['nets'].add(t.GetNetname())
for entry in tracks.values():
    entry['nets'] = sorted(entry['nets'])
    entry['length_mm'] = round(entry['length_mm'], 3)

thermal_holes = []
for f in b.GetFootprints():
    for q in f.Pads():
        d = q.GetDrillSize()
        if d.x and min(d.x, d.y) < p.FromMM(.3):
            thermal_holes.append({'reference': f.GetReference(), 'pad': q.GetNumber(),
                'drill_mm': [p.ToMM(d.x),p.ToMM(d.y)],
                'pad_size_mm': [p.ToMM(q.GetSize().x),p.ToMM(q.GetSize().y)]})

def xy(v): return tuple(round(p.ToMM(q),6) for q in (v.x,v.y))
def point(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
planes = {}
for layer in [p.In1_Cu, p.B_Cu]:
    z = next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==layer)
    polys = z.GetFilledPolysList(layer)
    samples = 0
    missing = Counter()
    for t in b.GetTracks():
        if isinstance(t,p.PCB_VIA) or 'USB' not in t.GetNetname(): continue
        a,c = xy(t.GetStart()),xy(t.GetEnd())
        dx,dy = c[0]-a[0],c[1]-a[1]
        length = math.hypot(dx,dy)
        if not length: continue
        steps = math.ceil(length/.025)
        for i in range(steps+1):
            u=i/steps
            for off in [0,-p.ToMM(t.GetWidth())/2-.05,p.ToMM(t.GetWidth())/2+.05]:
                x=a[0]+u*dx-dy/length*off
                y=a[1]+u*dy+dx/length*off
                samples+=1
                if not polys.Contains(point(x,y)): missing[t.GetNetname()]+=1
    planes[b.GetLayerName(layer)] = {'filled_regions':polys.OutlineCount(),
        'samples':samples,'missing_ground_samples':sum(missing.values()),
        'missing_by_net':dict(missing)}

result = {'status':'FEASIBILITY REVIEW ONLY; no two-layer PCB has been released',
    'pcb_sha256':hashlib.sha256(before).hexdigest(),
    'revision':b.GetTitleBlock().GetRevision(),
    'tracks_by_layer':tracks,
    'via_sizes':[{'drill_mm':d,'diameter_mm':w,'count':n} for (d,w),n in vias.items()],
    'plated_pads_with_drill_below_0_3mm':thermal_holes,
    'existing_USB_reference_coverage':planes,
    'interpretation':[
        'In2.Cu signal and power tracks must be rerouted onto the outer layers.',
        'The existing B.Cu pour is not a continuous reference under the USB routes; it cannot replace In1.Cu as-is.',
        'The twelve 0.2 mm holes have 0.6 mm copper pads. The previous 0.2/(0.3/0.35) quote selection is unnecessarily restrictive.',
        'Small-hole quote eligibility must be confirmed against Gerber/CAM; this review does not waive filled/capped thermal-hole requirements.',
        'JLCPCB standard FR4 controlled-impedance service lists four layers and above. A two-layer design needs a different validation agreement.'
    ],
    'sources':[
        'https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html',
        'https://jlcpcb.com/capabilities/pcb-capabilities/',
        'https://cart.jlcpcb.com/quote'
    ]}
assert CAD.read_bytes()==before
(OUT/'two-layer-feasibility.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'layers':{k:{'segments':v['segments'],'length_mm':v['length_mm'],'nets':len(v['nets'])} for k,v in tracks.items()},
    'planes':planes,'small_holes':len(thermal_holes),'CAD_unchanged':True},indent=2))
