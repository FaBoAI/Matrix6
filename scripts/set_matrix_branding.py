"""Set the two-line front silkscreen without moving copper or components."""
from pathlib import Path
import pcbnew as p

def apply_branding(board):
    title=next(t for t in board.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetText()=='Matrix Six')
    credit=next(t for t in board.GetDrawings() if isinstance(t,p.PCB_TEXT) and t.GetText().lower()=='designed by gpt-6 astra')
    # Centre both lines on the 40.64 mm outline. R8 is moved beside U1
    # by move_r8_for_branding.py to keep the two text rows together.
    centre_x=(97.46+138.10)/2
    for text,label,y,size,stroke in [(title,'Matrix Six',122.2,2.0,.25),(credit,'Designed by GPT-6 Astra',125.0,.8,.12)]:
        text.SetText(label)
        text.SetLayer(p.F_SilkS)
        text.SetMirrored(False)
        text.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        text.SetHorizJustify(p.GR_TEXT_H_ALIGN_CENTER)
        text.SetVertJustify(p.GR_TEXT_V_ALIGN_CENTER)
        text.SetPosition(p.VECTOR2I(p.FromMM(centre_x),p.FromMM(y)))
        text.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)))
        text.SetTextThickness(p.FromMM(stroke))

if __name__=='__main__':
    import wx
    app=wx.App(False)
    file=Path(__file__).resolve().parent.parent/'hardware/Matrix6/Matrix6.kicad_pcb'
    board=p.LoadBoard(str(file))
    apply_branding(board)
    p.SaveBoard(str(file),board)
    print('Front branding: Matrix Six 2.0 mm, credit 0.8 mm beneath it.')
