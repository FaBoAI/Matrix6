"""Check the rear card withdrawal corridor against actual CAD courtyards.

This measures geometry only; it never finds routes or changes the PCB.
"""
from pathlib import Path
import hashlib,html,json
import pcbnew as p
import wx
app=wx.App(False);ROOT=Path(__file__).resolve().parent.parent
board=ROOT/'hardware/Matrix6/Matrix6.kicad_pcb';b=p.LoadBoard(str(board))
fps={f.GetReference():f for f in b.GetFootprints()};slot=fps['J2']
def xy(v):return [p.ToMM(v.x),p.ToMM(v.y)]
def bounds(f,layer):
    boxes=[g.GetBoundingBox() for g in f.GraphicalItems() if g.GetLayer()==layer]
    assert boxes, f'{f.GetReference()} has no courtyard'
    return [min(p.ToMM(q.GetLeft()) for q in boxes),min(p.ToMM(q.GetTop()) for q in boxes),max(p.ToMM(q.GetRight()) for q in boxes),max(p.ToMM(q.GetBottom()) for q in boxes)]
zone=next(z for z in b.Zones() if z.GetZoneName()=='SD_CARD_WITHDRAWAL_AND_FINGER_CLEARANCE')
assert zone.GetIsRuleArea() and zone.GetLayer()==p.B_Cu and zone.GetDoNotAllowFootprints()
assert slot.GetLayer()==p.B_Cu and abs(slot.GetOrientationDegrees())<1e-6
poly=zone.Outline().COutline(0);points=[xy(poly.CPoint(i)) for i in range(poly.PointCount())]
corridor=[min(q[0] for q in points),min(q[1] for q in points),max(q[0] for q in points),max(q[1] for q in points)]
assert corridor==[109.9,100.5,125.7,123.0]
rear={r:bounds(f,p.B_CrtYd) for r,f in fps.items() if f.GetLayer()==p.B_Cu}
def overlap(a,c):return min(a[2],c[2])>max(a[0],c[0]) and min(a[3],c[3])>max(a[1],c[1])
blocked=[r for r,box in rear.items() if overlap(box,corridor)]
assert not blocked,blocked
assert all(xy(q.GetPosition())[1]>139 for q in slot.Pads() if q.GetNumber() in list('12345678'))
report={'pcb_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),'status':'PASS',
 'side':'B.Cu','slot_rotation_deg':slot.GetOrientationDegrees(),'opening_direction':'toward antenna / decreasing PCB Y',
 'component_keepout_mm':corridor,'keepout_width_mm':15.8,'keepout_depth_mm':22.5,
 'rear_courtyards_mm':rear,'obstructing_components':blocked,
 'scope':'Rear courtyard clearance for card withdrawal on the bare PCB. Enclosure, installed shield stack, solder protrusions and real card/finger handling require a physical fit check.'}
(ROOT/'docs/validation/sd-access.json').write_text(json.dumps(report,indent=2)+'\n')
# A dimensional drawing derived from the saved CAD, viewed from the rear.
s=12;ox=65;oy=80
def pos(x,y):return ox+(138.1-x)*s,oy+(y-100)*s
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="910" viewBox="0 0 1080 910">','<rect width="1080" height="910" fill="#f4f7fa"/>','<style>text{font-family:Arial,sans-serif;fill:#173047} .small{font-size:15px}</style>']
def text(x,y,label,size=20):svg.append(f'<text x="{x}" y="{y}" font-size="{size}">{html.escape(label)}</text>')
def rect(box,fill,stroke,dash=''):
    x,y=pos(box[2],box[1]);svg.append(f'<rect x="{x}" y="{y}" width="{(box[2]-box[0])*s}" height="{(box[3]-box[1])*s}" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-dasharray="{dash}"/>')
text(65,40,'Matrix Six v0.6 / microSD access — rear view',27)
rect([97.46,100,138.1,161],'white','#173047')
rect(corridor,'#dcf7e8','#179763','7 5')
for r,box in rear.items():
    rect(box,'#dce8f9' if r=='J2' else '#e9edf1','#4e6781')
    x,y=pos((box[0]+box[2])/2,(box[1]+box[3])/2);text(x-10,y+5,r,14)
for r in ['H1','H2']:
    for pad in fps[r].Pads():
        x,y=pos(*xy(pad.GetPosition()));svg.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#f1c55c" stroke="#705812"/>')
x,y=pos(117.8,121.8);xt,yt=pos(117.8,102.8)
svg.append(f'<path d="M{x},{y} L{xt},{yt} m-10,16 l10,-16 l10,16" fill="none" stroke="#138c5a" stroke-width="5"/>')
text(625,110,'Clear card withdrawal corridor',24)
for i,line in enumerate(['15.8 mm wide × 22.5 mm deep','Opening faces the antenna edge.','No rear component courtyard overlaps.','A rear placement keepout protects the path.','','J2: rear microSD slot','J3: rear LiPo connector','Charger and battery parts are behind J2.','','USB / RESET / BOOT remain at the lower edge.','','Dimensions are PCB coordinates in mm.','Check card handling after assembly.']):text(625,150+i*32,line,17)
text(65,855,'Green: reserved access area   Blue: SD slot courtyard   Gray: other rear components',16)
text(65,883,'No autorouter used. CAD courtyard check passed; this drawing is not a 3D collision simulation.',14)
svg.append('</svg>');(ROOT/'docs/validation/sd-access.svg').write_text('\n'.join(svg))
print('PASS: rear SD mouth points toward clear edge; 15.8 x 22.5 mm corridor, no component overlaps.')
