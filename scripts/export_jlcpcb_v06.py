"""Export the verified CAD for JLCPCB prototype quotation; no routing or CAD edits.

The BOM and positions are KiCad review exports, not a released JLCPCB assembly set.
Render the generated fabrication SVG to JPEG and include it in the upload ZIP.
"""
from pathlib import Path
import hashlib, html, json, os, subprocess
from sexpr import parse, children, child
from manufacturing_revision import REV, OUT, RADIUS

ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT / 'hardware/Matrix6/Matrix6.kicad_pcb'
MAC = Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
CLI = os.environ.get('KICAD_CLI', str(MAC) if MAC.exists() else 'kicad-cli')
for path, expected in json.loads((ROOT/'docs/validation/cad-sha256.json').read_text()).items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path
for name in ['gerber', 'review']:
    (OUT/name).mkdir(parents=True, exist_ok=True)

def run(*args):
    subprocess.run([CLI, *map(str, args)], check=True, cwd=ROOT)

run('pcb', 'export', 'gerbers', '--layers',
    'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts',
    '--no-x2', '--no-netlist', '--subtract-soldermask', '--disable-aperture-macros',
    '-o', OUT/'gerber/', CAD)
run('pcb', 'export', 'drill', '--format', 'excellon', '--drill-origin', 'absolute',
    '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal',
    '--excellon-oval-format', 'alternate', '--excellon-separate-th',
    '--generate-report', '--report-path', OUT/'review/drill-report.txt',
    '-o', OUT/'gerber/', CAD)
run('pcb', 'export', 'pos', '--side', 'both', '--format', 'csv', '--units', 'mm',
    '--exclude-dnp', '-o', OUT/'review/Matrix6-KiCad-positions.csv', CAD)
run('sch', 'export', 'bom', '--fields', 'Reference,Value,Footprint,MPN,Manufacturer,QUANTITY',
    '--labels', 'Reference,Value,Footprint,MPN,Manufacturer,Quantity', '--exclude-dnp',
    '-o', OUT/'review/Matrix6-KiCad-BOM-DRAFT.csv', CAD.with_suffix('.kicad_sch'))

b = parse(CAD.read_text())
pieces = ['<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1400" viewBox="0 0 1800 1400">',
          '<rect width="1800" height="1400" fill="white"/>',
          '<style>text{font-family:Arial,sans-serif;fill:#172337} .small{font-size:22px}</style>']
def text(x, y, value, size=27):
    pieces.append(f'<text x="{x}" y="{y}" font-size="{size}">{html.escape(value)}</text>')
text(60, 65, f'Matrix Six v{REV} — PCB FABRICATION / IMPEDANCE REQUIREMENTS', 37)
text(60, 108, 'Prototype quotation • CAD hash in source-manifest.json • All dimensions in mm • 2026-09-07', 23)
text(60, 160, 'USB routing', 25)
scale = 14
def xy(x, y): return 90+(x-97.46)*scale, 200+(y-100)*scale
x,y=xy(97.46,100)
pieces.append(f'<rect x="{x}" y="{y}" width="{40.64*scale}" height="{61*scale}" rx="{RADIUS*scale}" fill="#f5f7f8" stroke="#253649" stroke-width="3"/>')
for refx in [101.27,134.29]:
    for pin in range(20):
        px,py=xy(refx,153.26-pin*2.54)
        pieces.append(f'<circle cx="{px}" cy="{py}" r="5" fill="none" stroke="#8793a0" stroke-width="2"/>')
colors={'/USB_P':'#bd2e47','/USB_A_P':'#bd2e47','/MCU_USB_P':'#bd2e47',
        '/USB_N':'#145daa','/MCU_USB_N':'#145daa'}
for seg in children(b,'segment'):
    net=child(seg,'net')[1]
    if net not in colors: continue
    ax,ay=xy(*map(float,child(seg,'start')[1:3])); bx,by=xy(*map(float,child(seg,'end')[1:3]))
    pieces.append(f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}" stroke="{colors[net]}" stroke-width="{float(child(seg,"width")[1])*scale}" stroke-linecap="round"/>')
for label, ax,ay,aw,ah in [('U1',108.78,93.75,18,25.5),('J1 USB-C',113.31,154.325,8.94,7.35)]:
    px,py=xy(ax,ay)
    pieces.append(f'<rect x="{px}" y="{py}" width="{aw*scale}" height="{ah*scale}" fill="none" stroke="#647488" stroke-width="2" stroke-dasharray="7 5"/>')
    text(px+4,py+25,label,21)
for label,px,py in [('R3/R4',106.5,116.3),('R11 0R',117.53,151.75)]:
    xx,yy=xy(px,py);text(xx+85 if label.startswith('R11') else xx-15,yy-15,label,20)
text(90,1115,'D+ red / D− blue; all USB copper on L1.',23)
text(90,1150,f'Board: 40.64 × 61.00; 4 corners R{RADIUS:g}',23)
text(90,1185,'KiCad coordinates: X=97.46..138.10',23)
text(90,1220,'Y=100..161 (downward). Gerber Y is negative.',22)

rows=[
('CONTROLLED IMPEDANCE',34),
('Target: differential 90 ohm ±10%',29),
('Signal: L1 / F.Cu, USB_P and USB_N',26),
('Reference: L2 / In1.Cu, continuous GND',26),
('Uniform width: 0.280  |  edge gap: 0.200',26),
('L1 coplanar GND clearance: 0.500',26),
('Stackup: JLC04161H-7628, nominal 1.6 mm',26),
('L1/L4 copper: 0.035; L2/L3 copper: 0.0152',24),
('L1-L2 / L3-L4 dielectric: 0.2104 (7628)',24),
('L2-L3 dielectric core: 1.065',24),
('Main controlled section: KiCad Y=122..145.85.',24),
('0.200-wide pad escapes are local transitions.',24),
('CAM must review width/gap for the actual material.',24),
('Provide impedance calculation, coupon and report.',24),
('Submit CAM geometry changes for customer review.',24),
('',20),
('LAYER ORDER / DRILL',34),
('L1: Matrix6-F_Cu.gtl  /  L2: Matrix6-In1_Cu.g1',23),
('L3: Matrix6-In2_Cu.g2 /  L4: Matrix6-B_Cu.gbl',23),
('PTH: 12 × 0.200 thermal holes in U1 pad 41;',24),
('All drill counts and sizes: see drill-report.txt.',24),
('Open connector lead holes and USB plated slots.',24),
('NPTH: 2 × 0.650 USB positioning holes.',24),
('Epoxy-fill and copper-cap U1/U2 thermal vias.',24),
('These are thermal vias, NOT component lead holes.',24),
('Keep connector holes, USB slots and NPTH OPEN.',24),
('Preserve soldermask openings as supplied.',24),
]
yy=170
for row,size in rows:
    text(750,yy,row,size);yy+=41
text(60,1330,'USB connector body: no L1 tracks, vias or copper fill under x113.31..122.25 / y154.325..161.675.',25)
text(60,1370,'Keep the supplied pads, board edge, RF antenna area and continuous L2 ground. This sheet is fabrication guidance, not a Gerber layer.',23)
pieces.append('</svg>')
(OUT/'review/Matrix6-fabrication-requirements.svg').write_text('\n'.join(pieces)+'\n')
print('CAD unchanged. Render fabrication requirements to JPEG before packaging.')
