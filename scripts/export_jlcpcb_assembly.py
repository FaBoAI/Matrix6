"""Export quotation BOM/CPL. This does not release a PCBA order for manufacture."""
import csv
import hashlib
import json
import math
from collections import OrderedDict
from pathlib import Path

from sexpr import child, children, parse

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'manufacturing/v0.5'
DEST = OUT / 'assembly'
DEST.mkdir(exist_ok=True)
manifest = json.loads((OUT / 'source-manifest.json').read_text())
pcb_path = ROOT / 'hardware/Matrix6/Matrix6.kicad_pcb'
assert hashlib.sha256(pcb_path.read_bytes()).hexdigest() == manifest['cad_pcb_sha256']
for name in ['Matrix6-KiCad-BOM-DRAFT.csv', 'Matrix6-KiCad-positions.csv']:
    path = OUT / 'review' / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest['files']['review/' + name]
bom = list(csv.DictReader((OUT / 'review/Matrix6-KiCad-BOM-DRAFT.csv').open()))
pos = list(csv.DictReader((OUT / 'review/Matrix6-KiCad-positions.csv').open()))
refs = {r['Reference'] for r in bom}
assert len(refs) == len(bom) == len(pos) == 32
assert refs == {r['Ref'] for r in pos}
assert all(r['Side'] == 'top' for r in pos)

# Exact part numbers already specified by the circuit/footprint. Blank JLC
# numbers deliberately request matching, never an unreviewed substitution.
exact = {
    'C5': ('CL10B105KO8NNNC', 'Samsung Electro-Mechanics', 'C59782'),
    'D1': ('SS14-E3/61T', 'Vishay', 'C47460'),
    'F1': ('MF-NSMF110/16X-2', 'Bourns', 'C25415531'),
    'J1': ('USB4105-GF-A-120', 'GCT', 'C5184243'),
    'L1': ('SRN4018-4R7M', 'Bourns', 'C780206'),
    'R11': ('CRCW06030000Z0EA', 'Vishay', 'C844915'),
    'SW1': ('B3U-1000P', 'Omron', 'C231329'),
    'SW2': ('B3U-1000P', 'Omron', 'C231329'),
    'U1': ('ESP32-S3-WROOM-1-N8R8', 'Espressif Systems', 'C2913201'),
    'U2': ('AP63203WU-7', 'Diodes Incorporated', 'C780769'),
    'U3': ('USBLC6-2SC6', 'STMicroelectronics', 'C7519'),
}
for designators, mpn, jlc in [
        (['R1', 'R2'], '0603WAF5101T5E', 'C23186'),
        (['R3', 'R4'], '0603WAF220JT5E', 'C23345'),
        (['R5', 'R6', 'R7', 'R8'], '0603WAF1002T5E', 'C25804'),
        (['R9', 'R10'], '0603WAF1001T5E', 'C21190')]:
    for ref in designators:
        exact[ref] = (mpn, 'UNI-ROYAL', jlc)
packages = {
    'C_0805_2012Metric': '0805', 'C_0603_1608Metric': '0603',
    'R_0603_1608Metric': '0603', 'LED_0603_1608Metric': '0603',
    'D_SMA': 'SMA', 'Fuse_1206_3216Metric': '1206',
    'PinSocket_1x20_P2.54mm_Vertical': 'Through Hole 1x20 P2.54mm Female',
    'USB4105_NoUnderbodyCopper': 'USB4105-GF-A-120',
    'L_Bourns-SRN4018': '4x4mm SRN4018',
    'SW_SPST_B3U-1000P': 'SMD 3x2.5mm',
    'ESP32-S3-WROOM-1_Edge': 'SMD 18x25.5mm',
    'TSOT-23-6': 'TSOT-23-6', 'SOT-23-6': 'SOT-23-6',
}
comments = {'D2': 'LED Red', 'D3': 'LED Blue',
            'H1': 'Female Socket 1x20 2.54mm Vertical',
            'H2': 'Female Socket 1x20 2.54mm Vertical'}
