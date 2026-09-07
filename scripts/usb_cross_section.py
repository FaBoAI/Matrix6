"""Independent quasi-static 2-D odd-mode finite-difference calculation.

Half of a symmetric differential microstrip: x=0 is the virtual ground.
The conductor is at 1 V, the reference and coplanar grounds at 0 V.
Compute odd-mode C with dielectric and with vacuum; Zdiff=2/(c*sqrt(C*C0)).
This verifies the uniform section only, not connectors, IC packages or bends.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('OMP_NUM_THREADS','1')
from pathlib import Path
import argparse,json,math
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

EPS0=8.8541878128e-12
C0=299792458.0

def axis(anchors,step):
    return np.unique(np.concatenate([np.linspace(a,b,max(2,math.ceil((b-a)/step)+1))
        for a,b in zip(anchors,anchors[1:])]))

def solve(width=.28,gap=.2,height=.2104,copper=.035,er=4.4,mask_er=3.8,
          mask_trace=.0127,mask_base=.02032,coplanar=.5,step=.005,domain=3.,vacuum=False,coplanar_width=None,bottom_reference=True):
    left=gap/2;right=left+width;gnd=right+coplanar
    gx_end=gnd+coplanar_width if coplanar_width is not None else domain
    x=axis(sorted(set([0,left,right,gnd,gx_end,domain])),step)
    y=axis(([0] if bottom_reference else [-3.,0])+[height,height+mask_base,height+copper,height+copper+mask_trace,height+3.0],step)
    X,Y=np.meshgrid(x,y);ny,nx=X.shape
    cu_y=(Y>=height-1e-10)&(Y<=height+copper+1e-10)
    signal=cu_y&(X>=left-1e-10)&(X<=right+1e-10)
    fixed=signal|(cu_y&(X>=gnd-1e-10)&(X<=gx_end+1e-10))
    fixed[[0,-1],:]=True;fixed[:,[0,-1]]=True
    prescribed=np.zeros_like(X);prescribed[signal]=1
    unknown=~fixed;ids=np.full(X.shape,-1,int);ids[unknown]=np.arange(unknown.sum())
    # Permittivity at a face midpoint; account for conformal coating on Cu.
    def eps(xx,yy):
        if vacuum:return np.ones_like(xx+yy)
        dx=np.maximum(np.maximum(left-xx,xx-right),0)
        dy=np.maximum(np.maximum(height-yy,yy-height-copper),0)
        dist=np.hypot(dx,dy)
        dg=np.hypot(np.maximum(np.maximum(gnd-xx,xx-gx_end),0),dy)
        mask=(yy<height+mask_base)|(dist<mask_trace)|(dg<mask_trace)
        return np.where(yy<0,1.,np.where(yy<height-1e-10,er,np.where(mask,mask_er,1.0)))
    # Finite-volume face conductance, midpoint quadrature split at node.
    # Use each adjacent half-face separately so dielectric boundaries at nodes
    # are integrated on both sides rather than arbitrarily classified.
    yh=np.r_[y[0],(y[:-1]+y[1:])/2,y[-1]]
    xh=np.r_[x[0],(x[:-1]+x[1:])/2,x[-1]]
    ex=(x[:-1]+x[1:])[None,:]/2
    gx=(eps(ex,(yh[:-1]+y)[:,None]/2)*(y-yh[:-1])[:,None]
       +eps(ex,(y+yh[1:])[:,None]/2)*(yh[1:]-y)[:,None])/np.diff(x)[None,:]
    ey=(y[:-1]+y[1:])[:,None]/2
    gy=(eps((xh[:-1]+x)[None,:]/2,ey)*(x-xh[:-1])[None,:]
       +eps((x+xh[1:])[None,:]/2,ey)*(xh[1:]-x)[None,:])/np.diff(y)[:,None]
    rows=[];cols=[];data=[];rhs=np.zeros(unknown.sum());diag=np.zeros(unknown.sum())
    def connect(i,j,g,vi,vj):
        for a,b,va,vb in [(i,j,vi,vj),(j,i,vj,vi)]:
            active=a>=0;ai=a[active];bi=b[active];gg=g[active]
            np.add.at(diag,ai,gg)
            free=bi>=0;rows.append(ai[free]);cols.append(bi[free]);data.append(-gg[free])
            np.add.at(rhs,ai[~free],gg[~free]*vb[active][~free])
    connect(ids[:,:-1],ids[:,1:],gx,prescribed[:,:-1],prescribed[:,1:])
    connect(ids[:-1,:],ids[1:,:],gy,prescribed[:-1,:],prescribed[1:,:])
    rows.append(np.arange(len(diag)));cols.append(np.arange(len(diag)));data.append(diag)
    mat=coo_matrix((np.concatenate(data),(np.concatenate(rows),np.concatenate(cols))),shape=(len(diag),len(diag))).tocsr()
    v=prescribed.copy();v[unknown]=spsolve(mat,rhs)
    residual=float(np.linalg.norm(mat@v[unknown]-rhs)/np.linalg.norm(rhs))
    energy2=float(np.sum(gx*np.diff(v,axis=1)**2)+np.sum(gy*np.diff(v,axis=0)**2))
    # Twice the electrostatic energy / V^2 gives capacitance per unit length.
    capacitance=EPS0*energy2
    return capacitance,residual,(x,y,v),int(unknown.sum())

def run(**args):
    c,r,field,n=solve(**args);cv,rv,_,_=solve(**args,vacuum=True)
    return {'parameters_mm':args,'odd_capacitance_F_per_m':c,'vacuum_capacitance_F_per_m':cv,
            'differential_ohm':2/(C0*math.sqrt(c*cv)),'relative_residual':max(r,rv),'unknowns':n},field

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--width',type=float,default=.28)
    ap.add_argument('--step',type=float,default=.005);ap.add_argument('--er',type=float,default=4.4)
    ap.add_argument('--height',type=float,default=.2104);ap.add_argument('--output',default='/tmp/usb-section.json')
    ap.add_argument('--plot');a=ap.parse_args()
    result,field=run(width=a.width,step=a.step,er=a.er,height=a.height)
    Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
    if a.plot:
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        x,y,v=field;fig,ax=plt.subplots(figsize=(9,3.5),layout='constrained')
        xx=np.r_[-x[:0:-1],x];vv=np.c_[-v[:,:0:-1],v]
        im=ax.contourf(xx,y,vv,31,cmap='RdBu_r',vmin=-1,vmax=1)
        ax.set(xlim=(-1.2,1.2),ylim=(0,.6),xlabel='Across pair (mm)',ylabel='Above L2 GND (mm)',
               title=f'USB uniform section — {result["differential_ohm"]:.1f} Ω differential (2-D estimate)')
        fig.colorbar(im,ax=ax,label='Odd-mode potential (V)');fig.savefig(a.plot,dpi=180)
