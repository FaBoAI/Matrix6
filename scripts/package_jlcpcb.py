"""Package fabrication layers and the rendered JPG; exclude review BOM/CPL."""
from pathlib import Path
import csv,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'manufacturing/v0.5'
required={'.gtl','.g1','.g2','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gbp','.gm1'}
files=sorted(p for p in (OUT/'gerber').iterdir() if p.suffix!='.gbrjob')
assert required <= {p.suffix for p in files}
assert sum(p.suffix=='.drl' for p in files)==2
assert (OUT/'gerber/Matrix6-fabrication-requirements.jpg').exists()
bom=list(csv.DictReader((OUT/'review/Matrix6-KiCad-BOM-DRAFT.csv').open()))
pos=list(csv.DictReader((OUT/'review/Matrix6-KiCad-positions.csv').open()))
assert len(bom)==len(pos)==32
assert {p['Reference'] for p in bom}=={p['Ref'] for p in pos}
assert all(p['Side']=='top' for p in pos)
with zipfile.ZipFile(OUT/'Matrix6-v0.5-Gerber.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.name)
with zipfile.ZipFile(OUT/'Matrix6-v0.5-Gerber.zip') as z:
    assert z.testzip() is None
for path,expected in json.loads((ROOT/'docs/validation/cad-sha256.json').read_text()).items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
manifest={'cad_source_commit':'d1438c606553286f8075416b602664ae09d1bd65',
          'cad_pcb_sha256':hashlib.sha256((ROOT/'hardware/Matrix6/Matrix6.kicad_pcb').read_bytes()).hexdigest(),
          'assembly_status':'NOT RELEASED; raw KiCad BOM/positions are for review only',
          'reference_parity':{'bom_count':len(bom),'position_count':len(pos),'all_on_top':True},
          'files':{str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='source-manifest.json'}}
(OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('PASS: verified CAD unchanged; 32 BOM/position references match; ZIP valid, fabrication JPG included.')
