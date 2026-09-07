"""Draw the saved CAD pads and package outlines for JLC's placement review."""
from pathlib import Path
from html import escape
import wx, pcbnew as p
ROOT=Path(__file__).resolve().parent.parent
app=wx.App(False); b=p.LoadBoard(str(ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'))
S=15; X0=97.46; Y0=90; W=40.64
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1520" viewBox="0 0 1600 1520">', '<rect width="1600" height="1520" fill="white"/>']
def text(x,y,t,size=19,color='#18242d'):
    svg.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}">{escape(t)}</text>')
text(65,50,'Matrix Six v0.6 — CAD assembly reference',32)
text(65,82,'Use actual pad locations and polarity. JLC preview model origins may differ. CAM/placement approval required.',19)
for bottom,ox,label in [(False,85,'TOP — viewed from component side'),(True,900,'BOTTOM — viewed from component side')]:
    text(ox,122,label,22)
    def xy(x,y):return (ox+((X0+W-x) if bottom else (x-X0))*S,145+(y-Y0)*S)
    x,y=xy(X0+W if bottom else X0,100)
    svg.append(f'<rect x="{x}" y="{y}" width="{W*S}" height="{61*S}" fill="#f1e9f7" stroke="#344653" stroke-width="2"/>')
    for f in b.GetFootprints():
        side=f.GetLayer()==p.B_Cu
        if side!=bottom:continue
        fab=p.B_Fab if bottom else p.F_Fab
        for g in f.GraphicalItems():
            if not isinstance(g,p.PCB_SHAPE) or g.GetLayer()!=fab:continue
            if g.GetShape()==p.SHAPE_T_SEGMENT:
                a,c=g.GetStart(),g.GetEnd(); xx,yy=xy(p.ToMM(a.x),p.ToMM(a.y)); xx2,yy2=xy(p.ToMM(c.x),p.ToMM(c.y))
                svg.append(f'<path d="M{xx},{yy} L{xx2},{yy2}" stroke="#526675" fill="none" stroke-width="1.5"/>')
            elif g.GetShape()==p.SHAPE_T_RECT:
                a,c=g.GetStart(),g.GetEnd();xx,yy=xy(p.ToMM(a.x),p.ToMM(a.y));xx2,yy2=xy(p.ToMM(c.x),p.ToMM(c.y))
                svg.append(f'<rect x="{min(xx,xx2)}" y="{min(yy,yy2)}" width="{abs(xx-xx2)}" height="{abs(yy-yy2)}" stroke="#526675" fill="none" stroke-width="1.5"/>')
        for pad in f.Pads():
            pos=pad.GetPosition();xx,yy=xy(p.ToMM(pos.x),p.ToMM(pos.y));sz=pad.GetSize();w,h=p.ToMM(sz.x)*S,p.ToMM(sz.y)*S
            angle=pad.GetOrientationDegrees()*(1 if bottom else -1)
            svg.append(f'<rect x="{xx-w/2}" y="{yy-h/2}" width="{w}" height="{h}" transform="rotate({angle} {xx} {yy})" fill="#d6a446" stroke="#674600" stroke-width="0.5"/>')
            drill=pad.GetDrillSize()
            if drill.x:
                svg.append(f'<circle cx="{xx}" cy="{yy}" r="{p.ToMM(drill.x)*S/2}" fill="white"/>')
            if pad.GetNumber()=='1' or (f.GetReference()=='J1' and pad.GetNumber()=='A1'):
                svg.append(f'<circle cx="{xx}" cy="{yy}" r="{max(w,h)/2+4}" fill="none" stroke="#d03535" stroke-width="2"/>')
        pos=f.GetPosition();xx,yy=xy(p.ToMM(pos.x),p.ToMM(pos.y));text(xx+5,yy-9,f.GetReference(),13)
    if bottom:
        x,y=xy(125.7,100.5);svg.append(f'<rect x="{x}" y="{y}" width="{15.8*S}" height="{22.5*S}" fill="#d5f4dc" stroke="#23803d" stroke-width="2" stroke-dasharray="7,5"/>')
        text(x+10,y+35,'Keep SD withdrawal path clear',16,'#185b2c')
text(65,1270,'Red circles: pad 1 (USB: A1). Brown pads and grey outlines come directly from the saved KiCad board.',20)
notes=[
'U1 body: X108.78..126.78, Y93.75..119.25 mm. Antenna overhang: 6.25 mm above board edge Y100. Keep rails clear.',
'U1 pad 1: (109.03,101.24); U2/U3/U4/Q1: follow circled pad 1. Do not infer position from a shifted 3D model.',
'J1 USB mouth faces lower board edge. J2 SD mouth faces upper antenna edge; contact row Y139.725 mm.',
'J3 pin 1 BAT+: (108.5,153.5), pin 2 GND: (106.5,153.5). Battery socket faces lower board edge.',
'D1/D2/D3 pad 1 = cathode. H1/H2 pin 1 at lower ends; 20 pins on 2.54 mm pitch, socket spacing 33.02 mm.',
'Coordinates above are absolute KiCad millimetres, X right / Y down. CPL uses Y up. Body dimensions exclude line width.'
]
for i,t in enumerate(notes):text(65,1308+i*30,t,18)
svg.append('</svg>')
out=ROOT/'manufacturing/v0.6/review/Matrix6-assembly-reference.svg';out.write_text('\n'.join(svg));print(out)
