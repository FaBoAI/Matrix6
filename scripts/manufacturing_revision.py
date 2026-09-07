"""Derive versioned output paths from the saved PCB, not a hardcoded release."""
from pathlib import Path
from sexpr import parse, child
ROOT = Path(__file__).resolve().parent.parent
CAD = ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'
REV = child(child(parse(CAD.read_text()), 'title_block'), 'rev')[1]
assert REV in ('0.6', '0.7'), REV
OUT = ROOT/f'manufacturing/v{REV}'
RADIUS = 2.0 if REV == '0.7' else 0.0
