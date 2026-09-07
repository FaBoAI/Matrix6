"""Read the actual saved PCB; measure USB paths, reference plane and DC paths.
Graph searches here only MEASURE existing copper; they never create routes.
Run with KiCad's Python 3.9 runtime.
"""
from pathlib import Path
import collections,heapq,json,math
import pcbnew as p
import wx

app=wx.App(False)
ROOT=Path(__file__).resolve().parent.parent
BOARD=ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'
b=p.LoadBoard(str(BOARD));fps={f.GetReference():f for f in b.GetFootprints()}
def xy(v):return tuple(round(p.ToMM(q),6) for q in (v.x,v.y))
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def getpad(ref,num):return next(q for q in fps[ref].Pads() if q.GetNumber()==str(num))
def pad(ref,num):return xy(getpad(ref,num).GetPosition())
def distance(a,c):return math.hypot(a[0]-c[0],a[1]-c[1])
def along(q,a,c):
    dx,dy=c[0]-a[0],c[1]-a[1];l2=dx*dx+dy*dy
    if l2<1e-15:return 0 if distance(q,a)<1e-5 else None
    u=((q[0]-a[0])*dx+(q[1]-a[1])*dy)/l2
    if -.00001<=u<=1.00001 and distance(q,(a[0]+u*dx,a[1]+u*dy))<.00001:return max(0,min(1,u))
    return None
LAYERS=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
# Conservative specified copper thicknesses; 20 um minimum via barrel plating.
THICKNESS={p.F_Cu:.035,p.B_Cu:.035,p.In1_Cu:.0152,p.In2_Cu:.0152}
RHO20=1.724e-5 # ohm mm
RHO=RHO20*(1+.00393*(60-20)) # resistance evaluated at copper 60 C
Z={p.F_Cu:0,p.In1_Cu:.2279,p.In2_Cu:1.3081,p.B_Cu:1.5687}

def graph(net,kind='length'):
    netnames={net} if isinstance(net,str) else set(net)
    tracks=[t for t in b.GetTracks() if t.GetNetname() in netnames and not isinstance(t,p.PCB_VIA)]
    vias=[t for t in b.GetTracks() if t.GetNetname() in netnames and isinstance(t,p.PCB_VIA)]
    positions=collections.defaultdict(set)
    for t in tracks:
        positions[t.GetLayer()].update([xy(t.GetStart()),xy(t.GetEnd())])
    for v in vias:
        for la in LAYERS:positions[la].add(xy(v.GetPosition()))
    for f in fps.values():
        for q in f.Pads():
            if q.GetNetname() in netnames:
                for la in LAYERS:
                    if q.IsOnLayer(la):positions[la].add(xy(q.GetPosition()))
    g=collections.defaultdict(list)
    def edge(a,c,w,desc):g[a].append((c,w,desc));g[c].append((a,w,desc))
    for t in tracks:
        la=t.GetLayer();a,c=xy(t.GetStart()),xy(t.GetEnd());width=p.ToMM(t.GetWidth())
        cuts=sorted((u,q) for q in positions[la] if (u:=along(q,a,c)) is not None)
        for (_,a),(_,c) in zip(cuts,cuts[1:]):
            length=distance(a,c);resistance=RHO*length/(width*THICKNESS[la])
            edge((la,*a),(la,*c),length if kind=='length' else resistance,
                 {'layer':b.GetLayerName(la),'length_mm':length,'width_mm':width,'resistance_ohm_60C':resistance})
    for v in vias:
        pos=xy(v.GetPosition());drill=p.ToMM(v.GetDrillValue());area=math.pi*((drill/2+.020)**2-(drill/2)**2)
        for a,c in zip(LAYERS,LAYERS[1:]):
            length=Z[c]-Z[a];r=RHO*length/area
            edge((a,*pos),(c,*pos),length if kind=='length' else r,
                 {'via_at':pos,'length_mm':length,'resistance_ohm_60C':r,'drill_mm':drill})
    # Through-hole header pins are plated; connect their pad centers across layers.
    for f in fps.values():
        for q in f.Pads():
            if q.GetNetname() not in netnames or not q.IsOnLayer(p.B_Cu):continue
            pos=xy(q.GetPosition());drill=max(.1,p.ToMM(q.GetDrillSize().x));area=math.pi*((drill/2+.020)**2-(drill/2)**2)
            for a,c in zip(LAYERS,LAYERS[1:]):
                length=Z[c]-Z[a];r=RHO*length/area
                edge((a,*pos),(c,*pos),length if kind=='length' else r,
                     {'pth':f.GetReference()+'-'+q.GetNumber(),'resistance_ohm_60C':r})
    # Tracks may end INSIDE a pad, before its center, to avoid J1's body keepout.
    # Include pad-center geometry in length reporting; copper exists throughout
    # the pad. This is a length proxy, not an electromagnetic pad-delay model.
    for f in fps.values():
        for q in f.Pads():
            if q.GetNetname() not in netnames:continue
            center=xy(q.GetPosition())
            for la in LAYERS:
                if not q.IsOnLayer(la):continue
                for pos in positions[la]:
                    if pos==center or not q.HitTest(pt(*pos)):continue
                    length=distance(pos,center)
                    resistance=RHO*length/(min(p.ToMM(q.GetSize().x),p.ToMM(q.GetSize().y))*THICKNESS[la])
                    edge((la,*pos),(la,*center),length if kind=='length' else resistance,
                         {'pad_center_extension':f.GetReference()+'-'+q.GetNumber(),'length_mm':length,'resistance_ohm_60C':resistance})
    if {'/USB_P','/USB_A_P'} <= netnames:
        a,c=pad('R11',1),pad('R11',2);length=distance(a,c)
        assert kind=='length'
        edge((p.F_Cu,*a),(p.F_Cu,*c),length,{'component':'R11 0R','pad_center_span_mm':length,
             'note':'Nominal geometric span; package electrical delay is not measured.'})
    return g

