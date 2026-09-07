"""Two-layer DC resistor mesh of saved pours and actual GND through vias.
GND pads, traces and pours are combined with drill holes removed; via barrels use
20 um plating and one mesh node per end. Not a thermal or AC field solution.
"""
from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import Polygon,Point,LineString
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
from shapely import contains_xy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parent.parent;R=ROOT/'docs/validation'
geo=json.loads((R/'ground-geometry.json').read_text());layers=['F.Cu','B.Cu']
holes=[]
for q in geo['ground_holes']:
 w,h=q['size'];r=min(w,h)/2
 shape=(LineString([(-(w-h)/2,0),((w-h)/2,0)]) if w>h else LineString([(0,-(h-w)/2),(0,(h-w)/2)])).buffer(r,quad_segs=12) if abs(w-h)>1e-6 else Point(0,0).buffer(r,quad_segs=12)
 holes.append(translate(rotate(shape,-q['angle'],origin=(0,0)),*q['at']))
holes=unary_union(holes)
shapes=[unary_union([Polygon(p['shell'],p['holes']) for p in geo['layers'][la]+geo['ground_copper'][la]]).difference(holes) for la in layers]
rho=1.724e-5*(1+.00393*40);thickness=.035

def run(step,source,sink,current=.5):
 x=np.arange(97.46,138.10+1e-6,step);y=np.arange(100,161+1e-6,step);X,Y=np.meshgrid(x,y)
 ids=[];coords=[];coppers=[];N=0;aa=[];bb=[];gg=[]
 for shape in shapes:
  copper=contains_xy(shape,X,Y);i=np.full(X.shape,-1,int);i[copper]=np.arange(copper.sum())+N
  ids.append(i);coords.append(np.c_[X[copper],Y[copper]]);coppers.append(copper);N+=int(copper.sum())
  for a,b,mx,my in [(i[:,:-1],i[:,1:],(X[:,:-1]+X[:,1:])/2,Y[:,:-1]),(i[:-1,:],i[1:,:],X[:-1,:],(Y[:-1,:]+Y[1:,:])/2)]:
   good=(a>=0)&(b>=0)&contains_xy(shape,mx,my);aa.extend(a[good]);bb.extend(b[good]);gg.extend(np.full(good.sum(),thickness/rho))
 offsets=[0,len(coords[0])];trees=[cKDTree(c) for c in coords];connected_vias=0;omitted=[]
 for via in geo['stitches']:
  matches=[tree.query(via['at']) for tree in trees]
  if max(d for d,_ in matches)>via['drill_mm']/2+1.5*step:omitted.append(via['at']);continue
  d=via['drill_mm'];area=math.pi*((d/2+.02)**2-(d/2)**2);rv=rho*1.565/area
  aa.append(matches[0][1]);bb.append(matches[1][1]+offsets[1]);gg.append(1/rv);connected_vias+=1
 aa=np.array(aa);bb=np.array(bb);gg=np.array(gg);rr=np.r_[aa,bb,aa,bb];cc=np.r_[aa,bb,bb,aa];vv=np.r_[gg,gg,-gg,-gg]
 mat=coo_matrix((vv,(rr,cc)),shape=(N,N)).tocsr();allcoords=np.vstack(coords)
 # Sources and sinks enter on front copper; current may use either layer.
 ports=[]
 for at in [source,sink]:
  mask=np.zeros(N,bool);mask[:len(coords[0])]=np.sum((coords[0]-np.array(at))**2,axis=1)<=.3**2
  assert mask.any(),('port_missing',at);ports.append(mask)
 count,labels=connected_components(mat,directed=False);source_label=labels[np.flatnonzero(ports[0])[0]]
 assert all(labels[i]==source_label for port in ports for i in np.flatnonzero(port)), 'Ground return disconnected in mesh'
 active=(labels==source_label)&~ports[0]&~ports[1];v=np.zeros(N);v[ports[0]]=1
 v[active]=spsolve(mat[active,:][:,active],-(mat@v)[active]);onevolt=float((mat@v)[ports[0]].sum());resistance=1/onevolt;v*=current/onevolt
 fields=[]
 for idx,cu in enumerate(coppers):
  img=np.full(X.shape,np.nan);img[cu]=v[offsets[idx]:offsets[idx]+len(coords[idx])]*1000;fields.append(img)
 return {'mesh_step_mm':step,'source_front_mm':source,'sink_front_mm':sink,'copper_C':60,'copper_mm':thickness,'current_A':current,'ground_resistance_ohm':resistance,'ground_drop_mV':current*resistance*1000,'connected_stitches':connected_vias,'omitted_stitches':omitted,'active_nodes':int(active.sum())},(x,y,fields)
results=[]
for step in [.25,.125,.0625]:
 result,field=run(step,[118.8,109.7],[121.2,137.6]);results.append(result)
input_result,_=run(.125,[121.2,137.6],[115.1,149.35],.8)
(R/'ground-plane-dc.json').write_text(json.dumps({'module_return':results,'input_return':input_result,'scope':'Front and rear filled pours, through-hole GND stitches; 20 um barrel plating; 60 C copper. Approximate DC mesh. GND pads/traces are included and drill holes subtracted; solder/contact resistance is not included. Not an EMC or thermal certification.'},indent=2)+'\n')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
x,y,fields=field;fig,axs=plt.subplots(1,2,figsize=(10,8),layout='constrained')
for ax,la,img in zip(axs,layers,fields):
 im=ax.pcolormesh(x,y,img,cmap='viridis',shading='nearest');ax.invert_yaxis();ax.set_aspect('equal');ax.set(xlabel='PCB X (mm)',ylabel='PCB Y (mm)',title=la+' GND / 500 mA');fig.colorbar(im,ax=ax,label='mV')
fig.savefig(R/'ground-plane-dc.png',dpi=170)
print(json.dumps({'module_return':results,'input_return':input_result},indent=2),flush=True)
assert results[-1]['ground_drop_mV']<10 and input_result['ground_drop_mV']<10
