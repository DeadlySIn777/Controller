"""Bounded motherboard-only IO3 supply correction; retained MC is read-only.

apply_io3_upgrade(tree, model) transforms copies and returns (tree, model,
receipt). The model can be a full assembly or a components dictionary. Parent
integration must provide CNC_MB_IO3 and CNC_MB_IO3 footprints in its tables.
"""
from __future__ import annotations
import copy, hashlib, json, shutil, subprocess, uuid
from pathlib import Path
from hardware_build_assembly import parse,dump,child,children,value,q,point,ref_property

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/motherboard_io3_upgrade'
REPORT=ROOT/'reports/motherboard-io3-upgrade-20260930'
KICAD='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
NS=uuid.UUID('89cbfd6c-46c8-56e9-bc90-23d55687c667')
uid=lambda n:str(uuid.uuid5(NS,n))
LOCAL='IO_3V3_REG_LOCAL'
ENDS=(('U2002','3'),('L2002','2'),('C2005','1'),('C2010','1'))
PIN_NAMES={'1':'PG','2':'SW','3':'VOS','4':'GND','5':'EN','6':'VIN','7':'MODE/S-CONF','8':'SS/TR','9':'FB/VSET'}
RREF='R18001'
TOPREF='R18002'
FB_BOTTOM_MPN='TNPW06032K55BYEA'
FB_TOP_MPN='TNPW060311K5BYEA'
RMPN='KRL2012E-C-R015-F-T5'
RFP='CNC_MB_IO3:KRL2012_Susumu'
LIBID='CNC_MB_IO3:TPS62902RPJR'

def symbol_for(tree,ref):
    found=[s for s in children(tree,'symbol') if value(ref_property(s)[2])==ref]
    if len(found)!=1:raise ValueError('Expected exactly one '+ref)
    return found[0]

def coords(tree,symbol):
    at=child(symbol,'at')
    if len(at)>3 and float(at[3])!=0:raise ValueError('Unreviewed rotation')
    lib=value(child(symbol,'lib_id')[1])
    defs=[s for s in children(child(tree,'lib_symbols'),'symbol') if value(s[1])==lib]
    if len(defs)!=1:raise ValueError('Ambiguous embedded definition')
    out={}
    for sub in children(defs[0],'symbol'):
        for pin in children(sub,'pin'):
            n=value(child(pin,'number')[1]);xy=point(child(pin,'at'))
            out[n]=(round(float(at[1])+xy[0],4),round(float(at[2])-xy[1],4))
    return out,defs[0]

def exact_label(tree,ref,pin,expected):
    start=coords(tree,symbol_for(tree,ref))[0][pin]
    reachable={start}
    while True:
        old=len(reachable)
        for wire in children(tree,'wire'):
            ends={point(x) for x in children(child(wire,'pts'),'xy')}
            if reachable &ends:reachable |= ends
        if old==len(reachable):break
    labels=[l for tag in ['label','hierarchical_label','global_label'] for l in children(tree,tag) if point(child(l,'at')) in reachable]
    if len(labels)!=1 or value(labels[0][1])!=expected:
        raise ValueError(f'{ref}.{pin} expected one exact {expected} label')
    return labels[0]

