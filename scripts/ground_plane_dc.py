"""DC resistor mesh of actual filled L2 geometry, including antipads.
Plane-only estimate. Parallel top/bottom copper is deliberately omitted.
No PCB routing or mutation is performed.
"""
from pathlib import Path
import json,math
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import contains_xy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parent.parent;R=ROOT/'docs/validation'
geo=json.loads((R/'ground-geometry.json').read_text())
if 'layers' in geo:
 import subprocess,sys
 subprocess.run([sys.executable,str(ROOT/'scripts/ground_two_layer_dc.py')],check=True)
 raise SystemExit(0)
shape=unary_union([Polygon(p['shell'],p['holes']) for p in geo['polygons']])
rho=1.724e-5*(1+.00393*40);thickness=.0152

def run(step,source,sink):
 x=np.arange(97.46,138.10+1e-6,step);y=np.arange(100,161+1e-6,step);X,Y=np.meshgrid(x,y)
 copper=contains_xy(shape,X,Y);ids=np.full(X.shape,-1,int);ids[copper]=np.arange(copper.sum());N=int(copper.sum())
 aa=[];bb=[]
 for a,b,mx,my in [(ids[:,:-1],ids[:,1:],(X[:,:-1]+X[:,1:])/2,Y[:,:-1]),(ids[:-1,:],ids[1:,:],X[:-1,:],(Y[:-1,:]+Y[1:,:])/2)]:
  good=(a>=0)&(b>=0)&contains_xy(shape,mx,my);aa.extend(a[good]);bb.extend(b[good])
 aa=np.array(aa);bb=np.array(bb);rr=np.r_[aa,bb,aa,bb];cc=np.r_[aa,bb,bb,aa];vv=np.r_[np.ones(2*len(aa)),-np.ones(2*len(aa))]*(thickness/rho)
 mat=coo_matrix((vv,(rr,cc)),shape=(N,N)).tocsr()
 coords=np.c_[X[copper],Y[copper]]
 ports=[np.sum((coords-np.array(p))**2,axis=1) <= .3**2 for p in [source,sink]]
 assert all(np.any(port) for port in ports)
 count,labels=connected_components(mat,directed=False)
 source_label=labels[np.flatnonzero(ports[0])[0]]
 assert all(labels[i]==source_label for port in ports for i in np.flatnonzero(port))
 active=(labels==source_label)&~ports[0]&~ports[1]
 v=np.zeros(N);v[ports[0]]=1
 v[active]=spsolve(mat[active,:][:,active],-(mat@v)[active])
 current=float((mat@v)[ports[0]].sum());resistance=1/current;v*=.5/current
 out={'mesh_step_mm':step,'source_via_mm':source,'sink_via_mm':sink,'copper_C':60,'L2_copper_mm':thickness,
 'current_A':.5,'plane_resistance_ohm':resistance,'plane_drop_mV':.5*resistance*1000,'contact_diameter_mm':.6,'nodes':int(active.sum())}
 img=np.full(X.shape,np.nan);img[copper]=v*1000
 return out,(x,y,img)
results=[]
for step in [.25,.125]:
 result,field=run(step,[118.8,109.7],[121.2,137.6]);results.append(result)
input_result,_=run(.125,[121.2,137.6],[115.1,149.35])
(R/'ground-plane-dc.json').write_text(json.dumps({'module_return':results,'input_return':input_result,
 'scope':'L2 only between named GND vias. 0.5 A through a single source/sink; copper 60C. Does not include via barrels, solder/contact resistance or top-layer spreading.'},indent=2))
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
x,y,img=field;fig,ax=plt.subplots(figsize=(5,8),layout='constrained');im=ax.pcolormesh(x,y,img,cmap='viridis',shading='nearest');ax.invert_yaxis();ax.set_aspect('equal');ax.set(xlabel='PCB X (mm)',ylabel='PCB Y (mm)',title='L2 GND: 500 mA return, copper 60°C\nDC mesh estimate between two GND vias');ax.plot([118.8,121.2],[109.7,137.6],'wo',ms=5);fig.colorbar(im,ax=ax,label='Ground potential (mV)');fig.savefig(R/'ground-plane-dc.png',dpi=180)
print(json.dumps({'module_return':results,'input_return':input_result},indent=2))
