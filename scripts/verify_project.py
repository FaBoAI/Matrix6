"""Validate the saved project. Does not regenerate or autoroute the board."""
from pathlib import Path
import os,subprocess,sys,hashlib,json
ROOT=Path(__file__).resolve().parent.parent
CAD=ROOT/'hardware/Matrix6/Matrix6'
REPORT=ROOT/'docs/validation';REPORT.mkdir(exist_ok=True,parents=True)
MAC=Path('/Applications/KiCad/KiCad.app/Contents')
CLI=os.environ.get('KICAD_CLI',str(MAC/'MacOS/kicad-cli') if MAC.exists() else 'kicad-cli')
PYTHON=os.environ.get('KICAD_PYTHON',str(MAC/'Frameworks/Python.framework/Versions/3.9/bin/python3') if MAC.exists() else sys.executable)
def run(*args):subprocess.run(list(args),check=True,cwd=ROOT)
run(CLI,'sch','erc','--severity-all','--exit-code-violations','--format','json','-o',str(REPORT/'erc.json'),str(CAD.with_suffix('.kicad_sch')))
run(CLI,'pcb','drc','--schematic-parity','--all-track-errors','--severity-all','--refill-zones','--save-board','--exit-code-violations','--format','json','-o',str(REPORT/'drc.json'),str(CAD.with_suffix('.kicad_pcb')))
run(PYTHON,'scripts/audit_electrical_layout.py')
run(PYTHON,'scripts/verify_usb_keepout.py')
run(sys.executable,'scripts/verify_matrix5_compat.py')
run(PYTHON,'scripts/export_ground_geometry.py')
analysis=os.environ.get('ANALYSIS_PYTHON')
if analysis:run(analysis,'scripts/ground_plane_dc.py')
else:print('DC plane mesh not rerun: set ANALYSIS_PYTHON to a Python with numpy/scipy/shapely/matplotlib.')
files=[p for p in (ROOT/'hardware/Matrix6').rglob('*') if p.is_file() and (p.suffix in ['.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_dru','.kicad_mod'] or p.name=='fp-lib-table')]
(REPORT/'cad-sha256.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2)+'\n')
print('All requested checks passed; CAD hashes saved.')
