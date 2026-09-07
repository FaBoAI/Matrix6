"""Move the IO46 pull-down beside the module to clear central silkscreen.

All routing is explicitly specified. No autorouter is used.
"""
from pathlib import Path
import pcbnew as p

def xy(v): return tuple(round(p.ToMM(n),6) for n in (v.x,v.y))
def point(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))

def move_r8(board):
    part=next(f for f in board.GetFootprints() if f.GetReference()=='R8')
    if xy(part.GetPosition())==(129.3,120.3): return
    assert xy(part.GetPosition())==(112.5,123.6),'Unexpected R8 position'
    old_io46={frozenset(pair) for pair in [
        ((111.675,123.6),(111.675,122.6)),
        ((111.675,122.6),(112.065,122.21)),
        ((112.065,122.21),(112.065,121.8))]}
    removed=[]
    for track in list(board.GetTracks()):
        a,c=xy(track.GetStart()),xy(track.GetEnd())
        is_via=isinstance(track,p.PCB_VIA)
        old_ground=track.GetNetname()=='/GND' and (
            (is_via and a==(113.325,124.4)) or
            (not is_via and frozenset((a,c))==frozenset(((113.325,123.6),(113.325,124.4)))))
        old_branch=not is_via and track.GetNetname()=='/IO46' and frozenset((a,c)) in old_io46
        if old_ground or old_branch:
            removed.append(track);board.Remove(track)
    assert len(removed)==5
    part.SetPosition(point(129.3,120.3));part.SetOrientationDegrees(90)
    signal=next(q for q in part.Pads() if q.GetNumber()=='1')
    assert xy(signal.GetPosition())==(129.3,121.125)
    track=p.PCB_TRACK(board);track.SetStart(point(129.3,122.1));track.SetEnd(signal.GetPosition())
    track.SetLayer(p.F_Cu);track.SetWidth(p.FromMM(.25));track.SetNet(signal.GetNet());board.Add(track)
    # Ground pad 2 connects directly to the refilled F.Cu GND pour.

if __name__=='__main__':
    import wx
    app=wx.App(False)
    file=Path(__file__).resolve().parent.parent/'hardware/Matrix6/Matrix6.kicad_pcb'
    board=p.LoadBoard(str(file));move_r8(board);p.SaveBoard(str(file),board)
    print('R8 moved to front (129.3,120.3), 90 degrees; refill and run DRC.')
