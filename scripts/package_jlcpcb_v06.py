"""Create versioned quotation BOM/CPL and Gerber package for the verified v0.6.

No order is submitted. Coordinates are read from KiCad; no PCB mutation.
Run with KiCad Python after export_jlcpcb_v06.py and rendering the fab JPG.
"""
from pathlib import Path
from collections import OrderedDict
import ast,csv,hashlib,json,zipfile
import wx,pcbnew as p
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'manufacturing/v0.6';DEST=OUT/'assembly';DEST.mkdir(exist_ok=True)
CAD=ROOT/'hardware/Matrix6/Matrix6.kicad_pcb';hashes=json.loads((ROOT/'docs/validation/cad-sha256.json').read_text())
for path,h in hashes.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
app=wx.App(False);b=p.LoadBoard(str(CAD));fps={f.GetReference():f for f in b.GetFootprints()}
bom=list(csv.DictReader((OUT/'review/Matrix6-KiCad-BOM-DRAFT.csv').open()));pos=list(csv.DictReader((OUT/'review/Matrix6-KiCad-positions.csv').open()))
refs={r['Reference'] for r in bom};assert refs=={r['Ref'] for r in pos}==set(fps)
assert len(refs)==len(bom)==len(pos)==48
# Previously selected exact parts, updated by the v0.6 circuit manifest.
old=list(csv.DictReader((ROOT/'manufacturing/v0.5/assembly/Matrix6-v0.5-BOM.csv').open()))
exact={ref:(r['Manufacturer Part Number'],r['JLCPCB Part #']) for r in old for ref in r['Designator'].split(',')}
for ref,d in json.loads((ROOT/'docs/reference/v0.6-parts.json').read_text()).items():
    if d['pcb'] is not None and d['mpn']:exact[ref]=(d['mpn'],d['lcsc'])
# 100 nF bypasses remain one specified dielectric/voltage group pending live matching.
comments={'D2':'LED Red 0603','D3':'LED Blue 0603','H1':'Female Socket 1x20 2.54mm Vertical','H2':'Female Socket 1x20 2.54mm Vertical',**{r:'100nF 50V X7R' for r in ['C4','C6','C7','C12']}}
groups=OrderedDict()
for row in bom:
    ref=row['Reference'];mpn,lcsc=exact.get(ref,('',''));name=mpn or comments.get(ref,row['Value']);fp=row['Footprint'].split(':')[-1]
    if fp.startswith(('C_0805','C_0603','R_0603','LED_0603')):fp=fp.split('_')[1]
    groups.setdefault((name,fp,lcsc,mpn),[]).append(ref)
bf=DEST/'Matrix6-v0.6-BOM.csv'
with bf.open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','JLCPCB Part #','Manufacturer Part Number','Quantity'])
    for (name,fp,lcsc,mpn),rr in groups.items():w.writerow([name,','.join(rr),fp,lcsc,mpn,len(rr)])
# Only non-centred connectors need a centroid offset. Fab outline geometry is
# measured in board coordinates, so the rear mirror is already applied.
centroids={};cf=DEST/'Matrix6-v0.6-CPL.csv'
with cf.open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Rotation','Layer'])
    for row in pos:
        ref=row['Ref'];x,y=float(row['PosX']),float(row['PosY']);fp=fps[ref]
        if ref in ['H1','H2','J2','J3']:
            layer=p.F_Fab if fp.GetLayer()==p.F_Cu else p.B_Fab
            boxes=[g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer()==layer and isinstance(g,p.PCB_SHAPE)]
            if ref=='J2':
                # Its Fab layer also depicts a protruding card; exclude that
                # travel outline from the actual connector body centroid.
                courtyard=[g.GetBoundingBox() for g in fp.GraphicalItems() if g.GetLayer()==p.B_CrtYd]
                low=min(q.GetTop() for q in courtyard);high=max(q.GetBottom() for q in courtyard)
                boxes=[q for q in boxes if q.GetTop()>=low and q.GetBottom()<=high]
            assert boxes,ref
            x=(min(p.ToMM(q.GetLeft()) for q in boxes)+max(p.ToMM(q.GetRight()) for q in boxes))/2
            y=-(min(p.ToMM(q.GetTop()) for q in boxes)+max(p.ToMM(q.GetBottom()) for q in boxes))/2
            centroids[ref]={'anchor':[float(row['PosX']),float(row['PosY'])],'fab_body_center':[x,y]}
        w.writerow([ref,f'{x:.6f}',f'{y:.6f}',f'{float(row["Rot"])%360:.6f}','Top' if row['Side']=='top' else 'Bottom'])
files=sorted(q for q in (OUT/'gerber').iterdir() if q.suffix!='.gbrjob')
assert {'.gtl','.g1','.g2','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gbp','.gm1'}<={q.suffix for q in files}
assert sum(q.suffix=='.drl' for q in files)==2
assert (OUT/'gerber/Matrix6-fabrication-requirements.jpg').exists()
with zipfile.ZipFile(OUT/'Matrix6-v0.6-Gerber.zip','w',zipfile.ZIP_DEFLATED) as z:
    for q in files:z.write(q,q.name)
with zipfile.ZipFile(OUT/'Matrix6-v0.6-Gerber.zip') as z:assert z.testzip() is None
report={'status':'QUOTATION; live parts matching, model rotations and CAM review pending','cad_pcb_sha256':hashlib.sha256(CAD.read_bytes()).hexdigest(),'component_count':len(refs),'bom_groups':len(groups),'top_count':sum(r['Side']=='top' for r in pos),'bottom_count':sum(r['Side']=='bottom' for r in pos),'centroid_adjustments':centroids,'coordinate_origin':'KiCad absolute origin, same as Gerber, Y inverted to Cartesian; actual KiCad side rotations','unmatched':[','.join(rr) for (_,_,lcsc,_),rr in groups.items() if not lcsc]}
(DEST/'export-validation.json').write_text(json.dumps(report,indent=2)+'\n')
manifest={**report,'cad_hashes':hashes,'files':{str(q.relative_to(OUT)):hashlib.sha256(q.read_bytes()).hexdigest() for q in OUT.rglob('*') if q.is_file() and q.name!='source-manifest.json'}}
(OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report,indent=2))
