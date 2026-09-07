"""Reproducible nominal/sensitivity screening, not a fabricated impedance guarantee."""
from pathlib import Path
import json
from usb_cross_section import run
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/analysis'
base=dict(width=.38,gap=.18,height=1.53,er=4.5,coplanar=.20,step=.01,domain=5.,coplanar_width=1.,bottom_reference=True)
cases=[('nominal',{}),('finer_mesh',{'step':.0075}),('minimum_checked_ground_width',{'coplanar_width':.5}),('no_rear_reference',{'bottom_reference':False}),('higher_impedance_sensitivity',{'width':.36,'gap':.20,'coplanar':.22,'er':4.3}),('lower_impedance_sensitivity',{'width':.40,'gap':.16,'coplanar':.18,'er':4.7})]
results=[];plotfield=None
for label,overrides in cases:
 r,field=run(**{**base,**overrides});r['case']=label;results.append(r)
 if label=='finer_mesh':plotfield=field
 print(label,round(r['differential_ohm'],3),flush=True)
report={'method':'2-D odd-mode finite-volume electrostatics: Zdiff=2/(c*sqrt(C*Cvacuum))','target_ohm':[81,99],
 'nominal_uniform_section_only':True,'fabrication_impedance_guarantee':False,
 'scope':'Symmetric, uniform cross-sections only; no connector/package/bend/meander or frequency-dependent loss model. Finite coplanar ground and loss of the distant rear reference are separate screening cases. Sensitivity corners are assumptions, not JLCPCB tolerances or acceptance limits.',
 'requirements':'Retain the top coplanar return bands and stitches. Confirm actual FR4/copper/etch and test both USB-C orientations, SI/EMC and supply transients on assembled prototypes.',
 'cases':results,'sources':['https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s3/pcb-layout-design.html','https://jlcpcb.com/capabilities/pcb-capabilities/']}
(OUT/'two-layer-usb.json').write_text(json.dumps(report,indent=2)+'\n')
import numpy as np,matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
x,y,v=plotfield;xx=np.r_[-x[:0:-1],x];vv=np.c_[-v[:,:0:-1],v]
fig,ax=plt.subplots(figsize=(9,5),layout='constrained');im=ax.contourf(xx,y,vv,31,cmap='RdBu_r',vmin=-1,vmax=1)
ax.set(xlim=(-1.7,1.7),ylim=(0,2.3),xlabel='Across pair (mm)',ylabel='Above rear copper (mm)',title=f'Matrix Six 2-layer USB: {results[1]["differential_ohm"]:.1f} Ω nominal\n0.38 mm width / 0.18 mm pair gap / 0.20 mm coplanar clearance')
ax.axhline(1.53,c='gray',lw=.5);ax.axhline(0,c='black',lw=2);fig.colorbar(im,ax=ax,label='Odd-mode potential (V)');fig.savefig(OUT/'two-layer-usb-section.png',dpi=170)
assert 81<results[1]['differential_ohm']<99
assert abs(results[1]['differential_ohm']-results[0]['differential_ohm'])<1
