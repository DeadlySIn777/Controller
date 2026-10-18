"""Add the reviewed BASE 64 NC promotions to an isolated motherboard source.

No retained MC/FPGA source, production motherboard, PCB or root builder is
written. apply_base_allocation() is a bounded callable for root integration.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET

from hardware_build_assembly import parse,dump,child,children,value,q,point,ref_property
from hardware_validate_fpga_core import primary_pins

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/motherboard-fpga-source-20260930'
LIVE=ROOT/'hardware/motherboard'
KICAD=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
NS=uuid.UUID('a66868c7-72ac-5186-b31b-82de27ba4cc6')
FIELD_ALIASES={'PRB0_FPGA':('G12','PROBE_FPGA'),
               'PRB1_FPGA':('G15','TOOLSETTER_FPGA'),
               'EXT_PERMIT_FPGA':('G16','PROTECTIVE_STATUS_FPGA')}
SHARED_ROOT={'FPGA_OUTPUT_REQUEST','WD_M_OK','WD_O_OK'}
REVIEWED_BASE_SHA256='1e690a0aea7032d05df9c6c83b203137f091393b373ec7eb8dc413dd0c581aeb'
REVIEWED_COLUMNS=('signal','ball','direction','allocation_state','manufacturer_pin',
                  'bank','worksheet_row','vccio_nominal_v','io_standard')
SLOW_ENABLE_RECEIPT=ROOT/'reports/motherboard-fpga-allocation-20260930/slow-enable-allocation.json'
REVIEWED_SLOW_ENABLE_SHA256='45d4bc6443c955e6e300264353fc06c7bfac8f9d788cb9094e2459eb86d46890'
SLOW_ENABLE_PINS=(('FAST_PORTS_ENABLE','M4','GPIOB_TXP00',192),
                  ('XF_POWER_ENABLE','M6','GPIOB_TXP05',197))
HOME_DEALLOC_PINS=(
 ('HOME0_FPGA','B10','GPIOR_82','BANK3A',86),
 ('HOME1_FPGA','B11','GPIOR_83','BANK3A',87),
 ('HOME2_FPGA','A11','GPIOR_84','BANK3A',88),
 ('HOME3_FPGA','C12','GPIOR_85','BANK3A',89),
 ('HOME4_FPGA','C11','GPIOR_86','BANK3A',90),
 ('HOME5_FPGA','D12','GPIOR_89','BANK3A',93),
 ('HOME6_FPGA','C14','GPIOR_102','BANK3B',94),
 ('HOME7_FPGA','D13','GPIOR_103','BANK3B',95),
 ('HOME8_FPGA','B16','GPIOR_106','BANK3B',98),
 ('HOME9_FPGA','A14','GPIOR_90','BANK3B',99),
 ('HOME10_FPGA','E12','GPIOR_91','BANK3B',100),
 ('HOME11_FPGA','B14','GPIOR_92','BANK3B',101))
HOME_SPEC=ROOT/'reports/motherboard-is2-contract-20260930/inputs/spec/modules.json'
HOME_SPEC_SHA256='d9bc85530a921e8db26814abf80dca814d09cb7f15eb951b0c163a25cd9c0597'
RESERVED_HEALTH_PINS=(
 ('HEALTH_SR_CLK','C8','GPIOL_72_EXTFB0_CDI14','BANK1E',76,'obsolete_rack_acquisition'),
 ('HEALTH_SR_DATA','T12','GPIOB_RXP07','BANK4A',173,'obsolete_rack_acquisition'),
 ('HEALTH_SR_LOAD_N','D8','GPIOL_73_EXTFB1_CDI15','BANK1E',77,'obsolete_rack_acquisition'),
 ('XS_CS_N','K16','GPIOR_132_CDI19','BANK3D',129,'future_reserved_no_base_interface'),
 ('XS_MISO','T3','GPIOB_TXN03','BANK4B',182,'future_reserved_no_base_interface'),
 ('XS_MOSI','J13','GPIOR_133_CDI18','BANK3D',130,'future_reserved_no_base_interface'),
 ('XS_REFCLK','J14','GPIOR_135_CDI17','BANK3D',131,'future_reserved_no_base_interface'),
 ('XS_SCLK','K15','GPIOR_136_CDI16','BANK3D',132,'future_reserved_no_base_interface'),
 ('XS_SYNC_STROBE','L13','GPIOR_157_PLLIN','BANK3E',149,'future_reserved_no_base_interface'),
 ('RAILS_OK_FPGA','P4','GPIOB_TXN01','BANK4B',180,'required_existing_qualified_rail_bridge'))

def uid(n):return str(uuid.uuid5(NS,n))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write_json(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf8')
def shape(direction):return {'input':'input','output':'output','bidirectional':'bidirectional'}[direction]

def actual_pin_coordinates(core,reference='U1001'):
    us=[s for s in children(core,'symbol') if value(ref_property(s)[2])==reference]
    if len(us)!=1:raise ValueError('Expected one '+reference)
    u=us[0];at=child(u,'at')
    if len(at)>3 and float(at[3])!=0:raise ValueError('Rotated FPGA instance requires an explicitly reviewed transformation')
    lib=value(child(u,'lib_id')[1]);libs=child(core,'lib_symbols')
    symbols=[s for s in children(libs,'symbol') if value(s[1])==lib]
    if len(symbols)!=1:raise ValueError('FPGA embedded symbol ambiguous')
    definition=symbols[0];official=primary_pins();coordinates={}
    for sub in children(definition,'symbol'):
        for p in children(sub,'pin'):
            number=value(child(p,'number')[1]);name=value(child(p,'name')[1])
            if number in coordinates or number not in official:raise ValueError('Unknown/duplicate FPGA ball '+number)
            if name!=official[number]['name']:raise ValueError('Manufacturer FPGA pin-name mismatch '+number)
            xy=point(child(p,'at'));coords=(round(float(at[1])+xy[0],4),round(float(at[2])-xy[1],4))
            coordinates[number]=dict(coordinate=coords,pin=p,manufacturer_name=name,
                bank=official[number]['bank'],worksheet_row=official[number]['row'],side='left' if xy[0]<0 else 'right')
    if len(coordinates)!=256:raise ValueError('Native FPGA symbol must contain all 256 balls')
    return coordinates

def fpga_sheet(root):
    s=[s for s in children(root,'sheet') if any(value(p[1])=='Sheetname' and value(p[2])=='fpga_core' for p in children(s,'property'))]
    if len(s)!=1:raise ValueError('Exactly one existing fpga_core hierarchy page is required')
    return s[0]

def hierarchy_item(signal,xy,direction,key):
    return ['hierarchical_label',q(signal),['shape',shape(direction)],['at',str(xy[0]),str(xy[1]),'0'],
        ['effects',['font',['size','0.95','0.95']],['justify','left','bottom']],['uuid',q(uid(key))]]

def rebuild_root_geometry(root,port_maps):
    """Repack generated sibling pages, preserving all UUIDs/net labels.

    Existing root ports must each have exactly one simple stub wire/label. This
    refuses user-drawn buses or branching wires rather than erasing them.
    """
    sheets=children(root,'sheet');old_stubs=[];layouts=[]
    for s in sheets:
        name=next(value(p[2]) for p in children(s,'property') if value(p[1])=='Sheetname')
        existing={}
        for pin in children(s,'pin'):
            coord=point(child(pin,'at'));wires=[]
            for w in children(root,'wire'):
                pts=[point(p) for p in children(child(w,'pts'),'xy')]
                if coord in pts:wires.append((w,pts))
            if len(wires)!=1:raise ValueError('Expected one root stub for '+name+'/'+value(pin[1]))
            w,pts=wires[0];other=next(p for p in pts if p!=coord)
            labels=[l for l in children(root,'label') if point(child(l,'at'))==other]
            if len(labels)!=1:raise ValueError('Expected one root endpoint label for '+name+'/'+value(pin[1]))
            if any(point(child(j,'at')) in pts for j in children(root,'junction')):
                raise ValueError('Branched root stub needs reviewed integration '+name)
            existing[value(pin[1])]=dict(pin=copy.deepcopy(pin),wire=copy.deepcopy(w),label=copy.deepcopy(labels[0]))
            old_stubs.extend([w,labels[0]])
        wanted=port_maps.get(name,{n:value(v['label'][1]) for n,v in existing.items()})
        if not set(existing)<=set(wanted):raise ValueError('Existing hierarchy port removed '+name)
        layouts.append((s,name,existing,wanted))
    for x in old_stubs:root.remove(x)
    paper=child(root,'paper')
    max_height=float(paper[3])-40 if paper is not None and value(paper[1])=='User' and len(paper)>=4 else 800
    columns=[76.2]*3;changes=[]
    for s,name,existing,wanted in layouts:
        before=dict(at=point(child(s,'at')),size=point(child(s,'size')))
        ports=sorted(wanted);left_count=(len(ports)+1)//2
        height=round(max(55.88,left_count*5.08+15.24),4)
        col=min(range(3),key=lambda i:columns[i]);x=round(101.6+col*355.6,4);y=columns[col]
        columns[col]+=height+25.4
        if columns[col]>max_height:raise ValueError('Hierarchy packing exceeds actual source page')
        child(s,'at')[1:3]=[str(x),str(y)];child(s,'size')[1:3]=['177.8',str(height)]
        for prop in children(s,'property'):
            if value(prop[1])=='Sheetname':child(prop,'at')[1:3]=[str(x),str(round(y-3,4))]
            if value(prop[1])=='Sheetfile':child(prop,'at')[1:3]=[str(x),str(round(y+height+3,4))]
        for p in list(children(s,'pin')):s.remove(p)
        for i,n in enumerate(ports):
            left=i<left_count;row=i if left else i-left_count
            py=round(y+7.62+row*5.08,4);edge=x if left else round(x+177.8,4)
            end=round(edge+(-50.8 if left else 50.8),4)
            if n in existing:
                v=existing[n];pin,wire,label=v['pin'],v['wire'],v['label']
                child(pin,'at')[1:]=[str(edge),str(py),'180' if left else '0']
                child(label,'at')[1:3]=[str(end),str(py)]
                label[1]=q(wanted[n])
                child(wire,'pts')[1:]=[['xy',str(end),str(py)],['xy',str(edge),str(py)]]
            else:
                d=port_maps.get('_directions',{}).get(n,'bidirectional')
                pin=['pin',q(n),shape(d),['at',str(edge),str(py),'180' if left else '0'],
                     ['effects',['font',['size','1','1']]],['uuid',q(uid(name+'/'+n+'/root-pin'))]]
                wire=['wire',['pts',['xy',str(end),str(py)],['xy',str(edge),str(py)]],
                      ['stroke',['width','0'],['type','default']],['uuid',q(uid(name+'/'+n+'/root-wire'))]]
                label=['label',q(wanted[n]),['at',str(end),str(py),'0'],
                       ['effects',['font',['size','1','1']],['justify','left','bottom']],['uuid',q(uid(name+'/'+n+'/root-label'))]]
            s.append(pin);root.extend([wire,label])
        changes.append(dict(sheet=name,before=before,after=dict(at=(x,y),size=(177.8,height)),ports=len(ports)))
    return changes

def apply_base_allocation(root_tree,core_tree,proposal=None,native_before=None):
    """Return isolated transformed trees plus bounded metadata; inputs unchanged.

    The physical FPGA symbol remains manufacturer bidirectional GPIO; desired
    user directions are stated by typed hierarchy ports and the pin ledger.
    Existing local net labels survive the three adopted field aliases. Their
    protected front ends are still absent, so this step records their exact
    local endpoints rather than adding three unconnected extra root exports.
    """
    proposal=proposal or load(LIVE/'fpga-allocation-proposal.json')
    if proposal.get('vendor_fit') or proposal.get('manufacturing_ready'):raise ValueError('Proposal must preserve unproved readiness boundary')
    candidate=proposal['candidates']['base_preserve_all_current']
    if candidate['assigned']!=161 or candidate['unassigned']:raise ValueError('Only the complete BASE161 candidate is authorized')
    promotions=[r for r in candidate['signals'] if r['allocation_state']=='proposed_NC_to_named_signal']
    if len(promotions)!=64:raise ValueError('BASE must promote exactly64 NC balls')
    if len({r['ball'] for r in promotions})!=64:raise ValueError('Duplicate promotion ball')
    if candidate['existing_ball_repurposes']:raise ValueError('Optional five-pad reuse is not authorized here')
    official=primary_pins()
    for r in candidate['signals']:
        p=official[r['ball']]
        if (r['manufacturer_pin'],r['bank'],r['worksheet_row'])!=(p['name'],p['bank'],p['row']):raise ValueError('Proposal differs from official workbook '+r['ball'])
        if r['vccio_nominal_v']!=3.3 or r['io_standard']!='3.3_V_LVCMOS':raise ValueError('Unsupported user voltage '+r['ball'])
        if r['direction'] not in ('input','output','bidirectional'):raise ValueError('Unsupported pin direction '+r['ball'])
        if r['mode']=='LVDS_as_GPIO' and r['direction']!='input':raise ValueError('Reviewed BASE uses LVDS GPIO as inputs only '+r['ball'])
    bounded_rows=[{k:r[k] for k in REVIEWED_COLUMNS} for r in candidate['signals']]
    reviewed_sha=hashlib.sha256(json.dumps(bounded_rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if reviewed_sha!=REVIEWED_BASE_SHA256:raise ValueError('BASE pin/function ledger differs from the exact reviewed candidate')
    root=copy.deepcopy(root_tree);core=copy.deepcopy(core_tree)
    coordinates=actual_pin_coordinates(core)
    sheet=fpga_sheet(root)
    existing_ports={value(p[1]) for p in children(sheet,'pin')}
    parent_labels={}
    for p in children(sheet,'pin'):
        xy=point(child(p,'at'));wire=next(w for w in children(root,'wire') if xy in [point(v) for v in children(child(w,'pts'),'xy')])
        other=next(point(v) for v in children(child(wire,'pts'),'xy') if point(v)!=xy)
        label=next(l for l in children(root,'label') if point(child(l,'at'))==other)
        parent_labels[value(p[1])]=value(label[1])
    before_nodes={}
    if native_before is not None:
        for net in native_before.findall('.//nets/net'):
            for node in net.findall('node'):
                before_nodes[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name']
    ledger=[]
    for r in promotions:
        b=r['ball'];n=r['signal'];info=coordinates[b];xy=info['coordinate']
        nc=[c for c in children(core,'no_connect') if point(child(c,'at'))==xy]
        if len(nc)!=1:raise ValueError('Expected one actual NC cross at '+b)
        if any(point(child(l,'at'))==xy for l in children(core,'label')+children(core,'hierarchical_label')):
            raise ValueError('NC promotion already labelled '+b)
        core.remove(nc[0])
        ex=round(xy[0]+(-101.6 if info['side']=='left' else 10.16),4);ey=xy[1]
        core.extend([['wire',['pts',['xy',str(xy[0]),str(xy[1])],['xy',str(ex),str(ey)]],
                     ['stroke',['width','0'],['type','default']],['uuid',q(uid('U1001/'+b+'/new-wire'))]],
                     hierarchy_item(n,(ex,ey),r['direction'],'U1001/'+b+'/new-port')])
        parent= n if n in SHARED_ROOT else 'fpga_core/'+n
        parent_labels[n]=parent
        old=before_nodes.get(('U1001',b),'unconnected-(U1001-'+info['manufacturer_name']+'-Pad'+b+')')
        expected='unconnected-(U1001-'+info['manufacturer_name']+'-Pad'+b+')'
        if old!=expected:raise ValueError('Native old NC name differs from exact expected ball '+b)
        ledger.append(dict(reference='U1001',pin=b,manufacturer_pin=info['manufacturer_name'],bank=r['bank'],
            direction=r['direction'],signal=n,old_native_net=old,new_native_net='/'+parent,
            removed_nc_uuid=value(child(nc[0],'uuid')[1]),coordinate=list(xy),
            scope='exact previously NC FPGA pin only; no wildcard or non-FPGA rename',
            native_export_verified=False))
    alias_ledger=[]
    for n,(b,old) in FIELD_ALIASES.items():
        if old in parent_labels:raise ValueError('Alias physical port already exists '+old)
        labels=[l for l in children(core,'label') if value(l[1])==old]
        if not labels:raise ValueError('Missing actual preserved alias label '+old)
        # Preserve these existing local endpoints. Root can promote them when
        # the actual protected probe/permit front-end sheet is integrated.
        alias_ledger.append(dict(signal=n,ball=b,old_local_label=old,hierarchy_port=None,
            hierarchy_export_applied=False,
            root_physical_label='fpga_core/'+old,expected_native_net='/fpga_core/'+old,
            scope='same-pad semantic alias only; historical native net and boundary wiring preserved; field frontend/root bridge remains open'))
    directions={r['signal']:r['direction'] for r in candidate['signals']}
    for n,(b,old) in FIELD_ALIASES.items():directions[old]='input'
    geometry=rebuild_root_geometry(root,{'fpga_core':parent_labels,'_directions':directions})
    core.append(['text',q('BASE FPGA ALLOCATION / 64 former NC GPIO now exported. 161 user functions including clock; 22 GPIO remain NC.\nThree probe/permit semantic aliases preserve historical local endpoints. This adds pins and hierarchy, not peripheral circuits or gateware.\nHealth/OPI/watchdog endpoint obligations are in the bounded ledger. No healthy constants; Efinity fit and loaded timing remain unproved.'),
        ['at','560','774','0'],['effects',['font',['size','1.2','1.2']],['justify','left','top']],['uuid',q(uid('scope-note'))]])
    metadata=dict(schema_version=1,revision='motherboard-fpga-base-source-r01',candidate='base_preserve_all_current',
        manufacturing_ready=False,vendor_fit=False,physical_validation=False,
        source_scope='isolated candidate; current parent and retained MC/FPGA sources untouched',
        assigned_user_pins=161,free_user_gpio=22,promoted_nc_pin_count=64,
        old_fpga_hierarchy_ports=len(existing_ports),new_fpga_hierarchy_ports=len(parent_labels),
        exact_pin_rename_ledger=ledger,semantic_alias_exports=alias_ledger,
        root_sheet_port_map=parent_labels,desired_directions=directions,
        root_geometry_changes=geometry,optional_five_reuse_applied=False,
        parent_endpoint_obligations=endpoint_obligations(),
        symbol_library_changed=False,
        note='Manufacturer bidirectional pin type is retained for programmable GPIO; planned directions are checked independently and typed on the hierarchy ports. No gateware mode has been fitted.')
    metadata['reviewed_base_pin_function_sha256']=reviewed_sha
    return root,core,metadata


def apply_slow_enable_allocation(root_tree,core_tree,base_metadata,review_receipt=None):
    """Add ONLY the two independently reviewed slow enables after BASE64.

    Inputs remain unchanged. The default-off resistors and independent CDONE,
    supply and accessory qualification gates belong to the real 14xxx source;
    these two hierarchy exports do not implement those gates or gateware.
    No original allocation, optional five-pin reuse or BASE64 row is changed.
    """
    receipt=copy.deepcopy(review_receipt or load(SLOW_ENABLE_RECEIPT))
    frozen=load(SLOW_ENABLE_RECEIPT)
    if sha(SLOW_ENABLE_RECEIPT)!=REVIEWED_SLOW_ENABLE_SHA256 or receipt!=frozen:
        raise ValueError('Slow-enable review differs from the exact frozen primary receipt')
    if (base_metadata.get('assigned_user_pins'),base_metadata.get('free_user_gpio'),
        base_metadata.get('promoted_nc_pin_count'),base_metadata.get('optional_five_reuse_applied'))!=(161,22,64,False):
        raise ValueError('Slow enables require the unreused BASE161/64 source')
    if base_metadata.get('vendor_fit') or base_metadata.get('manufacturing_ready'):
        raise ValueError('Unproved readiness boundary must remain false')
    root=copy.deepcopy(root_tree);core=copy.deepcopy(core_tree);metadata=copy.deepcopy(base_metadata)
    coordinates=actual_pin_coordinates(core);official=primary_pins();sheet=fpga_sheet(root)
    parent_labels={}
    for p in children(sheet,'pin'):
        xy=point(child(p,'at'))
        wires=[w for w in children(root,'wire') if xy in [point(v) for v in children(child(w,'pts'),'xy')]]
        if len(wires)!=1:raise ValueError('Expected one current FPGA root stub')
        other=next(point(v) for v in children(child(wires[0],'pts'),'xy') if point(v)!=xy)
        labels=[l for l in children(root,'label') if point(child(l,'at'))==other]
        if len(labels)!=1:raise ValueError('Expected one current FPGA root endpoint label')
        parent_labels[value(p[1])]=value(labels[0][1])
    additions=[]
    rows=receipt['signals']
    if len(rows)!=2:raise ValueError('Exactly two slow-enable rows required')
    for row,(n,b,pn,wr) in zip(rows,SLOW_ENABLE_PINS):
        p=official[b]
        expected=(n,b,pn,'BANK4B',wr,'output',3.3,'3.3_V_LVCMOS',4700)
        actual=tuple(row[k] for k in ('signal','ball','manufacturer_pin','bank','worksheet_row',
                                     'direction','vccio_nominal_v','io_standard','external_low_default_ohm'))
        if actual!=expected or (p['name'],p['bank'],p['row'])!=(pn,'BANK4B',wr):
            raise ValueError('Slow-enable row differs from the exact official workbook '+b)
        if n in parent_labels or any(r['pin']==b for r in metadata['exact_pin_rename_ledger']):
            raise ValueError('Slow-enable pin/function is already allocated '+b)
        info=coordinates[b];xy=info['coordinate']
        nc=[c for c in children(core,'no_connect') if point(child(c,'at'))==xy]
        if len(nc)!=1:raise ValueError('Expected one actual free NC cross at '+b)
        if any(point(child(l,'at'))==xy for l in children(core,'label')+children(core,'hierarchical_label')):
            raise ValueError('Slow-enable free pin is already labelled '+b)
        old='unconnected-(U1001-'+pn+'-Pad'+b+')'
        new='/fpga_core/'+n
        if (row['old_native_net'],row['new_native_net'])!=(old,new):
            raise ValueError('Slow-enable exact native rename mismatch '+b)
        core.remove(nc[0]);ex=round(xy[0]+(-101.6 if info['side']=='left' else 10.16),4)
        core.extend([['wire',['pts',['xy',str(xy[0]),str(xy[1])],['xy',str(ex),str(xy[1])]],
            ['stroke',['width','0'],['type','default']],['uuid',q(uid('U1001/'+b+'/slow-wire'))]],
            hierarchy_item(n,(ex,xy[1]),'output','U1001/'+b+'/slow-port')])
        parent_labels[n]='fpga_core/'+n
        additions.append(dict(reference='U1001',pin=b,manufacturer_pin=pn,bank='BANK4B',
            direction='output',signal=n,old_native_net=old,new_native_net=new,
            removed_nc_uuid=value(child(nc[0],'uuid')[1]),coordinate=list(xy),
            scope='exact two former NC slow-enable FPGA pins only',native_export_verified=False,
            external_low_default_ohm=4700,independent_default_off_gate_required=True))
    directions=dict(metadata['desired_directions']);directions.update({n:'output' for n,_,_,_ in SLOW_ENABLE_PINS})
    geometry=rebuild_root_geometry(root,{'fpga_core':parent_labels,'_directions':directions})
    core.append(['text',q('BOUNDED TWO SLOW ENABLES: M4 FAST_PORTS_ENABLE / M6 XF_POWER_ENABLE.\n3.3V LVCMOS LVDS-resource GPIO; actual 4.7k LOW defaults and independent qualification in operator region.\n163 user functions, 20 free GPIO; no loaded output, vendor fit or bitstream qualification.'),
        ['at','560','791','0'],['effects',['font',['size','1.2','1.2']],['justify','left','top']],['uuid',q(uid('slow-enable-scope-note'))]])
    metadata.update(revision='motherboard-fpga-base-plus-two-slow-source-r01',
        assigned_user_pins=163,free_user_gpio=20,promoted_nc_pin_count=66,
        exact_pin_rename_ledger=metadata['exact_pin_rename_ledger']+additions,
        slow_enable_pin_rename_ledger=additions,root_sheet_port_map=parent_labels,
        desired_directions=directions,new_fpga_hierarchy_ports=len(parent_labels),
        root_geometry_changes=geometry,slow_enable_primary_receipt_sha256=REVIEWED_SLOW_ENABLE_SHA256,
        slow_enable_gateware_implemented=False,slow_enable_physical_validation=False)
    return root,core,metadata

def audit_obsolete_home_copper(board_path):
    """Prove the exact obsolete HOME nets have no routed/fill copper.

    The retained FPGA pad geometry remains. J1007 is a legacy logical
    boundary with no MPN/footprint, not a purchased header on this board.
    Both current KiCad10 named-net and earlier numeric-net syntax work.
    """
    board_path=Path(board_path);tree=parse(board_path.read_text(encoding='utf8'))
    names={str(n[1]):value(n[2]) for n in children(tree,'net')}
    def net(n):
        p=child(n,'net')
        return None if p is None else names.get(str(p[1]),value(p[1]))
    pads={};refs=set()
    for f in children(tree,'footprint'):
        props=[p for p in children(f,'property') if value(p[1])=='Reference']
        if len(props)!=1:raise ValueError('HOME copper audit requires exact native footprint references')
        ref=value(props[0][2]);refs.add(ref)
        for p in children(f,'pad'):
            if value(p[1]):pads[(ref,value(p[1]))]=net(p)
    if 'J1007' in refs:raise ValueError('J1007 physical footprint unexpectedly exists; separate mechanical/DNP review required')
    rows=[]
    for signal,ball,pn,bank,row in HOME_DEALLOC_PINS:
        old='/fpga_core/'+signal
        actual=[key for key,name in pads.items() if name==old]
        if actual!=[('U1001',ball)]:raise ValueError('HOME native pad partition differs '+signal)
        counts={kind:sum(net(x)==old for x in children(tree,kind)) for kind in ['segment','via','zone']}
        if any(counts.values()):raise ValueError('HOME deallocation would discard routed copper '+signal)
        rows.append(dict(signal=signal,ball=ball,old_native_net=old,numbered_copper_pads=[dict(reference='U1001',pin=ball)],**counts))
    return dict(schema_version=1,board_path=str(board_path),board_sha256=sha(board_path),
        rows=rows,J1007_physical_footprint_present=False,zero_routed_HOME_copper=True,
        physical_geometry_changed=False,manufacturing_ready=False)


def audit_reserved_health_copper(board_path):
    """Exact ten formerly single-pad FPGA nets; discard no routed copper."""
    board_path=Path(board_path);tree=parse(board_path.read_text(encoding='utf8'))
    names={str(n[1]):value(n[2]) for n in children(tree,'net')}
    def net(n):
        p=child(n,'net');return None if p is None else names.get(str(p[1]),value(p[1]))
    pads={}
    for f in children(tree,'footprint'):
        props=[p for p in children(f,'property') if value(p[1])=='Reference']
        if len(props)!=1:raise ValueError('Reserved-health audit needs exact footprint references')
        ref=value(props[0][2])
        for p in children(f,'pad'):
            if value(p[1]):pads[(ref,value(p[1]))]=net(p)
    rows=[]
    for signal,ball,pn,bank,row,reason in RESERVED_HEALTH_PINS:
        old='/fpga_core/'+signal
        actual=[key for key,name in pads.items() if name==old]
        if actual!=[('U1001',ball)]:raise ValueError('Reserved-health pad partition differs '+signal)
        counts={kind:sum(net(x)==old for x in children(tree,kind)) for kind in ['segment','via','zone']}
        if any(counts.values()):raise ValueError('Reserved-health change would discard copper '+signal)
        rows.append(dict(signal=signal,ball=ball,old_native_net=old,reason=reason,
            numbered_copper_pads=[dict(reference='U1001',pin=ball)],**counts))
    return dict(schema_version=1,board_path=str(board_path),board_sha256=sha(board_path),rows=rows,
        zero_routed_copper=True,physical_geometry_changed=False,manufacturing_ready=False)


def apply_reserved_health_reconciliation(root_tree,core_tree,allocation_metadata,native_before,copper_evidence):
    """Nine reviewed unused balls NC; P4 observes a real buffered rail node.

    Three removed rack acquisition pins do not replace real onboard health.
    Six XS pins remain named future reservations, with no current interface.
    The original MC and every unrelated pin/net/part remain read-only.
    """
    if sha(HOME_SPEC)!=HOME_SPEC_SHA256:raise ValueError('Reserved-health frozen specification changed')
    if not allocation_metadata.get('home_deallocation_applied') or (allocation_metadata.get('assigned_user_pins'),allocation_metadata.get('free_user_gpio'))!=(151,32):
        raise ValueError('Reserved-health reconciliation requires reviewed HOME-deallocated151/32 source')
    if allocation_metadata.get('reserved_health_reconciliation_applied') or allocation_metadata.get('vendor_fit') or allocation_metadata.get('manufacturing_ready'):
        raise ValueError('Reserved-health already applied or unproved readiness claimed')
    evidence=copy.deepcopy(copper_evidence);board=Path(evidence.get('board_path',''))
    if not board.is_file() or sha(board)!=evidence.get('board_sha256') or evidence!=audit_reserved_health_copper(board):
        raise ValueError('Reserved-health copper evidence stale, incomplete or modified')
    root=copy.deepcopy(root_tree);core=copy.deepcopy(core_tree);metadata=copy.deepcopy(allocation_metadata)
    official=primary_pins();coordinates=actual_pin_coordinates(core);sheet=fpga_sheet(root)
    native={n.attrib['name']:{(p.attrib['ref'],p.attrib['pin']) for p in n.findall('node')} for n in native_before.findall('./nets/net')}
    if ('U2006','4') not in native.get('/FPGA_CRESET_N',set()) or ('U2006','2') not in native.get('/mc_local_power/MC_RAILS_OK_5V',set()):
        raise ValueError('Required rail bridge lacks actual U2006 buffered3.3V rail source')
    comps={c.attrib['ref']:c for c in native_before.findall('./components/comp')}
    c=comps.get('U2006');lib=None if c is None else c.find('libsource')
    if c is None or c.findtext("./fields/field[@name='MPN']",'')!='SN74LVC1G17DBVR':
        raise ValueError('Required rail bridge U2006 actual part differs')
    part=next((p for p in native_before.findall('./libparts/libpart') if p.attrib['lib']==lib.attrib['lib'] and p.attrib['part']==lib.attrib['part']),None)
    kinds={} if part is None else {p.attrib['num']:p.attrib['type'] for p in part.findall('./pins/pin')}
    if kinds.get('4')!='output' or kinds.get('2')!='input' or ('U2006','5') not in native.get('/IO_3V3',set()):
        raise ValueError('Rail bridge is not a qualified3.3V input-to-output source')
    ledger=[];removed=[];reserved=[]
    for signal,ball,pn,bank,row,reason in RESERVED_HEALTH_PINS:
        if (official[ball]['name'],official[ball]['bank'],official[ball]['row'])!=(pn,bank,row):raise ValueError('Reserved-health official ball identity changed '+ball)
        old='/fpga_core/'+signal
        if native.get(old)!={('U1001',ball)}:raise ValueError('Reserved-health native endpoint is not exactly one FPGA pad '+signal)
        xy=coordinates[ball]['coordinate']
        wires=[w for w in children(core,'wire') if xy in [point(p) for p in children(child(w,'pts'),'xy')]]
        if len(wires)!=1:raise ValueError('Reserved-health core endpoint not one source stub '+signal)
        w=wires[0];pts=[point(p) for p in children(child(w,'pts'),'xy')];end=next(p for p in pts if p!=xy)
        labels=[l for l in children(core,'hierarchical_label') if value(l[1])==signal and point(child(l,'at'))==end]
        pins=[p for p in children(sheet,'pin') if value(p[1])==signal]
        if len(labels)!=1 or len(pins)!=1 or any(value(l[1])==signal for l in children(core,'label')+children(core,'global_label')):
            raise ValueError('Reserved-health source ports are not exact bounded stubs '+signal)
        direction='input' if signal in {'HEALTH_SR_DATA','XS_MISO','RAILS_OK_FPGA'} else 'output'
        if metadata.get('desired_directions',{}).get(signal)!=direction or value(child(labels[0],'shape')[1])!=direction or pins[0][2]!=direction:
            raise ValueError('Reserved-health planned/native port direction changed '+signal)
        if any(point(child(j,'at')) in pts for j in children(core,'junction')) or any(end in [point(p) for p in children(child(v,'pts'),'xy')] for v in children(core,'wire') if v is not w):
            raise ValueError('Reserved-health core stub is branched '+signal)
        pin=pins[0];rxy=point(child(pin,'at'));rw=[v for v in children(root,'wire') if rxy in [point(p) for p in children(child(v,'pts'),'xy')]]
        if len(rw)!=1:raise ValueError('Reserved-health root endpoint not one source stub '+signal)
        rpt=[point(p) for p in children(child(rw[0],'pts'),'xy')];rend=next(p for p in rpt if p!=rxy)
        rl=[l for l in children(root,'label') if point(child(l,'at'))==rend]
        if len(rl)!=1 or value(rl[0][1])!='fpga_core/'+signal or any(point(child(j,'at')) in rpt for j in children(root,'junction')):
            raise ValueError('Reserved-health root label/branch changed '+signal)
        if any(rend in [point(p) for p in children(child(v,'pts'),'xy')] for v in children(root,'wire') if v is not rw[0]):
            raise ValueError('Reserved-health root stub is branched '+signal)
        if reason=='required_existing_qualified_rail_bridge':
            rl[0][1]=q('FPGA_CRESET_N');new='/FPGA_CRESET_N'
            metadata['root_sheet_port_map'][signal]='FPGA_CRESET_N'
        else:
            if any(point(child(n,'at'))==xy for n in children(core,'no_connect')):raise ValueError('Reserved-health pin already NC '+signal)
            for tree,item in [(core,w),(core,labels[0]),(root,rw[0]),(root,rl[0]),(sheet,pin)]:
                removed.append(dict(type=item[0],uuid=value(child(item,'uuid')[1])));tree.remove(item)
            ncuid=uid('reserved-health/'+ball+'/NC')
            core.append(['no_connect',['at',str(xy[0]),str(xy[1])],['uuid',q(ncuid)]])
            new='unconnected-(U1001-'+pn+'-Pad'+ball+')'
            metadata['root_sheet_port_map'].pop(signal);metadata['desired_directions'].pop(signal,None)
            if reason=='future_reserved_no_base_interface':reserved.append(dict(signal=signal,ball=ball,bank=bank,physical_state='NC',interface_implemented=False))
        ledger.append(dict(reference='U1001',pin=ball,signal=signal,manufacturer_pin=pn,bank=bank,
            worksheet_row=row,old_native_net=old,new_native_net=new,reason=reason,
            scope='exact reviewed single-pad signal only; no wildcard',zero_copper_verified=True,native_export_verified=False))
    core.append(['text',q('IS2 CURRENT reconciliation:142 assigned /41 free user-function GPIO resources.\nHEALTH_SR rack acquisition removed; real onboard direct/IOL1 health is preserved.\nSix named XS future resources are NC, not a base expansion interface. P4 RAILS_OK reads actual buffered FPGA_CRESET_N.\nNo health constant, vendor fit, target bitstream or physical qualification is claimed.'),
        ['at','560','835','0'],['effects',['font',['size','1.2','1.2']],['justify','left','top']],['uuid',q(uid('reserved-health-reconciliation-note'))]])
    metadata.update(revision='motherboard-fpga-reserved-health-reconciliation-r01',
        assigned_user_pins=142,free_user_gpio=41,deallocated_user_pin_count=21,
        reserved_health_reconciliation_applied=True,reserved_health_pin_rename_ledger=ledger,
        exact_pin_rename_ledger=metadata['exact_pin_rename_ledger']+ledger,
        reserved_health_removed_source_stubs=removed,XS_future_resource_reservations=reserved,
        RAILS_OK_FPGA_actual_source='/FPGA_CRESET_N',RAILS_OK_FPGA_source_pin='U2006.4',
        reserved_health_copper_evidence=evidence,new_fpga_hierarchy_ports=len(metadata['root_sheet_port_map']),
        original_MC_source_changed=False,physical_component_inventory_changed=False,
        target_health_runtime_verified=False,XS_interface_implemented=False)
    metadata['parent_endpoint_obligations']=[r for r in metadata.get('parent_endpoint_obligations',[]) if r.get('signal') not in {p[0] for p in RESERVED_HEALTH_PINS[:9]}]
    for r in metadata.get('parent_endpoint_obligations',[]):
        if r.get('signal')=='RAILS_OK_FPGA':r.update(target_sheet='mc_local_power',target_nets=['FPGA_CRESET_N'],
            polarity='actual U2006 Schmitt3.3V rail readback; not an identity or OS-ready signal',implemented_connection=True)
    return root,core,metadata


def verify_reserved_health_native(before_path,after_path,metadata):
    """Independently bounded whole-native parity check for nineNC/onebridge."""
    before=ET.parse(before_path);after=ET.parse(after_path);errors=[]
    def nodes(tree):
        result={}
        for net in tree.findall('./nets/net'):
            for node in net.findall('node'):
                key=(node.attrib['ref'],node.attrib['pin'])
                if key in result:errors.append('Duplicate native endpoint '+str(key))
                result[key]=net.attrib['name']
        return result
    old,new=nodes(before),nodes(after)
    expected={('U1001',ball):('/fpga_core/'+signal,
        '/FPGA_CRESET_N' if reason=='required_existing_qualified_rail_bridge' else 'unconnected-(U1001-'+pn+'-Pad'+ball+')')
        for signal,ball,pn,bank,row,reason in RESERVED_HEALTH_PINS}
    if set(old)!=set(new):errors.append('Reserved-health changed complete native endpoint set')
    ledger=metadata.get('reserved_health_pin_rename_ledger',[])
    if len(ledger)!=10 or len({(r['reference'],r['pin']) for r in ledger})!=10:errors.append('Reserved-health exact10 ledger missing/duplicated')
    for r in ledger:
        if expected.get((r['reference'],r['pin']))!=(r['old_native_net'],r['new_native_net']):errors.append('Reserved-health ledger outside exact bounded set')
    for key,name in old.items():
        want=expected[key][1] if key in expected else name
        if new.get(key)!=want:errors.append('Reserved-health unexpected native pin/net change '+str(key))
    def identities(tree):
        return {c.attrib['ref']:(c.findtext('value'),c.findtext('footprint',''),c.findtext("./fields/field[@name='MPN']",'')) for c in tree.findall('./components/comp')}
    if identities(before)!=identities(after):errors.append('Reserved-health changed native component identity/inventory')
    if (metadata.get('assigned_user_pins'),metadata.get('free_user_gpio'),metadata.get('promoted_nc_pin_count'),metadata.get('deallocated_user_pin_count'))!=(142,41,66,21):errors.append('Reserved-health canonical resource counts differ')
    if len(metadata.get('XS_future_resource_reservations',[]))!=6 or metadata.get('XS_interface_implemented') or metadata.get('target_health_runtime_verified') or metadata.get('vendor_fit') or metadata.get('manufacturing_ready'):
        errors.append('Reserved-health lost future reservation or claimed unproved implementation/readiness')
    if new.get(('U1001','P4'))!=new.get(('U2006','4')):errors.append('RAILS_OK is not actual Schmitt source')
    return dict(ok=not errors,errors=sorted(set(errors)),native_pins_before=len(old),native_pins_after=len(new),
        exact_physical_pin_changes=10,NC_deallocations=9,real_rail_bridges=1,
        physical_part_set_changed=False,original_MC_source_changed=False,manufacturing_ready=False)


def apply_obsolete_home_deallocation(root_tree,core_tree,allocation_metadata,native_before,copper_evidence):
    """NC exactly twelve obsolete direct HOME balls and their old boundary.

    Home switches belong to the existing validated DI/IOL1 contract. This
    does not remove probes/EXT permission, reuse a free ball, mutate the
    retained MC, or imply that runtime DI/home integration is implemented.
    Every changed physical pin has an exact named-net-to-NC ledger row.
    """
    if sha(HOME_SPEC)!=HOME_SPEC_SHA256:raise ValueError('HOME inheritance source differs from frozen specification')
    spec=load(HOME_SPEC)
    inherited=[r for r in spec['changes_to_codex_drawn_hardware'] if r.get('drawn_value','').startswith('22 dedicated FPGA machine inputs:')]
    if len(inherited)!=1 or 'homes and machine status move to the 24 general DI' not in inherited[0]['is1_value']:
        raise ValueError('Frozen source no longer obsoletes direct HOME inputs')
    if (allocation_metadata.get('assigned_user_pins'),allocation_metadata.get('free_user_gpio'),allocation_metadata.get('promoted_nc_pin_count'))!=(163,20,66):
        raise ValueError('HOME deallocation requires exact BASE64 plus M4/M6 allocation')
    if allocation_metadata.get('home_deallocation_applied') or allocation_metadata.get('vendor_fit') or allocation_metadata.get('manufacturing_ready'):
        raise ValueError('HOME deallocation is already applied or unproved readiness claimed')
    evidence=copy.deepcopy(copper_evidence)
    board=Path(evidence.get('board_path',''))
    if not board.is_file() or sha(board)!=evidence.get('board_sha256') or evidence!=audit_obsolete_home_copper(board):
        raise ValueError('HOME copper evidence is stale, incomplete or modified')
    root=copy.deepcopy(root_tree);core=copy.deepcopy(core_tree);metadata=copy.deepcopy(allocation_metadata)
    official=primary_pins();coordinates=actual_pin_coordinates(core)
    promoted=metadata.get('exact_pin_rename_ledger',[])
    if len(promoted)!=66 or len({r.get('pin') for r in promoted})!=66:raise ValueError('HOME prerequisite is not the exact66 promoted source pins')
    for r in promoted:
        info=coordinates.get(r.get('pin'))
        if r.get('reference')!='U1001' or info is None or r.get('manufacturer_pin')!=info['manufacturer_name'] or r.get('bank')!=info['bank']:
            raise ValueError('HOME prerequisite promoted ball identity mismatch')
        xy=info['coordinate'];wires=[w for w in children(core,'wire') if xy in [point(p) for p in children(child(w,'pts'),'xy')]]
        if len(wires)!=1:raise ValueError('HOME prerequisite promoted pin has no exact source wire '+r['pin'])
        end=next(point(p) for p in children(child(wires[0],'pts'),'xy') if point(p)!=xy)
        ports=[p for p in children(core,'hierarchical_label') if point(child(p,'at'))==end and value(p[1])==r['signal']]
        if len(ports)!=1:raise ValueError('HOME prerequisite promoted source function mismatch '+r['pin'])
    if any(value(p[1]).startswith('HOME') for p in children(fpga_sheet(root),'pin')):
        raise ValueError('Unexpected HOME root hierarchy export requires separate reconciliation')
    headers=[s for s in children(core,'symbol') if value(ref_property(s)[2])=='J1007']
    if len(headers)!=1:raise ValueError('Exactly one retained J1007 logical boundary required')
    header=headers[0];lib=value(child(header,'lib_id')[1]);definition=next(s for s in children(child(core,'lib_symbols'),'symbol') if value(s[1])==lib)
    for key in ['MPN','Footprint']:
        prop=[p for p in children(header,'property') if value(p[1])==key]
        if prop and value(prop[0][2]):raise ValueError('J1007 is physical; unreviewed component removal is prohibited')
    ha=child(header,'at')
    if len(ha)>3 and float(ha[3])!=0:raise ValueError('Rotated J1007 requires explicit review')
    hcoords={value(child(p,'number')[1]):(round(float(ha[1])+point(child(p,'at'))[0],4),round(float(ha[2])-point(child(p,'at'))[1],4)) for sub in children(definition,'symbol') for p in children(sub,'pin')}
    if set(hcoords)!={str(i) for i in range(1,13)}:raise ValueError('J1007 must be the exact twelve-pin HOME-only boundary')
    components={c.attrib['ref']:c for c in native_before.findall('./components/comp')}
    native_header=components.get('J1007')
    if native_header is None or native_header.findtext('footprint','') or native_header.findtext("./fields/field[@name='MPN']",''):
        raise ValueError('Native J1007 physical exclusion is not proved')
    native={}
    for n in native_before.findall('./nets/net'):
        native[n.attrib['name']]={(p.attrib['ref'],p.attrib['pin']) for p in n.findall('node')}
    ledger=[];boundary_ledger=[];removed=[]
    for index,(signal,ball,pn,bank,row) in enumerate(HOME_DEALLOC_PINS,1):
        if (official[ball]['name'],official[ball]['bank'],official[ball]['row'])!=(pn,bank,row):raise ValueError('HOME official ball/bank mismatch '+ball)
        old='/fpga_core/'+signal
        if native.get(old)!={('U1001',ball),('J1007',str(index))}:raise ValueError('HOME native source partition is not exactly the two obsolete endpoints '+signal)
        labels=[l for l in children(core,'label') if value(l[1])==signal]
        if len(labels)!=2 or any(value(l[1])==signal for l in children(core,'hierarchical_label')+children(core,'global_label')):
            raise ValueError('HOME labels/hierarchy are not exact simple local stubs '+signal)
        for ref,pin,xy,name in [('U1001',ball,coordinates[ball]['coordinate'],pn),('J1007',str(index),hcoords[str(index)],str(index))]:
            if any(point(child(n,'at'))==xy for n in children(core,'no_connect')):raise ValueError('HOME pin already NC '+ref+'.'+pin)
            wires=[w for w in children(core,'wire') if xy in [point(p) for p in children(child(w,'pts'),'xy')]]
            if len(wires)!=1:raise ValueError('HOME endpoint is not one bounded wire '+ref+'.'+pin)
            wire=wires[0];pts=[point(p) for p in children(child(wire,'pts'),'xy')];end=next(p for p in pts if p!=xy)
            endpoint=[l for l in labels if point(child(l,'at'))==end]
            if len(endpoint)!=1 or any(point(child(j,'at')) in pts for j in children(core,'junction')):
                raise ValueError('HOME endpoint is branched/unreviewed '+ref+'.'+pin)
            shared=[w for w in children(core,'wire') if w is not wire and end in [point(p) for p in children(child(w,'pts'),'xy')]]
            if shared:raise ValueError('HOME endpoint joins another wire '+ref+'.'+pin)
            removed.extend([dict(type='wire',uuid=value(child(wire,'uuid')[1])),dict(type='label',uuid=value(child(endpoint[0],'uuid')[1]))])
            core.remove(wire);core.remove(endpoint[0]);ncuid=uid('home-obsolete/'+ref+'/'+pin+'/NC')
            core.append(['no_connect',['at',str(xy[0]),str(xy[1])],['uuid',q(ncuid)]])
            new_nc='unconnected-('+ref+'-'+name+'-Pad'+pin+')' if ref=='U1001' else 'unconnected-(J1007-Pad'+pin+')'
            item=dict(reference=ref,pin=pin,signal=signal,old_native_net=old,new_native_net=new_nc,
                coordinate=list(xy),created_nc_uuid=ncuid,scope='exact obsolete dedicated HOME endpoint only; no wildcard',native_export_verified=False)
            if ref=='U1001':
                item.update(manufacturer_pin=pn,bank=bank,worksheet_row=row,direction='unused_NC',function_replaced_by='DI24/IOL1 configured home input',zero_copper_verified=True)
                ledger.append(item)
            else:boundary_ledger.append(item)
    for flag in ['in_bom','on_board']:child(header,flag)[1]='no'
    child(header,'dnp')[1]='yes'
    next(p for p in children(header,'property') if value(p[1])=='Value')[2]=q('OBSOLETE HOME boundary / NC test-only / NO PHYSICAL HEADER')
    core.append(['text',q('OBSOLETE direct HOME0-11: twelve exact FPGA balls and the legacy nonphysical J1007 boundary are NC/test-only.\nHomes use the existing DI24/IOL1 electrical/logical contract; no new home connector, runtime function or ball reuse is claimed.\nG12 PROBE / G15 TOOLSETTER / G16 protective EXT status remain unchanged. 151 user functions;32 ordinary freeGPIO after this reviewed delta.'),
        ['at','560','815','0'],['effects',['font',['size','1.2','1.2']],['justify','left','top']],['uuid',q(uid('home-deallocation-note'))]])
    metadata.update(revision='motherboard-fpga-base64-slow2-home-deallocation-r01',assigned_user_pins=151,free_user_gpio=32,
        home_deallocation_applied=True,deallocated_user_pin_count=12,
        exact_pin_rename_ledger=metadata['exact_pin_rename_ledger']+ledger,
        home_deallocation_pin_rename_ledger=ledger,home_boundary_nc_ledger=boundary_ledger,
        home_removed_source_stubs=removed,home_source_sha256=HOME_SPEC_SHA256,
        home_copper_evidence=evidence,home_runtime_DI_integration_verified=False,
        J1007_physical_header_exists=False,J1007_nonphysical_boundary_excluded=True,
        physical_component_inventory_changed=False,original_MC_source_changed=False)
    for signal,ball,pn,bank,row in HOME_DEALLOC_PINS:metadata['desired_directions'].pop(signal,None)
    return root,core,metadata


def verify_obsolete_home_native(before_path,after_path,metadata):
    """Uncapped whole-native pin/identity check for the exact HOME delta."""
    before=ET.parse(before_path);after=ET.parse(after_path);errors=[]
    def nodes(tree):
        result={}
        for net in tree.findall('./nets/net'):
            for n in net.findall('node'):
                key=(n.attrib['ref'],n.attrib['pin'])
                if key in result:errors.append('Duplicate native endpoint '+str(key))
                result[key]=net.attrib['name']
        return result
    old=nodes(before);new=nodes(after)
    if set(old)!=set(new):errors.append('HOME delta changed complete native pin inventory')
    led=metadata.get('home_deallocation_pin_rename_ledger',[])+metadata.get('home_boundary_nc_ledger',[])
    if len(led)!=24 or len({(r['reference'],r['pin']) for r in led})!=24:errors.append('HOME exact24 endpoint ledger missing or duplicated')
    expected={('U1001',b):('/fpga_core/'+s,'unconnected-(U1001-'+pn+'-Pad'+b+')') for s,b,pn,bank,row in HOME_DEALLOC_PINS}
    expected.update({('J1007',str(i)):('/fpga_core/'+s,'unconnected-(J1007-Pad'+str(i)+')') for i,(s,b,pn,bank,row) in enumerate(HOME_DEALLOC_PINS,1)})
    for r in led:
        key=(r['reference'],r['pin']);pair=(r['old_native_net'],r['new_native_net'])
        if expected.get(key)!=pair:errors.append('HOME ledger not the independently bounded endpoint '+str(key))
    for key,net in old.items():
        want=expected[key][1] if key in expected else net
        if new.get(key)!=want:errors.append('HOME unexpected native pin/net change '+str(key))
    for signal,ball,pn,bank,row in HOME_DEALLOC_PINS:
        if any(n.attrib['name']=='/fpga_core/'+signal for n in after.findall('./nets/net')):errors.append('Obsolete HOME native net survives '+signal)
    def identities(tree):
        return {c.attrib['ref']:(c.findtext('value'),c.findtext('footprint',''),c.findtext("./fields/field[@name='MPN']",'')) for c in tree.findall('./components/comp')}
    bi=identities(before);ai=identities(after)
    if set(bi)!=set(ai):errors.append('HOME changed complete native component set')
    for ref,v in bi.items():
        if ref=='J1007':
            if v[1:]!=('','') or ai.get(ref)!=('OBSOLETE HOME boundary / NC test-only / NO PHYSICAL HEADER','',''):errors.append('J1007 logical exclusion/identity mismatch')
        elif ai.get(ref)!=v:errors.append('HOME changed unrelated native MPN/value/footprint '+ref)
    h=next((c for c in after.findall('./components/comp') if c.attrib['ref']=='J1007'),None)
    if h is None or not {'exclude_from_bom','exclude_from_board','dnp'}<={p.attrib['name'] for p in h.findall('property')}:errors.append('J1007 obsolete nonphysical boundary not explicitly excluded')
    if (metadata.get('assigned_user_pins'),metadata.get('free_user_gpio'),metadata.get('promoted_nc_pin_count'),metadata.get('deallocated_user_pin_count'))!=(151,32,66,12):errors.append('HOME canonical allocation count mismatch')
    if metadata.get('vendor_fit') or metadata.get('manufacturing_ready') or metadata.get('home_runtime_DI_integration_verified'):errors.append('HOME unproved vendor/readiness/runtime claim')
    aliases={b:old.get(('U1001',b)) for b in ['G12','G15','G16']}
    if any(new.get(('U1001',b))!=name for b,name in aliases.items()):errors.append('HOME removal disturbed preserved probe/EXT aliases')
    return dict(ok=not errors,errors=sorted(set(errors)),native_pins_before=len(old),native_pins_after=len(new),
        native_components_before=len(bi),native_components_after=len(ai),changed_physical_fpga_pins=12,
        changed_nonphysical_boundary_pins=12,all_other_native_pins_preserved=not errors,
        G12_G15_G16_native_functions_preserved=True,manufacturing_ready=False,vendor_fit=False)


def endpoint_obligations():
    return [
      dict(signal='FPGA_PROGRESS_O',target_sheet='watchdog_conditioning',target_nets=['FPGA_PROGRESS_O'],polarity='toggle on accepted useful output progress',implemented_connection=False),
      dict(signal='OPI_REARM_M',target_sheet='mc_permission',target_nets=['OPI_REARM_TX','OPI_REARM_BOE'],polarity='rising deliberate ARM-only strobe; real A/B OPI latches still required',implemented_connection=False),
      dict(signal='OPI_REARM_O',target_sheet='mc_permission',target_nets=['OPI_REARM_OUT'],polarity='rising deliberate IO_ENABLE-only strobe',implemented_connection=False),
      dict(signal='WATCHDOG_TRIP_M',target_sheet='mc_permission',target_nets=['WD_M_TRIP_N'],polarity='actual retained output ACTIVE LOW; full RTL must invert into active-high logical trip status',implemented_connection=False),
      dict(signal='WATCHDOG_TRIP_O',target_sheet='mc_permission',target_nets=['WD_O_TRIP_N'],polarity='actual retained output ACTIVE LOW; full RTL must invert into active-high logical trip status',implemented_connection=False),
      dict(signal='WATCHDOG_TRIP_CLEAR',target_sheet='mc_permission',target_nets=['WD_REARM_M','WD_REARM_O'],polarity='ACTIVE HIGH into U4018 inputs with default LOW; U4019 drives WD_M/O_TRIP_CLEAR_N and must never be driven by FPGA; deliberate disarmed common-clear policy remains to implement',implemented_connection=False),
      dict(signal='RAILS_OK_FPGA',target_sheet='root_existing',target_nets=['FPGA_CRESET_N'],polarity='actual qualified rail-reset readback; verify timing semantics before root connects',implemented_connection=False),
      dict(signal='OPI_OK_TX',target_sheet='mc_permission',target_nets=['OPI_OK_TX'],polarity='high means intact since deliberate ARM',implemented_connection=False),
      dict(signal='OPI_OK_BOE',target_sheet='mc_permission',target_nets=['OPI_OK_BOE'],polarity='high means actual bank-B buffer-OE path intact',implemented_connection=False),
      dict(signal='OPI_OK_OUT',target_sheet='mc_permission',target_nets=['OPI_OK_OUT'],polarity='high means intact since deliberate IO_ENABLE',implemented_connection=False),
      dict(signal='PERMIT_OUT_REQ',target_sheet='mc_permission',target_nets=['PERMIT_OUT_REQ'],polarity='high deliberate machine contact permission request; forced low during selftest',implemented_connection=False),
      dict(signal='OUT_PERMIT',target_sheet='mc_permission',target_nets=['OUT_PERMIT'],polarity='actual hardware permission high',implemented_connection=False),
      dict(signal='PROC_PERMIT',target_sheet='mc_permission',target_nets=['PROC_PERMIT'],polarity='actual hardware permission high',implemented_connection=False),
      dict(signal='TAMPER_CLEAR_N',target_sheet='mc_permission',target_nets=['TAMPER_CLEAR_N'],polarity='actual measured/latching clear qualification high; detector sources still open',implemented_connection=False),
      *[dict(signal=n,target_sheet='motherboard_fast_inputs',target_nets=[n],polarity='3.3 V digital receiver output; exact native receiver endpoint exists',implemented_connection=False)
          for n in ('FREQ0_FPGA','FREQ1_FPGA','MPG_A_FPGA','MPG_B_FPGA')],
      *[dict(signal=n,target_sheet='missing_health_or_IO_circuit',target_nets=[],polarity='not a healthy constant; circuit and authentic diagnostics required',implemented_connection=False)
          for n in ('MOTION_A_PGOOD','MOTION_B_PGOOD','OPI_OK_A','OPI_OK_B','HEALTH_SR_CLK','HEALTH_SR_LOAD_N','HEALTH_SR_DATA')]
    ]

def reconcile_current_allocation_annotations(core_tree,allocation_metadata):
    """Label prior transactions historical and publish current135/48 facts.

    This final parent-stage operation changes text and metadata only. It never
    changes any package pin, port, wire, label, UUID, or transaction ledger.
    """
    expected=(135,48,66,28)
    actual=tuple(allocation_metadata.get(k) for k in
        ('assigned_user_pins','free_user_gpio','promoted_nc_pin_count','deallocated_user_pin_count'))
    if actual!=expected:raise ValueError('Current allocation must be exact reviewed135/48 with66 promotions and28 deallocations')
    if allocation_metadata.get('current_annotations_reconciled'):
        raise ValueError('Current allocation annotations already reconciled')
    core=copy.deepcopy(core_tree);metadata=copy.deepcopy(allocation_metadata)
    prefixes=('BASE FPGA ALLOCATION /','BOUNDED TWO SLOW ENABLES:',
              'OBSOLETE direct HOME0-11:','IS2 CURRENT reconciliation:')
    found=[]
    for prefix in prefixes:
        matches=[t for t in children(core,'text') if value(t[1]).startswith(prefix)]
        if len(matches)!=1:raise ValueError('Exact historical FPGA annotation missing or duplicated '+prefix)
        text=matches[0];before=value(text[1])
        text[1]=q('HISTORICAL TRANSACTION — '+before)
        found.append(dict(prefix=prefix,before=before,after=value(text[1])))
    core.append(['text',q('CURRENT IS2 FPGA ALLOCATION:135 assigned /48 free user-function resources, including the retained clock.\n'
        '183 manufacturer user-function resources; all256 package balls and14 VCCIO contacts retain their exact reviewed pin/bank mapping.\n'
        'The prior66 NC promotions,12 HOME deallocations,nine reserved-health NC reversals,P4 real rail bridge andseven obsolete status NCs remain separate historical transactions.\n'
        'This is native electrical resource reconciliation. Vendor package fit,timing,loaded output and physical qualification remain unproved.'),
        ['at','148','194'],['effects',['font',['size','1.1','1.1']],['justify','left']],
        ['uuid',q(str(uuid.uuid5(NS,'current-IS2-allocation-135-48-text')))]])
    metadata.update(revision='motherboard-fpga-current-source135-48-r01',
        source_scope='Current parent source after exact historical66 promotions and bounded28 user-function deallocations; no vendor fit or physical qualification.',
        current_annotations_reconciled=True,current_user_function_resources=183,
        current_annotation_changes=found,
        historical_resource_counts=[dict(transaction='base64',assigned=161,free=22),
            dict(transaction='slow2',assigned=163,free=20),dict(transaction='HOME12 NC',assigned=151,free=32),
            dict(transaction='reserved-health9 NC plus real P4 bridge',assigned=142,free=41)],
        current_resource_counts=dict(assigned=135,free=48))
    return core,metadata


def native_nodes(path):
    nodes={}
    for net in ET.parse(path).findall('.//nets/net'):
        for n in net.findall('node'):
            key=(n.attrib['ref'],n.attrib['pin'])
            if key in nodes:raise ValueError('Duplicate native node '+str(key))
            nodes[key]=net.attrib['name']
    return nodes


def erc_summary(path):
    report=load(path);violations=[v for s in report.get('sheets',[]) for v in s.get('violations',[])]
    types={};severities={}
    for v in violations:
        types[v['type']]=types.get(v['type'],0)+1
        severities[v['severity']]=severities.get(v['severity'],0)+1
    return dict(violations=len(violations),errors=severities.get('error',0),warnings=severities.get('warning',0),
        violation_types=types,ignored_checks=report.get('ignored_checks',[]),report=str(Path(path).resolve().relative_to(ROOT)),
        clean=not violations)

def verify_native(before_path,after_path,metadata):
    before=native_nodes(before_path);after=native_nodes(after_path)
    permitted={(r['reference'],r['pin']):(r['old_native_net'],r['new_native_net']) for r in metadata['exact_pin_rename_ledger']}
    errors=[];changes=[]
    def groups(path):
        result={}
        for net in ET.parse(path).findall('.//nets/net'):
            name=net.attrib['name']
            if name in result:errors.append('Duplicate native net name '+name)
            result.setdefault(name,set()).update((n.attrib['ref'],n.attrib['pin']) for n in net.findall('node'))
        return result
    expected_groups=groups(before_path);actual_groups=groups(after_path)
    for key,(old,new) in permitted.items():
        if key not in expected_groups.get(old,set()):errors.append('Declared old NC not in physical net group '+str(key));continue
        expected_groups[old].remove(key)
        if not expected_groups[old]:del expected_groups[old]
        expected_groups.setdefault(new,set()).add(key)
    if expected_groups!=actual_groups:errors.append('Native physical net groups changed beyond the exact64 NC promotions')
    for key,old in before.items():
        if key not in after:errors.append('Missing native pin '+str(key));continue
        new=after[key]
        if key in permitted:
            expected=permitted[key]
            if (old,new)!=expected:errors.append('Bounded NC rename mismatch '+str(key)+': '+str((old,new)))
            else:changes.append(dict(reference=key[0],pin=key[1],old_native_net=old,new_native_net=new))
        elif old!=new:errors.append('Unapproved native rename '+str(key)+': '+old+' -> '+new)
    if set(after)!=set(before):errors.append('Native node set changed; no component added by pin allocation')
    if len(changes)!=64:errors.append('Expected exactly64 independently verified pin-net changes')
    for r in metadata['exact_pin_rename_ledger']:r['native_export_verified']=not errors
    return dict(ok=not errors,errors=errors,verified_pin_changes=changes,
        source_native_pin_count=len(before),candidate_native_pin_count=len(after),
        untouched_existing_native_pins=len(before)-len(permitted),no_component_or_footprint_additions=True)

def build_isolated_candidate(candidate_name='candidate'):
    if (REPORT/candidate_name).exists():raise ValueError('Existing isolated candidate is frozen; use a new reviewed report revision')
    REPORT.mkdir(parents=True,exist_ok=True);snapshot=REPORT/'inputs/motherboard'
    if not snapshot.exists():shutil.copytree(LIVE,snapshot,ignore=shutil.ignore_patterns('*.kicad_prl'))
    candidate=REPORT/candidate_name;shutil.copytree(snapshot,candidate)
    source_files=[p for p in snapshot.rglob('*') if p.is_file()]
    hashes={p.relative_to(snapshot).as_posix():sha(p) for p in source_files}
    root=parse((candidate/'motherboard.kicad_sch').read_text(encoding='utf8'))
    core=parse((candidate/'fpga_core.kicad_sch').read_text(encoding='utf8'))
    transformed_root,transformed_core,metadata=apply_base_allocation(root,core,
        proposal=load(snapshot/'fpga-allocation-proposal.json'),native_before=ET.parse(snapshot/'netlist.xml'))
    (candidate/'motherboard.kicad_sch').write_text(dump(transformed_root)+'\n',encoding='utf8')
    (candidate/'fpga_core.kicad_sch').write_text(dump(transformed_core)+'\n',encoding='utf8')
    commands=[
        [str(KICAD),'sch','export','netlist','--format','kicadxml','--output',str(candidate/'netlist.xml'),str(candidate/'motherboard.kicad_sch')],
        [str(KICAD),'sch','erc','--format','json','--output',str(candidate/'erc.json'),str(candidate/'motherboard.kicad_sch')],
        [str(KICAD),'sch','export','pdf','--output',str(candidate/'motherboard.pdf'),str(candidate/'motherboard.kicad_sch')]]
    run=[]
    for cmd in commands:
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace')
        run.append(dict(command=cmd,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
        if result.returncode and 'erc' not in cmd:raise ValueError('Native source export failed '+result.stderr)
    metadata['native_verification']=verify_native(snapshot/'netlist.xml',candidate/'netlist.xml',metadata)
    metadata['native_runs']=run
    metadata['native_erc']=erc_summary(candidate/'erc.json')
    if (REPORT/'baseline-erc.json').exists():
        metadata['native_erc_baseline']=erc_summary(REPORT/'baseline-erc.json')
        metadata['native_erc']['warning_delta']=metadata['native_erc']['warnings']-metadata['native_erc_baseline']['warnings']
    metadata['source_inputs_sha256']=hashes
    metadata['revision']='motherboard-fpga-base-source-'+candidate_name
    metadata['candidate_source_directory']=str(candidate.relative_to(ROOT))
    metadata['source_input_stability']=dict(unchanged=all(sha(LIVE/n)==h for n,h in hashes.items()),files=len(hashes))
    write_json(REPORT/'applied-source.json',metadata)
    write_json(LIVE/'fpga-allocation-applied.json',metadata)
    write_json(REPORT/'native-verification.json',metadata['native_verification'])
    if not metadata['native_verification']['ok']:raise ValueError('Unexpected native net changes: '+str(metadata['native_verification']['errors'][:10]))
    print(json.dumps({'candidate':str(candidate),'promoted_nc':64,'ports':metadata['new_fpga_hierarchy_ports'],
        'native_check':metadata['native_verification']['ok'],'erc':metadata['native_erc'],'manufacturing_ready':False},indent=2))
    return metadata

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--candidate-name',default='candidate');args=a.parse_args()
    build_isolated_candidate(args.candidate_name)
