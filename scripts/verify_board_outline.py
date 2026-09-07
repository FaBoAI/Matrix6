"""Verify the saved R2 outline and two-layer drilling limits; no mutations."""
from pathlib import Path
import json,math,subprocess,hashlib
from sexpr import parse,children,child,dump
ROOT=Path(__file__).resolve().parent.parent;cad=ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'
b=parse(cad.read_text());old=parse(subprocess.check_output(['git','show','f12c10f:hardware/Matrix6/Matrix6.kicad_pcb'],cwd=ROOT,text=True))
def edges(tree):return sorted(dump(q) for tag in ['gr_line','gr_arc'] for q in children(tree,tag) if child(q,'layer')[1]=='Edge.Cuts')
assert edges(b)==edges(old),'R2 outline changed'
counts={tag:sum(child(q,'layer')[1]=='Edge.Cuts' for q in children(b,tag)) for tag in ['gr_line','gr_arc']};assert counts=={'gr_line':4,'gr_arc':4}
radii=[]
for q in children(b,'gr_arc'):
 if child(q,'layer')[1]!='Edge.Cuts':continue
 a,m,c=[tuple(map(float,child(q,k)[1:3])) for k in ['start','mid','end']]
 A=math.dist(m,c);B=math.dist(a,c);C=math.dist(a,m);area2=abs((m[0]-a[0])*(c[1]-a[1])-(m[1]-a[1])*(c[0]-a[0]));radius=A*B*C/(2*area2);radii.append(radius);assert abs(radius-2)<2e-5
pads=[]
for f in children(b,'footprint'):
 ref=next(q[2] for q in children(f,'property') if q[1]=='Reference')
 for q in children(f,'pad'):
  if q[2]!='thru_hole':continue
  size=list(map(float,child(q,'size')[1:3]));drill=child(q,'drill');dd=list(map(float,drill[2:4] if drill[1]=='oval' else [drill[1],drill[1]]));annulus=min((x-y)/2 for x,y in zip(size,dd));assert annulus>=.18-1e-6,(ref,q[1],annulus)
  assert min(dd)>=.3-1e-6,(ref,q[1],dd)
  pads.append({'reference':ref,'pad':q[1],'drill_mm':dd,'minimum_annulus_mm':annulus})
thermal=[q for q in pads if q['reference']=='U1' and q['pad']=='41'];assert len(thermal)==12 and all(abs(q['minimum_annulus_mm']-.25)<1e-6 for q in thermal)
report={'pcb_sha256':hashlib.sha256(cad.read_bytes()).hexdigest(),'revision':child(child(b,'title_block'),'rev')[1],'outline_preserved_from':'v0.7 / f12c10f','corner_radius_mm':2,'measured_arc_radii_mm':radii,'outline_bounds_mm':[97.46,100,138.1,161],'straight_edges':4,'quarter_circle_arcs':4,'nominal_area_mm2':40.64*61-(4-math.pi)*4,'minimum_PTH_annulus_mm':min(q['minimum_annulus_mm'] for q in pads),'PTH_pads':pads}
(ROOT/'docs/validation/rounded-corners.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: R2 outline preserved; PTH holes >=0.3 mm, annulus >=0.18 mm; thermal annulus 0.25 mm.')