def measure(net,source,dest,kind='length'):
    g=graph(net,kind);start=(p.F_Cu,*pad(*source));target=(p.F_Cu,*pad(*dest))
    todo=[(0,start)];visited={};prev={}
    while todo:
        val,u=heapq.heappop(todo)
        if u in visited:continue
        visited[u]=val
        if u==target:break
        for v,w,d in g[u]:
            if v not in visited:
                if val+w < prev.get(v,(float('inf'),None,None))[0]:prev[v]=(val+w,u,d)
                heapq.heappush(todo,(val+w,v))
    if target not in visited:raise RuntimeError(f'No route {net} {source} -> {dest}')
    u=target;segments=[]
    while u!=start:
        _,u,d=prev[u];segments.append(d)
    return visited[target],segments

usb={}
for contact,minus,plus in [('A','A7','A6'),('B','B7','B6')]:
    n,_=measure('/USB_N',('R3','1'),('J1',minus))
    q,segments=measure(('/USB_P','/USB_A_P') if contact=='A' and 'R11' in fps else '/USB_P',('R4','1'),('J1',plus))
    usb[contact]={'minus_centerline_mm':n,'plus_centerline_mm':q,'absolute_skew_mm':abs(n-q)}
    if contact=='A' and 'R11' in fps:
        usb[contact]['R11_geometric_span_mm']=distance(pad('R11',1),pad('R11',2))
        usb[contact]['plus_copper_and_pad_mm']=q-usb[contact]['R11_geometric_span_mm']
        usb[contact]['package_delay_unverified']=True
usb['module_N_mm']=measure('/MCU_USB_N',('U1','13'),('R3','2'))[0]
usb['module_P_mm']=measure('/MCU_USB_P',('U1','14'),('R4','2'))[0]
usb['vias']=sum(isinstance(t,p.PCB_VIA) for t in b.GetTracks() if 'USB' in t.GetNetname())
usb['all_on_top']=all(t.GetLayer()==p.F_Cu for t in b.GetTracks() if 'USB' in t.GetNetname())

ground=next(z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==p.In1_Cu)
polys=ground.GetFilledPolysList(p.In1_Cu)
def area(chain):
    vv=[xy(chain.CPoint(i)) for i in range(chain.PointCount())]
    return abs(sum(a[0]*c[1]-c[0]*a[1] for a,c in zip(vv,vv[1:]+vv[:1])))/2
