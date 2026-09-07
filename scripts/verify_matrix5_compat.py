"""Check actual PCB pads against the independent Matrix5 reference extraction.

No routing or mutation. Does not claim a physical fit or powered test.
"""
from pathlib import Path
import hashlib,json,re,sys,subprocess
from sexpr import parse,child,children,dump
ROOT=Path(__file__).resolve().parent.parent
PCB=ROOT/'hardware/Matrix6/Matrix6.kicad_pcb'
b=parse(PCB.read_text())
BASE_REV='ee580b181c5c248c455f0519c6c52200018bf0b3'
def baseline(path):
    return subprocess.check_output(['git','show',f'{BASE_REV}:{path}'],cwd=ROOT,text=True)
original=parse(baseline('hardware/Matrix6/Matrix6.kicad_pcb'))
def usb_copper(board):
    return sorted(dump(t) for tag in ['segment','arc','via'] for t in children(board,tag)
                  if child(t,'net') and child(t,'net')[1] in ['/USB_N','/USB_P','/USB_A_P','/MCU_USB_N','/MCU_USB_P'])
assert usb_copper(b)==usb_copper(original), 'USB copper changed from reviewed v0.4'
pro=json.loads((ROOT/'hardware/Matrix6/Matrix6.kicad_pro').read_text())
oldpro=json.loads(baseline('hardware/Matrix6/Matrix6.kicad_pro'))
for key in ['rules','rule_severities','drc_exclusions']:
    assert pro['board']['design_settings'][key]==oldpro['board']['design_settings'][key],key
assert pro['net_settings']['classes']==oldpro['net_settings']['classes']
rules=(ROOT/'hardware/Matrix6/Matrix6.kicad_dru').read_text()
expected=baseline('hardware/Matrix6/Matrix6.kicad_dru').replace("A.NetName == '/VBUS_FUSED'\"", "A.NetName == '/VBUS_FUSED' && !A.memberOfGroup('CHARGER_BRANCH')\"")
expected += "\n(rule \"Charger branch minimum\" (condition \"A.memberOfGroup('CHARGER_BRANCH')\") (constraint track_width (min 0.25mm)))\n"
assert rules==expected, 'Only reviewed low-current charger escape rule may differ'
fps={next(x[2] for x in children(f,'property') if x[1]=='Reference'):f for f in children(b,'footprint')}
reference=json.loads((ROOT/'docs/reference/matrix5-pinout.json').read_text())['headers']
shields=json.loads((ROOT/'docs/reference/matrix5-shield-interface.json').read_text())['shields']
exceptions={('H2',5):'USB_DM',('H2',6):'USB_DP'}
aliases={'3V3':'+3V3','VBUS':'VBUS_FUSED','U0RXD':'IO44_RX','U0TXD':'IO43_TX'}
pads={}
for ref in ['H1','H2']:
    f=fps[ref];fx,fy,angle=map(float,child(f,'at')[1:4]);assert angle==180
    for q in children(f,'pad'):
        n=int(q[1]);x,y=map(float,child(q,'at')[1:3]);x,y=fx-x,fy-y
        name=child(q,'net')[1]
        pads[ref,n]={'x_mm':x,'y_mm':y,'net':name}
        r=next(p for p in reference[ref] if p['pin']==n)
        assert abs(x-(101.27+r['x_mm']))<1e-5 and abs(y-(153.26-r['y_mm']))<1e-5,(ref,n,r,x,y)
        if (ref,n) in exceptions:assert name.startswith('unconnected-'),(ref,n,name)
        else:assert name=='/'+aliases.get(r['signal'],r['signal']),(ref,n,name,r)
assert len(pads)==40
def expected_gpio(name):
    direct={'GND':'GND','3V3':'+3V3','VBUS':'VBUS_FUSED','VBUS_IN':'VBUS_FUSED','MOSI':'IO11','SDA':'IO11','SCLK':'IO12','SCL':'IO12','MISO':'IO13','HEAT_EN':'IO14','CS':'IO1','DC':'IO2','LCD_RST':'IO3','BL_PWM':'IO4'}
    if name in direct:return direct[name]
    if name.startswith('IO'):return name
    m=re.fullmatch(r'(?:CS|XSHUT|CE|G|T|A)([1-9])',name)
    if m:return 'IO'+m[1]
    raise AssertionError('Unmapped shield signal '+name)
results={}
for name,pins in shields.items():
    active=[]
    for pin in pins:
        key=pin['header'],pin['pin'];actual=pads[key]
        assert abs(actual['x_mm']-(101.27+pin['x_mm']))<1e-5
        assert abs(actual['y_mm']-(153.26-pin['y_mm']))<1e-5
        if pin['used']:
            assert key not in exceptions
            target=expected_gpio(pin['net_on_shield'])
            assert actual['net']=='/'+target,(name,key,actual,target)
            active.append({'pin':f'{key[0]}.{key[1]}','shield_net':pin['net_on_shield'],'matrix6_net':target})
    results[name]={'pad_positions_checked':len(pins),'used_pins_checked':len(active),'connections':active,'status':'PIN_MAP_PASS'}
report={'pcb_sha256':hashlib.sha256(PCB.read_bytes()).hexdigest(),'preserved_from_v04':{'usb_copper':True,'design_rules_except_documented_charger_escape':True,'net_classes':True},'row_pitch_mm':2.54,'column_spacing_mm':33.02,'header_pins':40,'main_pins_matched':38,'intentional_NC':{f'{h}.{p}':signal for (h,p),signal in exceptions.items()},'shields':results,'scope':'XY pad positions and used signal/power pin assignments only. Connector mating height, all shield loads, radio behavior and physical operation remain prototype tests.'}
(ROOT/'docs/validation/matrix5-compatibility.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: 40 pad positions; 38 Main assignments + 2 documented NC; all {len(shields)} shield interfaces matched.')