def apply_io3_upgrade(tree,model):
    t,m=copy.deepcopy(tree),copy.deepcopy(model)
    parts=m['components'] if 'components' in m else m
    u=parts.get('U2002')
    if not u or u.get('mpn')!='TPS62901RPJR' or u.get('footprint')!='CNC_MC_Power:TPS62901_RPJ9':
        raise ValueError('Unexpected retained U2002 exact MPN/footprint')
    if RREF in parts:raise ValueError('IO3 upgrade already applied/ref collision')
    regulator=symbol_for(t,'U2002');_,definition=coords(t,regulator)
    names={value(child(p,'number')[1]):value(child(p,'name')[1]) for sub in children(definition,'symbol') for p in children(sub,'pin')}
    if names!=PIN_NAMES:raise ValueError('Manufacturer RPJ9 function map differs')
    relocated_io_port=None
    for ref,pin in ENDS:
        if parts[ref]['pins'].get(pin)!='IO_3V3':raise ValueError('Unexpected bounded endpoint '+ref+'.'+pin)
        label=exact_label(t,ref,pin,'IO_3V3')
        if label[0]=='hierarchical_label':
            if relocated_io_port is not None:raise ValueError('Unexpected multiple IO3 hierarchy ports')
            relocated_io_port=copy.deepcopy(label)
            label[0]='label';label.remove(child(label,'shape'))
        label[1]=q(LOCAL)
        parts[ref]['pins'][pin]=LOCAL
    newdef=parse(dump(definition).replace('MC_mc_local_power:TPS62901RPJR',LIBID).replace('TPS62901RPJR','TPS62902RPJR'))
    child(t,'lib_symbols').append(newdef)
    child(regulator,'lib_id')[1]=q(LIBID)
    for prop in children(regulator,'property'):
        if value(prop[1]) in ['Value','MPN']:prop[2]=q('TPS62902RPJR')
    u.update(value='TPS62902RPJR',mpn='TPS62902RPJR',
        inherited_mpn='TPS62901RPJR',component_substitution='MB-IO3-001',
        io3_source_current_allocation_a=2)
    if parts['R2005']['pins']!={'1':'IO_3V3_MODE','2':'LOGIC_GND'} or parts['R2005']['mpn']!='CRCW060332K4FKEA':
        raise ValueError('Unexpected retained mode resistance/endpoint')
    exact_label(t,'R2005','2','LOGIC_GND')[1]=q('CORE_5V')
    parts['R2005']['pins']['2']='CORE_5V'
    parts['R2005'].update(value='0ohm MODE tied VIN',mpn='CRCW06030000Z0EA',
        inherited_mpn='CRCW060332K4FKEA',resistance_ohm=0,
        component_substitution='MB-IO3-001')
    for prop in children(symbol_for(t,'R2005'),'property'):
        if value(prop[1])=='Value':prop[2]=q('0ohm MODE tied VIN')
        if value(prop[1])=='MPN':prop[2]=q('CRCW06030000Z0EA')
    if parts['R2008']['mpn']!='CRCW0603301KFKEA' or parts['R2008']['pins']!={'1':'IO_3V3_VSET','2':'LOGIC_GND'}:
        raise ValueError('Unexpected retained VSET bottom part/endpoint')
    parts['R2008'].update(value='2.55k 0.1% 10ppm',mpn=FB_BOTTOM_MPN,
        inherited_mpn='CRCW0603301KFKEA',resistance_ohm=2550,tolerance=.001,
        temperature_coefficient_ppm_k=10,component_substitution='MB-IO3-001')
    for prop in children(symbol_for(t,'R2008'),'property'):
        if value(prop[1])=='Value':prop[2]=q('2.55k 0.1% 10ppm')
        if value(prop[1])=='MPN':prop[2]=q(FB_BOTTOM_MPN)
    # Reuse reviewed native passive symbol without rotating or changing pin map.
    resistor=copy.deepcopy(symbol_for(t,'R2007'))
    oldcoords,_=coords(t,resistor)
    oldat=point(child(resistor,'at'));newat=(760.73,436.88)
    delta=(newat[0]-oldat[0],newat[1]-oldat[1])
    child(resistor,'at')[1:3]=[str(x) for x in newat]
    child(resistor,'uuid')[1]=q(uid(RREF))
    for prop in children(resistor,'property'):
        key=value(prop[1]);at=child(prop,'at');at[1:3]=[str(round(float(at[1])+delta[0],4)),str(round(float(at[2])+delta[1],4))]
        if key=='Reference':prop[2]=q(RREF)
        if key=='Value':prop[2]=q('15mohm 1% 50ppm 1W')
        if key=='MPN':prop[2]=q(RMPN)
        if key=='Footprint':prop[2]=q(RFP)
    for project in children(child(resistor,'instances'),'project'):
        for path in children(project,'path'):child(path,'reference')[1]=q(RREF)
    t.append(resistor)
    for pin,net in [('1',LOCAL),('2','IO_3V3')]:
        xy=(round(oldcoords[pin][0]+delta[0],4),round(oldcoords[pin][1]+delta[1],4))
        if pin=='2' and relocated_io_port is not None:
            port=copy.deepcopy(relocated_io_port);child(port,'at')[1:3]=[str(x) for x in xy]
            t.append(port)
        else:
            t.append(['label',q(net),['at',str(xy[0]),str(xy[1]),'0'],
                ['effects',['font',['size','.85','.85']],['justify','left','bottom']],['uuid',q(uid(RREF+pin))]])
    parts[RREF]={'kind':'R','value':'15mohm 1% 50ppm 1W','mpn':RMPN,'footprint':RFP,
        'physical':True,'pins':{'1':LOCAL,'2':'IO_3V3'},'no_connect':[],
        'resistance_ohm':.015,'tolerance':.01,'temperature_coefficient_ppm_k':50,
        'power_rating_w':1,'source_block':'motherboard_io3_upgrade','source_reference':RREF,
        'role':'controlled distributed-cap damping; local VOS remains upstream',
        'status':'source_candidate_not_layout_or_physical_qualified'}
    top=copy.deepcopy(resistor)
    child(top,'uuid')[1]=q(uid(TOPREF));child(top,'at')[2]=str(newat[1]-30.48)
    for prop in children(top,'property'):
        at=child(prop,'at');at[2]=str(round(float(at[2])-30.48,4))
        k=value(prop[1])
        if k=='Reference':prop[2]=q(TOPREF)
        if k=='Value':prop[2]=q('11.5k 0.1% 10ppm')
        if k=='MPN':prop[2]=q(FB_TOP_MPN)
        if k=='Footprint':prop[2]=q('Resistor_SMD:R_0603_1608Metric')
    for project in children(child(top,'instances'),'project'):
        for path in children(project,'path'):child(path,'reference')[1]=q(TOPREF)
    t.append(top)
    for pin,net in [('1',LOCAL),('2','IO_3V3_VSET')]:
        xy=(round(oldcoords[pin][0]+delta[0],4),round(oldcoords[pin][1]+delta[1]-30.48,4))
        t.append(['label',q(net),['at',str(xy[0]),str(xy[1]),'0'],
            ['effects',['font',['size','.85','.85']],['justify','left','bottom']],['uuid',q(uid(TOPREF+pin))]])
    parts[TOPREF]={'kind':'R','value':'11.5k 0.1% 10ppm','mpn':FB_TOP_MPN,
        'footprint':'Resistor_SMD:R_0603_1608Metric','physical':True,
        'pins':{'1':LOCAL,'2':'IO_3V3_VSET'},'no_connect':[],
        'resistance_ohm':11500,'tolerance':.001,'temperature_coefficient_ppm_k':10,
        'source_block':'motherboard_io3_upgrade','source_reference':TOPREF,
        'status':'source_candidate_not_layout_or_physical_qualified',
        'role':'scaled-low-impedance external-FB top;70nA leakage screen'}
    receipt={'id':'MB-IO3-001','old_mpn':'TPS62901RPJR','new_mpn':'TPS62902RPJR',
        'same_footprint':'CNC_MC_Power:TPS62901_RPJ9','pin_function_map':PIN_NAMES,
        'exact_pin_net_ledger':[{'ref':r,'pin':p,'old_model_net':'IO_3V3','new_model_net':LOCAL,
            'old_native_net':'/IO_3V3','new_native_parent_net':'/mc_local_power/'+LOCAL} for r,p in ENDS],
        'mode_pin_ledger':{'ref':'R2005','pin':'2','old_model_net':'LOGIC_GND','new_model_net':'CORE_5V',
            'new_native_parent_net':'/mc_local_power/CORE_5V','old_mpn':'CRCW060332K4FKEA',
            'old_value':'32.4k 1%','new_mpn':'CRCW06030000Z0EA','new_value':'0ohm MODE tied VIN'},
        'bottom_part_ledger':{'ref':'R2008','old_mpn':'CRCW0603301KFKEA','old_value':'301k 1%',
            'new_mpn':FB_BOTTOM_MPN,'new_value':'2.55k 0.1% 10ppm','pins_unchanged':True},
        'added_refs':[RREF,TOPREF],'new_components':{r:parts[r] for r in [RREF,TOPREF]},
        'all_other_retained_endpoints_unchanged':True,
        'library_id':LIBID,'library_file':'hardware/motherboard_io3_upgrade/CNC_MB_IO3.kicad_sym',
        'footprint_file':'hardware/motherboard_io3_upgrade/CNC_MB_IO3.pretty/KRL2012_Susumu.kicad_mod',
        'manufacturing_ready':False,'original_mc_changed':False,
        'source_bounds':{'rmin_at_max_junction_175c_ohm':.015*.99*(1-150*50e-6),
            'rmax_at_max_junction_175c_ohm':.015*1.01*(1+150*50e-6),
            'normal_design_current_a':.9087077446234255,'regulator_rating_a':2,
            'local_nominal_cout_f':22.1e-6,'distributed_nominal_cout_f':66.11e-6,
            'fb_resistors_ohm':[11500,2550],'fb_current_max_a':70e-9,
            'fb_error_max_v':.0008066905,'fb_reference_error_fraction':.009,
            'fb_resistor_temperature_range_c':[0,85],'fb_resistor_drift_fraction':.0005,
            'mode':'HIGH externalFB2.5MHz forcedPWM outputdischarge'},
        'open_engineering_gates':['Actual effective local Cout>=10uF and distributed damping stability/ESR.',
            'PCB must not bypass R18001 by planes/traces; VOS Kelvin local node.',
            'FB resistors use0..85C and published500ppm/1000h general-operation drift limit; exact lifetime/purchasing and routing/noise margins remain qualified conditions.',
            'Regulator input/inductor thermal/actual startup and target FPGA power.',
            'Overall allocation uses explicit reservations rather than complete guaranteed dynamic maxima.']}
    return t,m,receipt