grouped = OrderedDict()
for r in bom:
    ref = r['Reference']
    mpn, manufacturer, jlc = exact.get(ref, ('', '', ''))
    comment = mpn or comments.get(ref, r['Value'])
    footprint = packages[r['Footprint'].split(':')[-1]]
    key = (comment, footprint, jlc, manufacturer, mpn)
    grouped.setdefault(key, []).append(ref)
bom_file = DEST / 'Matrix6-v0.5-BOM.csv'
with bom_file.open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Comment', 'Designator', 'Footprint', 'JLCPCB Part #',
                     'Manufacturer', 'Manufacturer Part Number', 'Quantity'])
    for (comment, footprint, jlc, manufacturer, mpn), designators in grouped.items():
        writer.writerow([comment, ','.join(designators), footprint, jlc,
                         manufacturer, mpn, len(designators)])

# Headers have their anchor on pin 1, not the body midpoint. Derive the
# physical body center from F.Fab and transform the offset into CPL axes.
pcb = parse(pcb_path.read_text())
footprints = {next(p[2] for p in children(fp, 'property') if p[1] == 'Reference'): fp
              for fp in children(pcb, 'footprint')}
assert refs == set(footprints)
centroid_changes = {}
cpl_file = DEST / 'Matrix6-v0.5-CPL.csv'
with cpl_file.open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Designator', 'Mid X', 'Mid Y', 'Rotation', 'Layer'])
    for r in pos:
        ref = r['Ref']
        x, y, rot = float(r['PosX']), float(r['PosY']), float(r['Rot'])
        if ref in ['H1', 'H2']:
            points = []
            for line in children(footprints[ref], 'fp_line'):
                if child(line, 'layer')[1] == 'F.Fab':
                    points.extend([tuple(map(float, child(line, k)[1:3])) for k in ['start', 'end']])
            dx = (min(p[0] for p in points) + max(p[0] for p in points)) / 2
            dy = (min(p[1] for p in points) + max(p[1] for p in points)) / 2
            assert abs(dx) < 1e-6 and abs(dy - 24.13) < 1e-6
            angle = math.radians(rot)
            x += dx * math.cos(angle) + dy * math.sin(angle)
            y += dx * math.sin(angle) - dy * math.cos(angle)
            centroid_changes[ref] = {'original_mm': [float(r['PosX']), float(r['PosY'])],
                                     'body_center_mm': [round(x, 6), round(y, 6)]}
        writer.writerow([ref, f'{x:.6f}', f'{y:.6f}', f'{rot % 360:.6f}', 'Top'])

exported_bom = list(csv.DictReader(bom_file.open()))
exported_cpl = list(csv.DictReader(cpl_file.open()))
assert {ref for r in exported_bom for ref in r['Designator'].split(',')} == refs
assert {r['Designator'] for r in exported_cpl} == refs
assert sum(int(r['Quantity']) for r in exported_bom) == 32
report = {
    'status': 'QUOTATION ONLY - part selection and placement preview not released',
    'cad_pcb_sha256': manifest['cad_pcb_sha256'],
    'bom_lines': len(exported_bom), 'component_count': 32, 'cpl_lines': len(exported_cpl),
    'all_top': True, 'coordinate_units': 'mm',
    'coordinate_origin': 'KiCad absolute origin, identical to Gerbers; Y inverted to Cartesian',
    'centroid_corrections': centroid_changes,
    'rotation_status': 'KiCad rotations normalized to 0..359; JLC model rotations require preview review',
    'unmatched_part_numbers': [r['Designator'] for r in exported_bom if not r['JLCPCB Part #']],
    'unselected_manufacturer_parts': [r['Designator'] for r in exported_bom if not r['Manufacturer Part Number']],
    'file_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [bom_file, cpl_file]},
    'format_sources': ['https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad',
                       'https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly'],
    'part_sources': ['https://jlcpcb.com/partdetail/' + jlc
                     for jlc in sorted({item[2] for item in exact.values() if item[2]})],
}
(DEST / 'export-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'PASS: {len(exported_bom)} BOM groups / 32 components, 32 CPL rows; CAD unchanged.')
print('Header centroids corrected; part/model matching remains pending in JLCPCB.')
