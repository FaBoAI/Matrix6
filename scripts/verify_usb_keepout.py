"""Verify the real J1 keepout and negative controls in a temporary PCB copy."""
from pathlib import Path
import json,shutil,tempfile,subprocess,hashlib,os
import pcbnew as p,wx
app=wx.App(False)
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'hardware/Matrix6';NAME='Matrix6'
MAC=Path('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
CLI=os.environ.get('KICAD_CLI',str(MAC) if MAC.exists() else 'kicad-cli')
boardpath=OUT/(NAME+'.kicad_pcb');b=p.LoadBoard(str(boardpath));j=next(f for f in b.GetFootprints() if f.GetReference()=='J1')
zones=list(j.Zones());assert len(zones)==1
z=zones[0];assert z.GetIsRuleArea() and z.GetDoNotAllowTracks() and z.GetDoNotAllowVias() and z.GetDoNotAllowZoneFills()
assert z.GetLayer()==p.F_Cu and not z.GetDoNotAllowPads()
mm=p.FromMM
def pt(x,y):return p.VECTOR2I(mm(x),mm(y))
def inside(x,y):return 113.31<=x<=122.25 and 154.325<=y<=161.675
bad=[]
for t in b.GetTracks():
 if t.GetLayer()!=p.F_Cu and not isinstance(t,p.PCB_VIA):continue
 a,c=t.GetStart(),t.GetEnd();w=p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/2
 # Bounding box is conservative and sufficient for this rectangular region.
 xmin=min(p.ToMM(a.x),p.ToMM(c.x))-w;xmax=max(p.ToMM(a.x),p.ToMM(c.x))+w
 ymin=min(p.ToMM(a.y),p.ToMM(c.y))-w;ymax=max(p.ToMM(a.y),p.ToMM(c.y))+w
 if xmin<122.25 and xmax>113.31 and ymin<161.675 and ymax>154.325:bad.append(t.GetNetname())
assert not bad,bad
top=next(z for z in b.Zones() if z.GetLayer()==p.F_Cu and not z.GetIsRuleArea());poly=top.GetFilledPolysList(p.F_Cu)
filled=[]
for i in range(89):
 for k in range(73):
  x,y=113.35+.1*i,154.35+.1*k
  if poly.Contains(pt(x,y)):filled.append([x,y])
assert not filled,filled[:5]
with tempfile.TemporaryDirectory(prefix='usb-keepout-probe-') as tmp:
 d=Path(tmp)
 for ext in ['.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru']:shutil.copy2(OUT/(NAME+ext),d/(NAME+ext))
 shutil.copy2(OUT/'fp-lib-table',d/'fp-lib-table');shutil.copytree(OUT/'DevBoard.pretty',d/'DevBoard.pretty')
 net=next(n for name,n in b.GetNetInfo().NetsByName().items() if str(name)=='/GND')
 t=p.PCB_TRACK(b);t.SetStart(pt(117,157));t.SetEnd(pt(118,157));t.SetWidth(mm(.25));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t)
 v=p.PCB_VIA(b);v.SetPosition(pt(119,157.3));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(net);b.Add(v)
 p.SaveBoard(str(d/(NAME+'.kicad_pcb')),b)
 report=d/'probe.json'
 subprocess.run([CLI,'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--format','json','-o',str(report),str(d/(NAME+'.kicad_pcb'))],check=True)
 result=json.loads(report.read_text())
 forbidden=[v for v in result['violations'] if v['type']=='items_not_allowed']
 assert len(forbidden)>=2,result['violations']
test={'pcb_sha256':hashlib.sha256(boardpath.read_bytes()).hexdigest(),'footprint':str(j.GetFPID().GetLibItemName()),
      'body_F_Cu_tracks_or_vias':len(bad),'body_top_zone_filled_sample_points':len(filled),
      'body_top_zone_sample_count':89*73,'own_connector_pads_allowed':True,
      'negative_control':'Added an F.Cu track and through via inside J1 in a temporary copy only.',
      'negative_control_keepout_violations':len(forbidden),'status':'PASS'}
(ROOT/'docs/validation/usb-keepout-validation.json').write_text(json.dumps(test,indent=2)+'\n')
print(json.dumps(test,indent=2))