plane_area=sum(area(polys.COutline(i))-sum(area(polys.CHole(i,j)) for j in range(polys.HoleCount(i))) for i in range(polys.OutlineCount()))
missing=[];samples=0
for t in b.GetTracks():
    if 'USB' not in t.GetNetname() or isinstance(t,p.PCB_VIA):continue
    a,c=xy(t.GetStart()),xy(t.GetEnd());length=distance(a,c)
    if not length:continue
    nx,ny=-(c[1]-a[1])/length,(c[0]-a[0])/length
    for i in range(math.ceil(length/.025)+1):
        u=i/max(1,math.ceil(length/.025));cx,cy=a[0]+u*(c[0]-a[0]),a[1]+u*(c[1]-a[1])
        for off in [0,-p.ToMM(t.GetWidth())/2-.05,p.ToMM(t.GetWidth())/2+.05]:
            x,y=cx+nx*off,cy+ny*off;samples+=1
            if not polys.Contains(pt(x,y)):missing.append([t.GetNetname(),round(x,5),round(y,5)])
ground_info={'signal_track_count_L2':sum(t.GetLayer()==p.In1_Cu and not isinstance(t,p.PCB_VIA) for t in b.GetTracks()),
             'connected_copper_regions':polys.OutlineCount(),'area_mm2':plane_area,
             'USB_reference_samples':samples,'missing_ground_samples':missing}

power={}
for label,net,s,d,load in [
 ('USB_to_fuse','/VBUS',('J1','A4'),('F1','1'),.65),
 ('fuse_to_diode','/VBUS_FUSED',('F1','2'),('D1','2'),.55),
 ('diode_to_buck','/+5V',('D1','1'),('U2','3'),.55),
 ('buck_to_module','/+3V3',('L1','2'),('U1','2'),.5),
 ('buck_to_left_header','/+3V3',('L1','2'),('H1','1'),.5),
 ('fuse_to_shield_VBUS','/VBUS_FUSED',('F1','2'),('H2','1'),.1)]:
    resistance,segments=measure(net,s,d,'resistance');est=[]
    for seg in segments:
        if 'width_mm' not in seg:continue
        thick=.035 if seg['layer'] in ['F.Cu','B.Cu'] else .0152
        k=.048 if thick==.035 else .024
        cross_mil2=seg['width_mm']*thick/.0254**2
        rise=(load/(k*cross_mil2**.725))**(1/.44)
        est.append(rise)
    power[label]={'load_A':load,'one_conductive_path_resistance_ohm_60C':resistance,
                  'copper_drop_V':load*resistance,'copper_loss_W':load*load*resistance,
                  'max_IPC2221_trace_rise_C_estimate':max(est),'segments':segments}

# Switching converter loss envelope: efficiency is an explicit engineering
# assumption, not a manufacturer-guaranteed minimum or a measured value.
vin=5.25;vout=3.3;load=.5;ambient=50;efficiency_floor=.80
loss=vout*load*(1/efficiency_floor-1)
thermal={'design_current_A':load,'ambient_C':ambient,'assumed_efficiency_floor':efficiency_floor,
 'total_converter_loss_W':loss,'junction_C_if_all_loss_in_IC_at_89K_per_W':ambient+89*loss,
 'junction_C_sensitivity_at_150K_per_W':ambient+150*loss,
 'thermal_pass_is_conditional_on_assumptions':True,'design_junction_limit_C':125,
 'minimum_efficiency_to_stay_below_125C_at_150K_per_W':vout*load/(vout*load+(125-ambient)/150)}
# L tolerance -20%; frequency includes -6% spread, not unspecified oscillator tolerance.
L=4.7e-6*.8;frequency=1.1e6*.94
ripple=vout*(vin-vout)/(vin*L*frequency);irms=math.sqrt(load**2+ripple**2/12)
inductor={'part':'Bourns SRN4018-4R7M','nominal_H':4.7e-6,'minimum_L_H':L,
 'frequency_Hz_assumption':frequency,'ripple_A_pp':ripple,'peak_A':load+ripple/2,
 'rms_A':irms,'rating_rms_A':1.9,'rating_saturation_A':2.,'DCR_max_25C_ohm':.084,
 'estimated_copper_loss_60C_W':irms**2*.084*(1+.00393*40),
 'estimated_temperature_rise_from_rated_40C_C':40*(irms/1.9)**2,
 'note':'Normal 500mA operation only; inductor saturation is below IC peak current limit, so do not claim 2A board rating or guaranteed fault-current saturation margin.'}