def build():
    OUT.mkdir(exist_ok=True);REPORT.mkdir(exist_ok=True)
    source=ROOT/'hardware/motion_card'
    tree=parse((source/'mc_local_power.kicad_sch').read_text(encoding='utf8'))
    full=json.loads((source/'design.json').read_text(encoding='utf8'))
    refs={value(ref_property(s)[2]) for s in children(tree,'symbol') if not value(ref_property(s)[2]).startswith('#')}
    model={'schema_version':1,'revision':'motherboard-io3-upgrade-r0.1','manufacturing_ready':False,
        'components':{r:copy.deepcopy(full['components'][r]) for r in refs if r in full['components']}}
    tree,model,receipt=apply_io3_upgrade(tree,model)
    # Standalone test fixture has no parent. Real apply() preserves the IO3
    # hierarchy port at R18001.2 and leaves all other hierarchy ports intact.
    for label in children(tree,'hierarchical_label'):
        label[0]='label';label.remove(child(label,'shape'))
    root=value(child(tree,'uuid')[1])
    for s in children(tree,'symbol'):
        ref=value(ref_property(s)[2]);instances=child(s,'instances')
        if instances:
            instances[1:]=[['project',q('motherboard_io3_upgrade'),['path',q('/'+root),['reference',q(ref)],['unit','1']]]]
    (OUT/'motherboard_io3_upgrade.kicad_sch').write_text(dump(tree)+'\n',encoding='utf8')
    (OUT/'design.json').write_text(json.dumps(model,indent=2)+'\n',encoding='utf8')
    definition=next(s for s in children(child(tree,'lib_symbols'),'symbol') if value(s[1])==LIBID)
    library=copy.deepcopy(definition);library[1]=q('TPS62902RPJR')
    (OUT/'CNC_MB_IO3.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '+dump(library)+')\n',encoding='utf8')
    shutil.copyfile(source/'mc_local_power.kicad_sym',OUT/'mc_local_power.kicad_sym')
    (OUT/'sym-lib-table').write_text('(sym_lib_table(version 7)(lib(name "MC_mc_local_power")(type "KiCad")(uri "${KIPRJMOD}/mc_local_power.kicad_sym")(options "")(descr "Retained MC source"))(lib(name "CNC_MB_IO3")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_IO3.kicad_sym")(options "")(descr "Exact IO3 correction")))\n',encoding='utf8')
    fp=OUT/'CNC_MB_IO3.pretty';fp.mkdir(exist_ok=True)
    (fp/'KRL2012_Susumu.kicad_mod').write_text('''(footprint "KRL2012_Susumu"(version 20241229)(generator "pcbnew")(layer "F.Cu")(attr smd)
 (property "Reference" "REF**"(at 0 -2 0)(layer "F.SilkS")(effects(font(size .8 .8)(thickness .15))))
 (property "Value" "KRL2012_Susumu"(at 0 2 0)(layer "F.Fab")(effects(font(size .7 .7)(thickness .1))))
 (fp_rect(start -.625 -1)(end .625 1)(stroke(width .1)(type default))(fill none)(layer "F.Fab"))
 (fp_rect(start -1.25 -1.35)(end 1.25 1.35)(stroke(width .05)(type default))(fill none)(layer "F.CrtYd"))
 (pad "1" smd rect(at -.65 0)(size .7 2.2)(layers "F.Cu" "F.Paste" "F.Mask"))
 (pad "2" smd rect(at .65 0)(size .7 2.2)(layers "F.Cu" "F.Paste" "F.Mask")))
''',encoding='utf8')
    shutil.copytree(ROOT/'hardware/mc_local_power/CNC_MC_Power.pretty',OUT/'CNC_MC_Power.pretty',dirs_exist_ok=True)
    (OUT/'fp-lib-table').write_text('(fp_lib_table(version 7)(lib(name "CNC_MB_IO3")(type "KiCad")(uri "${KIPRJMOD}/CNC_MB_IO3.pretty")(options "")(descr "Susumu manufacturer lands"))(lib(name "CNC_MC_Power")(type "KiCad")(uri "${KIPRJMOD}/CNC_MC_Power.pretty")(options "")(descr "Retained power lands")))\n',encoding='utf8')
    (OUT/'motherboard_io3_upgrade.kicad_pro').write_text(json.dumps({'meta':{'filename':'motherboard_io3_upgrade.kicad_pro','version':1},'erc':{'rule_severities':{k:'warning' for k in ['single_global_label','four_way_junction','simulation_model_issue','footprint_filter']}}},indent=2)+'\n',encoding='utf8')
    for table in ['sym-lib-table','fp-lib-table']:
        path=OUT/table;path.write_text(dump(parse(path.read_text(encoding='utf8')))+'\n',encoding='utf8')
    for action in [('sch','export','netlist','--format','kicadxml','-o',str(OUT/'netlist.xml'),str(OUT/'motherboard_io3_upgrade.kicad_sch')),
                   ('sch','erc','--format','json','--output',str(REPORT/'erc.json'),str(OUT/'motherboard_io3_upgrade.kicad_sch'))]:
        r=subprocess.run([KICAD,*action],capture_output=True,text=True,encoding='utf8');
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    receipt['source_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'mc_local_power.kicad_sch',source/'design.json',OUT/'motherboard_io3_upgrade.kicad_sch',OUT/'design.json',OUT/'CNC_MB_IO3.kicad_sym',fp/'KRL2012_Susumu.kicad_mod']}
    (REPORT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
    return receipt

if __name__=='__main__':
    print(json.dumps(build(),indent=2))