# Effective capacitances are explicit minimum component-selection requirements.
capacitors={'C1_nominal_uF':22,'C1_min_effective_uF_at_5V_50C':10,
 'C2_C8_nominal_total_uF':44,'C2_C8_min_effective_total_uF_at_3V3_50C':22,
 'required_input_ripple_current_A_rms':load/2,'assumed_output_ESR_ohm':.01,
 'output_ripple_V_estimate':ripple/(8*frequency*22e-6)+ripple*.01}
# USB connector voltage is a stated design input at the PCB under load.
# PTC hot resistance is screened at twice its specified R1max, not guaranteed.
in_copper_R=sum(power[k]['one_conductive_path_resistance_ohm_60C'] for k in ['USB_to_fuse','fuse_to_diode','diode_to_buck'])
fuse={'part':'MF-NSMF110/16X-2','rated_hold_A_at_23C':1.1,'hold_A_at_50C':.83,
 'hold_A_at_60C':.80,'R1max_23C_ohm':.23,'assumed_hot_resistance_ohm':.46,
 'input_screen_A':.65,'hot_drop_V':.65*.46,'hot_loss_W':.65**2*.46}
diodes={'part':'Vishay SS14-E3/61T','screen_forward_drop_V':.5,
 'loss_W_at_055A':.55*.5,'junction_C_at_50C_theta150':50+.55*.5*150}
input_budget={'minimum_USB_voltage_at_connector_under_load_V':4.75,
 'screen_current_A':.65,'additional_shield_VBUS_load_A':.1,'converter_input_lower_bound_V':4.75-.5-.65*(.46+power['USB_to_fuse']['one_conductive_path_resistance_ohm_60C'])-.55*sum(power[k]['one_conductive_path_resistance_ohm_60C'] for k in ['fuse_to_diode','diode_to_buck'])-.01,
 'ground_return_drop_allowance_V':.01,'converter_minimum_input_V':3.8,
 'note':'500mA 3V3 load requires an adequately rated source. This is not a claim of USB enumeration/inrush compliance or operation at every USB cable-drop corner.'}
input_budget['calculated_input_A_at_lower_bound_and_80pct_efficiency']=3.3*.5/(.8*input_budget['converter_input_lower_bound_V'])
assert input_budget['converter_input_lower_bound_V']>3.8
assert input_budget['calculated_input_A_at_lower_bound_and_80pct_efficiency'] < .55
result={'board':str(BOARD.relative_to(ROOT)),'USB':usb,'GND':ground_info,'power':power,'buck_thermal_screening':thermal,'inductor':inductor,'capacitors':capacitors,'fuse':fuse,'diode':diodes,'input_budget':input_budget,
        'assumptions':{'copper_temperature_for_resistance_C':60,'via_plating_mm':.020,
        'power_path_note':'One existing conductive path; parallel vias/paths ignored conservatively. Ground-plane and component resistance are not included.',
        'thermal_method':'IPC-2221 empirical trace screen, not IPC-2152 certification or a board thermal simulation.'}}
out=ROOT/'docs/validation/electrical-audit.json';out.write_text(json.dumps(result,indent=2))
print(json.dumps({'USB':usb,'GND':{k:v for k,v in ground_info.items() if k!='missing_ground_samples'},
                  'missing_ground_count':len(missing),'power':{k:{a:c for a,c in v.items() if a!='segments'} for k,v in power.items()}},indent=2))
assert thermal['junction_C_sensitivity_at_150K_per_W'] < 125
assert inductor['peak_A'] < inductor['rating_saturation_A']
assert usb['all_on_top'] and usb['vias']==0
assert max(usb[c]['absolute_skew_mm'] for c in ['A','B'])<=.1
assert ground_info['signal_track_count_L2']==0 and ground_info['connected_copper_regions']==1 and not missing
