"""Add every actual parent-source footprint to a copy of retained routed copper.

Run with KiCad's bundled Python. This never edits the live parent source,
published viewer, retained PCB or manufacturing files. The large outline and
mechanical reservations are provisional; adding footprints does not route nets.
"""
from __future__ import annotations
import argparse
import copy
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
import pcbnew
from hardware_build_assembly import parse,children,child,value,dump
from hardware_route_logic_return import identity,pad_identity,xy,mm

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/motherboard-pcb-integration-20260930'
KICAD=Path('C:/Program Files/KiCad/10.0')
CLI=KICAD/'bin/kicad-cli.exe'
NS=uuid.UUID('509cc11e-e13c-58d6-a554-bc9719a2ae43')
WIDTH,HEIGHT=460.,340.


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf8'))
def write(path,obj):Path(path).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8')
def uid(name):return str(uuid.uuid5(NS,name))
def copper_pad(p):return bool(p.GetNumber()) and p.IsOnCopperLayer()
def footprint_name(fp):return str(fp.GetFPID().GetLibNickname())+':'+str(fp.GetFPID().GetLibItemName())
def bb(box):return tuple(pcbnew.ToMM(v) for v in (box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()))
def intersects(a,b,gap=0.):return a[0]<b[2]+gap and b[0]<a[2]+gap and a[1]<b[3]+gap and b[1]<a[3]+gap


def native_parts_and_nets(path,physical):
    t=ET.parse(path);parts={c.attrib['ref']:c for c in t.findall('.//components/comp') if c.attrib['ref'] in physical}
    if set(parts)!=set(physical):raise ValueError('Parent physical component inventory differs from native source')
    nodes={}
    for n in t.findall('.//nets/net'):
        for p in n.findall('node'):
            key=(p.attrib['ref'],p.attrib['pin'])
            if key in nodes:raise ValueError('Duplicate native physical node '+str(key))
            if key[0] in physical:nodes[key]=n.attrib['name']
    return parts,nodes


def native_pin_functions(path):
    t=ET.parse(path)
    libs={(p.attrib['lib'],p.attrib['part']):{n.attrib['num']:dict(n.attrib) for n in p.findall('./pins/pin')}
          for p in t.findall('.//libparts/libpart')}
    return {c.attrib['ref']:libs[c.find('libsource').attrib['lib'],c.find('libsource').attrib['part']]
            for c in t.findall('.//components/comp')}


def watchdog_clear_source_check(model,nodes):
    """A passive bridge may drive U4018 inputs, never U4019 driven outputs."""
    errors=[];graph=defaultdict(set)
    for ref,c in model['components'].items():
        resistance=c.get('resistance_ohm')
        if not ref.startswith('R') or resistance is None or not 0<=resistance<=100:continue
        a,b=nodes.get((ref,'1')),nodes.get((ref,'2'))
        if a is not None and b is not None:graph[a].add(b);graph[b].add(a)
    stem=nodes.get(('U1001','D6'));reachable=set();pending=[stem]
    while pending:
        net=pending.pop()
        if net in reachable:continue
        reachable.add(net);pending.extend(graph[net]-reachable)
    required={('U4018','1'),('U4018','3')};forbidden={('U4019','7'),('U4019','3')}
    for key in required:
        if nodes.get(key) not in reachable:errors.append('Watchdog clear command does not reach actual rearm INPUT '+str(key))
    for key in forbidden:
        if nodes.get(key) in reachable:errors.append('Watchdog clear command contends with driven clear OUTPUT '+str(key))
    pull=model['components'].get('R12006',{})
    if (pull.get('resistance_ohm'),nodes.get(('R12006','1')),nodes.get(('R12006','2')))!=(100000,stem,'/LOGIC_GND'):
        errors.append('Active-high watchdog clear stem lacks the exact default-low 100k bias')
    return dict(ok=not errors,errors=errors,required_input_pins=sorted(required),forbidden_driven_output_pins=sorted(forbidden),
                polarity='ACTIVE HIGH, default LOW',physical_copper_path_verified=False)


def raw_items(path,key):
    tree=parse(Path(path).read_text(encoding='utf8'))
    return {value(child(x,'uuid')[1]):dump(x) for x in children(tree,key)}


def pad_template(p):
    return (p.GetNumber(),tuple(p.GetFPRelativePosition()),tuple(p.GetSize()),
            p.GetFPRelativeOrientation().AsDegrees()%360,p.GetLayerSet().FmtBin(),p.GetShape(),p.GetAttribute(),
            tuple(p.GetDrillSize()),p.GetDrillShape(),tuple(p.GetOffset()),
            # KiCad serializes these dimensionless ratios to ten decimals.
            # Compare that exact native precision, not the unsaved binary
            # 0.135135135135... value of the manufacturer-library object.
            round(p.GetRoundRectRadiusRatio(),10),p.GetChamferPositions(),round(p.GetChamferRectRatio(),10))


def native_retained_objects(base,dest,ledger):
    """Compare every retained native footprint field and raw copper/plane item."""
    before=parse(Path(base).read_text(encoding='utf8'));after=parse(Path(dest).read_text(encoding='utf8'))
    allowed={(r['reference'],r['pin']):(r['old_native_net'],r['new_native_net']) for r in ledger}
    changed=[];errors=[]
    originals={value(child(f,'uuid')[1]):f for f in children(before,'footprint')}
    current={value(child(f,'uuid')[1]):f for f in children(after,'footprint')}
    for key,original in originals.items():
        if key not in current:errors.append('Retained full native footprint missing '+key);continue
        wanted=copy.deepcopy(original);observed=current[key]
        ref=value(next(p[2] for p in children(wanted,'property') if value(p[1])=='Reference'))
        current_pads={value(p[1]):p for p in children(observed,'pad')}
        for pad in children(wanted,'pad'):
            number=value(pad[1]);net=child(pad,'net')
            if (ref,number) not in allowed:continue
            actual=current_pads.get(number);new=child(actual,'net') if actual is not None else None
            if net is None or new is None or (value(net[-1]),value(new[-1]))!=allowed[ref,number]:
                errors.append('Bounded full-native pad reconciliation differs '+ref+'.'+number);continue
            pad[pad.index(net)]=copy.deepcopy(new);changed.append(ref+'.'+number)
        if dump(wanted)!=dump(observed):errors.append('Other retained full native footprint data changed '+ref)
    for key in ('segment','via','zone','gr_text'):
        old={value(child(x,'uuid')[1]):dump(x) for x in children(before,key)}
        new={value(child(x,'uuid')[1]):dump(x) for x in children(after,key)}
        if any(new.get(k)!=v for k,v in old.items()):errors.append('Retained raw '+key+' fields changed')
    # Only the four explicit edge-cut endpoints are allowed to expand.
    old_lines={value(child(x,'uuid')[1]):x for x in children(before,'gr_line')}
    new_lines={value(child(x,'uuid')[1]):x for x in children(after,'gr_line')}
    for key,line in old_lines.items():
        wanted=copy.deepcopy(line);observed=new_lines.get(key)
        if value(child(line,'layer')[1])=='Edge.Cuts' and observed is not None:
            for kind in ('start','end'):wanted[wanted.index(child(wanted,kind))]=copy.deepcopy(child(observed,kind))
        if observed is None or dump(wanted)!=dump(observed):errors.append('Retained raw drawing fields changed '+key)
    return dict(ok=not errors,errors=errors,retained_full_native_footprints=len(originals),
                exactly_bounded_pad_net_changes=len(changed),retained_all_copper_plane_and_annotation_fields=True)


def load_exact_footprint(name,source,base):
    library,item=name.split(':',1)
    paths=[source/(library+'.pretty'),base.parent/(library+'.pretty'),KICAD/'share/kicad/footprints'/(library+'.pretty')]
    found=[p/(item+'.kicad_mod') for p in paths if (p/(item+'.kicad_mod')).is_file()]
    if not found:raise FileNotFoundError('Unresolved exact source footprint '+name)
    if len({sha(p) for p in found})>1:raise ValueError('Conflicting exact footprint sources '+name)
    file=found[0];fp=pcbnew.FootprintLoad(str(file.parent),item)
    if fp is None:raise ValueError('Native footprint load failed '+name)
    fp.SetFPID(pcbnew.LIB_ID(library,item))
    return fp,file


def functional_groups(parts,mapping,block_models):
    """Use actual source-channel/driver relations; never unrelated global grids."""
    groups={};targets={}
    def parent(block,ref):return mapping['blocks'][block]['references'].get(ref,ref)
    def assign(block,ref,group):
        ref=parent(block,ref)
        if ref in parts:groups.setdefault(ref,group)
    motor='motherboard_motors'
    if motor in block_models:
        m=block_models[motor]
        for ch in m['channels']:
            g='motor-pair-'+str(ch['motor']//2)
            for k,v in ch.items():
                if k.endswith('_ref') or k in ('led_resistor','enable_pullup'):assign(motor,v,g)
                if k.endswith('_refs'):
                    for ref in v:assign(motor,ref,g)
        for ref,c in m['components'].items():
            channels=[int(n) for net in c.get('pins',{}).values() if net for n in re.findall(r'(?:STEP|DIR|EN|ALM)(\d+)',net)]
            if channels:assign(motor,ref,'motor-pair-'+str(min(channels)//2))
        for ref,c in m['components'].items():
            target=re.search(r'(?:bypass|load-switch input|gated enable supply output) (U\d+)',c.get('role',''))
            if target:
                r,t=parent(motor,ref),parent(motor,target.group(1));targets[r]=t
                if t in groups:groups.setdefault(r,groups[t])
        for ref,c in m['components'].items():
            bank='B' if any(net and ('_B' in net or 'MX4' in net) for net in c.get('pins',{}).values()) else 'A'
            assign(motor,ref,'motor-control-'+bank)
        for ref,target in list(targets.items()):
            if ref in groups and target in groups:groups[ref]=groups[target]
    di='motherboard_di'
    if di in block_models:
        m=block_models[di]
        for ch in m['channels']:
            # ch.group describes field-supply grouping, not the two-path IC.
            g='DI-pair-'+str(int(ch['id'][2:])//2)
            for k in ('schematic_ref','threshold_ref','sense_ref','filter_ref','output_bias_ref'):assign(di,ch[k],g)
        for ref,c in m['components'].items():
            if c.get('role')=='logic_bypass':
                i=int(re.search(r'\d+$',ref).group())%100-1
                assign(di,ref,'DI-pair-'+str(i));targets[parent(di,ref)]=parent(di,'U'+str(8001+i))
    fast='motherboard_fast_inputs'
    if fast in block_models:
        m=block_models[fast]
        for ch in m['channels']:
            g='receiver-'+ch['receiver'];assign(fast,ch['receiver'],g);assign(fast,ch['termination'],g)
        for ref,c in m['components'].items():
            if ref.startswith('C'):
                n=int(ref[1:]);target='U'+str((n-1)//2+1)
                assign(fast,ref,'receiver-'+target);targets[parent(fast,ref)]=parent(fast,target)
    power='motherboard_motor_power'
    if power in block_models:
        m=block_models[power]
        for w in m['windows']:
            g='motor-power-'+w['domain']+'-'+w['bank'];assign(power,w['supervisor'],g)
            for d in w['dividers']:
                for k in ('top_ref','bottom_ref'):assign(power,d[k],g)
        for ref,c in m['components'].items():
            n=int(re.search(r'\d+$',ref).group())
            if ref.startswith('C') and c.get('role')=='window supervisor bypass':
                target='U'+str(n);r,t=parent(power,ref),parent(power,target)
                targets[r]=t
                if t in groups:groups.setdefault(r,groups[t])
            if c.get('role','').endswith('bypass'):
                # Other health bypasses remain in the same authentic bank block.
                pass
            bank='B' if any(net and ('_B_' in net or net.endswith('_B')) for net in c.get('pins',{}).values()) else 'A'
            assign(power,ref,'motor-health-'+bank)
        health_caps={'C9005':'U9005','C9006':'U9006','C9007':'U9007','C9008':'U9007','C9009':'U9008'}
        for ref,target in health_caps.items():
            r,t=parent(power,ref),parent(power,target)
            if r in parts and t in groups:targets[r]=t;groups[r]=groups[t]
    do='motherboard_do'
    if do in block_models:
        m=block_models[do];driver_groups={}
        for ch in m['channels']:
            g='DO-quad-'+str(int(ch['id'][2:])//4);driver_groups[ch['driver']]=g
            for k in ('driver','rcb_fet','output_filter'):assign(do,ch[k],g)
        active=None;anchor=None
        for ref,c in m['components'].items():
            if ref in driver_groups:active=driver_groups[ref];anchor=parent(do,ref)
            host=any(net and ('_HOST' in net or 'OUT_PERMIT_' in net or '_CLR_N' in net) for net in c.get('pins',{}).values())
            bank='B' if any(net and (net.startswith('DOB_') or net.startswith('FIELD_B')) for net in c.get('pins',{}).values()) else 'A'
            if host and ref not in driver_groups:active='DO-control-'+bank;anchor=parent(do,ref) if ref.startswith('U') else anchor
            if active:assign(do,ref,active)
            else:assign(do,ref,'DO-control-'+bank)
            if ref.startswith('C') and any(w in c.get('role','') for w in ('bypass','stabilizer','local VS MLCC')) and anchor:
                targets[parent(do,ref)]=anchor
            target=re.search(r'(U\d+) logic decoupling',c.get('role',''))
            if target:targets[parent(do,ref)]=parent(do,target.group(1))
    control='motherboard_control_bridges'
    if control in block_models:
        for ref in block_models[control]['components']:assign(control,ref,'real-control-fanout')
    for ref,c in parts.items():
        if ref not in groups and c.get('source_block') not in ('fpga_core','mc_local_power','watchdog_conditioning','mc_permission','mc_motor_buffers'):
            raise ValueError('Unassigned new physical functional region '+ref+' '+c.get('source_block',''))
    return groups,targets


def region_boxes(groups):
    boxes={}
    for i in range(6):boxes['motor-pair-'+str(i)]=(232.+(i%3)*74.,10.+(i//3)*54.,70.,50.)
    boxes['motor-control-A']=(232.,122.,106.,26.)
    boxes['motor-control-B']=(344.,122.,106.,26.)
    power=['motor-power-LOGIC-A','motor-power-FIELD-A','motor-health-A','motor-power-LOGIC-B','motor-power-FIELD-B','motor-health-B']
    for i,k in enumerate(power):boxes[k]=(10.+i*35.,112.,32.,44.)
    for i in range(12):boxes['DI-pair-'+str(i)]=(10.+(i%6)*35.,170.+(i//6)*34.,32.,30.)
    for i in range(4):boxes['receiver-U'+str(i+1)]=(10.+i*53.,246.,49.,34.)
    for i in range(4):boxes['DO-quad-'+str(i)]=(232.+(i%2)*112.,160.+(i//2)*38.,106.,34.)
    boxes['DO-control-A']=(232.,242.,106.,30.)
    boxes['DO-control-B']=(344.,242.,106.,30.)
    boxes['real-control-fanout']=(150.,102.,70.,8.)
    unknown=set(groups.values())-set(boxes)
    if unknown:raise ValueError('No actual region plan for '+str(sorted(unknown)))
    return {k:boxes[k] for k in sorted(set(groups.values()))}


def courtyard_relative(fp):
    layers=pcbnew.LSET();layers.AddLayer(pcbnew.F_CrtYd)
    box=fp.GetLayerBoundingBox(layers)
    if box.GetWidth()==0 or box.GetHeight()==0:raise ValueError('Exact source footprint lacks finite courtyard '+fp.GetReference())
    return bb(box)


class Occupancy:
    """Exact courtyard collisions through conservative five-mm bins."""
    def __init__(self,boxes=()):
        self.boxes=[];self.bins={}
        for box in boxes:self.append(box)
    def keys(self,b):
        for x in range(math.floor(b[0]/5),math.floor(b[2]/5)+1):
            for y in range(math.floor(b[1]/5),math.floor(b[3]/5)+1):yield x,y
    def append(self,b):
        index=len(self.boxes);self.boxes.append(b)
        for key in self.keys(b):self.bins.setdefault(key,set()).add(index)
    def collision(self,b,gap):
        ids=set()
        for key in self.keys((b[0]-gap,b[1]-gap,b[2]+gap,b[3]+gap)):ids.update(self.bins.get(key,()))
        return any(intersects(b,self.boxes[i],gap) for i in ids)


def place_cluster(board,refs,footprints,model,nodes,rect,targets,pin_functions=None,occupied=None,bypass_specs=None):
    x,y,w,h=rect;occupied=Occupancy() if occupied is None else occupied
    placed={};centers={};relative={r:courtyard_relative(footprints[r]) for r in refs}
    # Incremental source additions can belong to an already retained IC.
    # Exact owner pins are optional; the historical callers retain their
    # independent supply-pin inference and unchanged behavior.
    bypass_specs=bypass_specs or {}
    for target in set(targets.values())-set(refs):
        if target in footprints:centers[target]=mm(footprints[target].GetPosition())
    frequencies=Counter(n for (r,p),n in nodes.items() if r in refs)
    nets={r:{n for (v,p),n in nodes.items() if v==r and not n.startswith('unconnected-') and frequencies[n]<=8
             and not re.search(r'(GND|_0V|_3V3|_5V|_24V|_VDD|_VS)$',n)} for r in refs}
    def priority(r):
        role=model[r].get('role','')
        return (0 if r.startswith('U') and not ('reverse blocking' in role or 'photorelay' in role) else
                1 if r in targets else 2 if r.startswith('U') else 3,r)
    order=sorted(refs,key=priority)
    pending=set(order);last=None;power_targets={}
    while pending:
        ready=[r for r in order if r in pending and (r not in targets or targets[r] in placed or targets[r] not in pending)]
        if not ready:raise ValueError('Cyclic local bypass target')
        attached=[r for r in ready if targets.get(r)==last]
        ref=(attached or ready)[0];fp=footprints[ref];box=relative[ref]
        neighbor=[centers[r] for r in placed if nets[r]&nets[ref]]
        if ref in targets and targets[ref] in centers:
            target=targets[ref];tf=footprints[target]
            cap_nets={p.GetNetname() for p in fp.Pads() if copper_pad(p)}
            functions=(pin_functions or {}).get(target,{})
            output_bulk='gated enable supply output' in model[ref].get('role','')
            exact=bypass_specs.get(ref)
            supply=[p for p in tf.Pads() if copper_pad(p) and
                    ((exact and p.GetNumber()==exact['owner_power_pin']) or
                     (not exact and p.GetNetname() in cap_nets
                    and ((functions.get(p.GetNumber(),{}).get('type')=='power_in'
                          and re.search(r'^(?:VCC|VDD|VS$|VIN|V\+)',functions.get(p.GetNumber(),{}).get('name','')))
                         or (output_bulk and functions.get(p.GetNumber(),{}).get('name')=='VOUT'))))]
            if supply:
                pad=supply[0];sx,sy=mm(pad.GetPosition());sign=1 if sx>=centers[target][0] else -1
                fp.SetOrientationDegrees(0 if sign>0 else 180)
                box=courtyard_relative(fp);relative[ref]=box
                cp=next(p for p in fp.Pads() if copper_pad(p) and
                        (p.GetNumber()==exact['capacitor_power_pin'] if exact else p.GetNetname()==pad.GetNetname()))
                cx,cy=mm(cp.GetPosition());desired=(sx+sign*1.-cx,sy-cy)
                power_targets[ref]=(target,pad.GetNumber(),pad.GetNetname())
            else:
                raise ValueError('No reviewed actual supply pin for bypass '+ref+' target '+target)
        elif neighbor:desired=tuple(sum(p[i] for p in neighbor)/len(neighbor) for i in (0,1))
        else:desired=(x+w/2.,y+h/2.)
        # Search near authentic connected circuitry; references remain F.Fab.
        candidates=[]
        for gx in range(math.ceil((x+1.-box[0])*2),math.floor((x+w-1.-box[2])*2)+1):
            for gy in range(math.ceil((y+1.-box[1])*2),math.floor((y+h-1.-box[3])*2)+1):
                px,py=gx/2.,gy/2.;score=(px-desired[0])**2+(py-desired[1])**2
                candidates.append((score,px,py))
        candidates.sort()
        selected=None
        for _,px,py in candidates:
            bounds=(px+box[0],py+box[1],px+box[2],py+box[3])
            if not occupied.collision(bounds,.35):selected=(px,py,bounds);break
        if selected is None:raise ValueError('Actual footprints do not fit functional region '+ref+' '+str(rect))
        px,py,bounds=selected;fp.SetPosition(xy((px,py)));occupied.append(bounds);placed[ref]=bounds;centers[ref]=(px,py);pending.remove(ref)
        last=ref if ref.startswith('U') else (targets.get(ref) if ref in targets else ref)
    result=[]
    for r in order:
        item=dict(reference=r,position_mm=list(centers[r]),courtyard_mm=list(placed[r]),rotation_degrees=footprints[r].GetOrientationDegrees(),
                  bypass_target=targets.get(r),target_distance_mm=math.dist(centers[r],centers[targets[r]]) if targets.get(r) in centers else None)
        if r in power_targets:
            target,pin,net=power_targets[r];tf=footprints[target]
            tp=next(p for p in tf.Pads() if p.GetNumber()==pin)
            spec=bypass_specs.get(r)
            cp=next(p for p in footprints[r].Pads() if
                    (p.GetNumber()==spec['capacitor_power_pin'] if spec else p.GetNetname()==net))
            ground=[p for p in tf.Pads() if copper_pad(p) and p.GetNetname()!=net
                    and ((spec and p.GetNumber() in spec['owner_return_pins']) or
                         (not spec and 'GND' in (pin_functions or {}).get(target,{}).get(p.GetNumber(),{}).get('name','')))]
            cg=[p for p in footprints[r].Pads() if copper_pad(p) and p.GetNetname()!=net]
            ground=[p for p in ground if any(q.GetNetname()==p.GetNetname() for q in cg)]
            item.update(supply_pin=target+'.'+pin,supply_pin_function=pin_functions[target][pin]['name'],
                        supply_pad_distance_mm=math.dist(mm(tp.GetPosition()),mm(cp.GetPosition())),
                        closest_same_net_ground_pad_distance_mm=min((math.dist(mm(p.GetPosition()),mm(q.GetPosition())) for p in ground for q in cg
                                                                     if p.GetNetname()==q.GetNetname()),default=None),
                        bypass_copper_routed=False)
        result.append(item)
    return result


def mechanical_reservations():
    return [
      dict(name='purchased compute bay',rectangle_mm=[232.,282.,74.,50.],status='nonphysical reservation; exact sockets/mates/height/thermal/antenna still required'),
      dict(name='replaceable purchased ESP/service',rectangle_mm=[312.,282.,36.,50.],status='nonphysical reservation; exact module, pins and antenna keepout not selected'),
      dict(name='storage/settings/accessory and analog/comms',rectangle_mm=[354.,282.,96.,50.],status='nonphysical reservation; unfinished actual source and mechanics'),
      dict(name='DI sensor/receiver terminal edge',rectangle_mm=[10.,288.,210.,40.],status='nonphysical reservation; protected supplies, connector/plug drawings still open'),
      dict(name='motor/output terminal edge',rectangle_mm=[232.,1.,218.,7.],status='nonphysical reservation; exact field connector mating/clearance remains open')]


def draw_box(board,rectangle,label):
    x,y,w,h=rectangle
    for a,b in (((x,y),(x+w,y)),((x+w,y),(x+w,y+h)),((x+w,y+h),(x,y+h)),((x,y+h),(x,y))):
        line=pcbnew.PCB_SHAPE(board);line.SetShape(pcbnew.SHAPE_T_SEGMENT);line.SetLayer(pcbnew.Dwgs_User)
        line.SetStart(xy(a));line.SetEnd(xy(b));line.SetWidth(pcbnew.FromMM(.1));board.Add(line)
    text=pcbnew.PCB_TEXT(board);text.SetText(label);text.SetLayer(pcbnew.Dwgs_User);text.SetPosition(xy((x+w/2.,y+2.)))
    text.SetTextSize(xy((.75,.75)));text.SetTextThickness(pcbnew.FromMM(.1));board.Add(text)


def expand_outline(board):
    edges=[s for s in board.GetDrawings() if s.GetLayer()==pcbnew.Edge_Cuts]
    if len(edges)!=4 or any(s.GetShape()!=pcbnew.SHAPE_T_SEGMENT for s in edges):raise ValueError('Expected four-edge rectangular provisional source outline')
    changes=[]
    for s in edges:
        a,b=mm(s.GetStart()),mm(s.GetEnd())
        if any(v not in (0.,220.) for v in (a[0],b[0])) or any(v not in (0.,100.) for v in (a[1],b[1])):
            raise ValueError('Unknown source mechanical outline; refuse implicit resizing')
        convert=lambda p:(WIDTH if p[0]==220. else p[0],HEIGHT if p[1]==100. else p[1])
        na,nb=convert(a),convert(b);s.SetStart(xy(na));s.SetEnd(xy(nb))
        changes.append(dict(uuid=s.m_Uuid.AsString(),before=[a,b],after=[na,nb],reason='only authorized provisional outline enlargement'))
    return changes


def verify_population(board,model,nodes,old_tracks,old_pads,old_footprints,ledger,expected_pad_templates=None):
    errors=[];fps={f.GetReference():f for f in board.GetFootprints()}
    if len(fps)!=len(board.GetFootprints()):errors.append('Duplicate physical reference on board')
    if set(fps)!=set(model['components']):errors.append('Board/source physical reference inventory differs')
    tracks={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    if tracks!=old_tracks:errors.append('Retained copper UUID/net/geometry changed or copper added by population')
    permitted={(r['reference'],r['pin']):(r['old_native_net'],r['new_native_net']) for r in ledger}
    changes=[];observed={};paste=0;other_non_electrical=0
    for ref,fp in fps.items():
        if footprint_name(fp)!=model['components'][ref]['footprint']:errors.append('Exact footprint mismatch '+ref)
        if expected_pad_templates is not None and ref in expected_pad_templates:
            if Counter(pad_template(p) for p in fp.Pads())!=Counter(expected_pad_templates[ref]):
                errors.append('Exact source pad/stencil geometry inventory changed '+ref)
        for p in fp.Pads():
            if not copper_pad(p):
                if not p.GetNumber() and p.IsOnLayer(pcbnew.F_Paste) and not p.IsOnCopperLayer():paste+=1
                else:other_non_electrical+=1
                continue
            key=(ref,p.GetNumber());observed.setdefault(key,[]).append(p)
            expected=nodes.get(key)
            if expected is None:errors.append('Numbered copper pad missing native source '+ref+'.'+p.GetNumber())
            elif p.GetNetname()!=expected:errors.append('Source pad/net mismatch '+ref+'.'+p.GetNumber())
            if key in old_pads:
                before=old_pads[key];after=pad_identity(p)
                if before[1:]!=after[1:]:errors.append('Retained pad geometry changed '+str(key))
                if before[0]!=after[0]:
                    if permitted.get(key)!=(before[0],after[0]):errors.append('Unapproved retained pad rename '+str(key))
                    else:changes.append(dict(reference=ref,pin=key[1],old_native_net=before[0],new_native_net=after[0]))
    if set(observed)!=set(nodes):errors.append('Missing/extra complete numbered-copper source pin inventory')
    for ref,original in old_footprints.items():
        current=fps[ref]
        if (current.m_Uuid.AsString(),tuple(current.GetPosition()),current.GetOrientationDegrees(),current.GetLayer(),footprint_name(current))!=original:
            errors.append('Retained footprint UUID/placement/orientation/side/identity changed '+ref)
    return dict(ok=not errors,errors=errors,physical_footprints=len(fps),fitted_footprints=sum(not f.IsDNP() for f in fps.values()),
        native_numbered_copper_nodes=len(nodes),physical_numbered_copper_pieces=sum(len(v) for v in observed.values()),
        stencil_only_unnumbered_apertures=paste,other_non_electrical_pads=other_non_electrical,
        bounded_retained_FPGA_pad_renames=changes,retained_copper_items=len(tracks))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,required=True)
    p.add_argument('--source',type=Path,default=ROOT/'hardware/motherboard');p.add_argument('--out',type=Path,required=True)
    p.add_argument('--ledger',type=Path,default=ROOT/'hardware/motherboard/assembly-map.json');a=p.parse_args()
    source=a.source.resolve();base=a.board.resolve();out=a.out.resolve()
    if out.exists() or not out.is_relative_to(REPORT):raise ValueError('Use a new owned immutable motherboard PCB report directory')
    model=load(source/'design.json');mapping=load(source/'assembly-map.json');physical=model['components']
    if not model.get('one_custom_board') or model.get('manufacturing_ready'):raise ValueError('Expected incomplete real one-board parent source')
    native,nodes=native_parts_and_nets(source/'netlist.xml',physical)
    pin_functions=native_pin_functions(source/'netlist.xml')
    clear_check=watchdog_clear_source_check(model,nodes)
    if not clear_check['ok']:raise ValueError('Invalid source watchdog command bridge: '+str(clear_check['errors']))
    input_files=[base,base.with_suffix('.kicad_pro'),base.with_suffix('.kicad_dru'),source/'design.json',source/'netlist.xml',source/'assembly-map.json']
    block_paths={k:((source/'source-blocks'/k/'design.json') if (source/'source-blocks'/k/'design.json').is_file()
                   else ROOT/'hardware'/k/'design.json') for k in mapping['blocks']}
    block_models={k:(load(block_paths[k]) if block_paths[k].is_file()
                    else dict(components={r:c for r,c in physical.items() if c.get('source_block')==k}))
                  for k in mapping['blocks']}
    input_files += [block_paths[k] for k in block_models if block_paths[k].is_file()]
    ledger=[]
    if a.ledger.exists():
        lm=load(a.ledger);ledger=lm.get('native_net_renames_allowed',lm.get('exact_pin_rename_ledger',[]))
        input_files.append(a.ledger.resolve())
        if len(ledger)!=64 or len({(r['reference'],r['pin']) for r in ledger})!=64:raise ValueError('FPGA reconciliation must be the exact 64-pin ledger')
    input_hashes={str(f):sha(f) for f in input_files}
    b=pcbnew.LoadBoard(str(base));b.BuildConnectivity()
    old_tracks={t.m_Uuid.AsString():identity(t) for t in b.GetTracks()}
    old_pads={(p.GetParentFootprint().GetReference(),p.GetNumber()):pad_identity(p) for p in b.GetPads() if copper_pad(p)}
    retained={f.GetReference():f for f in b.GetFootprints()}
    old_fps={r:(f.m_Uuid.AsString(),tuple(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),footprint_name(f)) for r,f in retained.items()}
    if len(retained)!=327:raise ValueError('Population must start from the current retained 327-part routed board')
    if not set(retained)<=set(physical):raise ValueError('Actual source removed an existing footprint')
    nets={str(n.GetNetname()):n for n in b.GetNetsByName().values()};new_net_names=sorted(set(nodes.values())-set(nets))
    next_code=max(n.GetNetCode() for n in nets.values())+1
    for n in new_net_names:
        net=pcbnew.NETINFO_ITEM(b,n,next_code);next_code+=1;b.Add(net);nets[n]=net
    permitted={(r['reference'],r['pin']):(r['old_native_net'],r['new_native_net']) for r in ledger}
    for key,before in old_pads.items():
        expected=nodes.get(key)
        if expected is None:raise ValueError('Parent source removed retained physical pin '+str(key))
        if expected!=before[0]:
            if permitted.get(key)!=(before[0],expected):raise ValueError('Unapproved retained physical net change '+str(key)+' '+str((before[0],expected)))
            matches=[q for q in retained[key[0]].Pads() if q.GetNumber()==key[1] and copper_pad(q)]
            for q in matches:q.SetNet(nets[expected])
    added={};footprint_inputs={};pad_templates={}
    for ref,c in physical.items():
        if ref in retained:continue
        name=c.get('footprint')
        if not name:raise ValueError('Actual physical source has no exact footprint '+ref)
        fp,file=load_exact_footprint(name,source,base);footprint_inputs[str(file)]=sha(file)
        pad_templates[ref]=[pad_template(q) for q in fp.Pads()]
        fp.SetReference(ref);fp.SetValue(c['value']);fp.Value().SetVisible(False)
        fp.Reference().SetLayer(pcbnew.F_Fab);fp.Reference().SetTextSize(xy((.65,.65)));fp.Reference().SetTextThickness(pcbnew.FromMM(.1))
        fp.SetDNP(c.get('dnp',not c.get('fitted',True)))
        path=native[ref].find('sheetpath').attrib['tstamps']+native[ref].findtext('tstamps')
        fp.SetPath(pcbnew.KIID_PATH(path));b.Add(fp)
        numbered={q.GetNumber() for q in fp.Pads() if copper_pad(q)}
        expected={pin for r,pin in nodes if r==ref}
        if numbered!=expected:raise ValueError('Exact footprint/source numbered-copper pin mismatch '+ref+' '+str((sorted(numbered),sorted(expected))))
        for pad in fp.Pads():
            if copper_pad(pad):pad.SetNet(nets[nodes[ref,pad.GetNumber()]])
        added[ref]=fp
    groups,targets=functional_groups(physical,mapping,block_models);regions=region_boxes({r:groups[r] for r in added})
    placements=[]
    for group,rect in regions.items():
        refs=[r for r in added if groups[r]==group]
        placements += [dict(v,region=group) for v in place_cluster(b,refs,added,physical,nodes,rect,targets,pin_functions)]
        draw_box(b,rect,group+' / incomplete routing')
    reservations=mechanical_reservations()
    for r in reservations:draw_box(b,r['rectangle_mm'],r['name']+' / RESERVED ONLY')
    outline=expand_outline(b)
    out.mkdir(parents=True);dest=out/'motherboard-populated-candidate.kicad_pcb'
    for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(base.with_suffix(suffix),dest.with_suffix(suffix))
    for parent in (base.parent,source):
        for folder in parent.glob('*.pretty'):
            target=out/folder.name
            if not target.exists():shutil.copytree(folder,target)
        for name in ('3dmodels','fp-lib-table'):
            f=parent/name;target=out/name
            if f.is_dir() and not target.exists():shutil.copytree(f,target)
            elif f.is_file():shutil.copyfile(f,target)
    snapshot=out/'source-inputs';snapshot.mkdir()
    for f in input_files:shutil.copyfile(f,snapshot/(f.parent.name+'-'+f.name))
    write(out/'placement-ledger.json',placements);write(out/'mechanical-reservations.json',reservations)
    write(out/'exact-source-pad-templates.json',pad_templates)
    b.BuildConnectivity();pcbnew.SaveBoard(str(dest),b)
    cmd=[str(CLI),'pcb','drc','--format','json','--output',str(out/'drc.json'),str(dest)]
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',errors='replace')
    (out/'drc-command.txt').write_text(run.stdout+run.stderr,encoding='utf8')
    if not (out/'drc.json').is_file():raise ValueError('Native DRC did not generate its report')
    fresh=pcbnew.LoadBoard(str(dest));fresh.BuildConnectivity()
    verification=verify_population(fresh,model,nodes,old_tracks,old_pads,old_fps,ledger,pad_templates)
    verification['native_object_retention']=native_retained_objects(base,dest,ledger)
    if not verification['native_object_retention']['ok']:
        verification['errors']+=verification['native_object_retention']['errors'];verification['ok']=False
    old_zones=raw_items(base,'zone');new_zones=raw_items(dest,'zone')
    verification['retained_zone_native_definitions_unchanged']=old_zones==new_zones
    if old_zones!=new_zones:verification['errors'].append('Retained filled zone definitions changed');verification['ok']=False
    verification['source_inputs_unchanged']=all(sha(Path(f))==h for f,h in input_hashes.items())
    if not verification['source_inputs_unchanged']:verification['errors'].append('Source input changed during population');verification['ok']=False
    drc=load(out/'drc.json');violations=drc.get('violations',[])
    report=dict(schema_version=1,source_board_sha256=input_hashes[str(base)],candidate_board_sha256=sha(dest),
        source_inputs_sha256=input_hashes,exact_footprint_inputs_sha256=footprint_inputs,
        population=verification,added_footprints=len(added),retained_footprints=len(retained),
        watchdog_clear_source_check=clear_check,
        layers=fresh.GetCopperLayerCount(),thickness_mm=pcbnew.ToMM(fresh.GetDesignSettings().GetBoardThickness()),
        dimensions_mm=[WIDTH,HEIGHT],final_outline=False,outline_changes=outline,
        retained_filled_zones=len(fresh.Zones()),new_field_or_full_board_planes_added=False,
        native_drc=dict(exit_code=run.returncode,regular_violations=len(violations),types=dict(Counter(v['type'] for v in violations)),
            severities=dict(Counter(v['severity'] for v in violations)),ignored_checks=drc.get('ignored_checks',[]),
            capped_unconnected_items=len(drc.get('unconnected_items',[])),report='drc.json'),
        uncapped_native_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),
        authentic_native_NC_pads=sum(n.startswith('unconnected-') for n in nodes.values()),
        source_circuit_blocks=dict(Counter(c.get('source_block') for c in physical.values())),
        purchased_module_footprints_added=False,mechanical_reservations=reservations,
        final_placement=False,routing_complete=False,manufacturing_ready=False,physical_qualification=False,
        scope='Complete actual-source footprint population and bounded NC reconciliation on retained copper; expanded provisional physical candidate with actual open routing and mechanics')
    write(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ('population','added_footprints','native_drc','uncapped_native_missing_joins','manufacturing_ready')},indent=2))
    if not verification['ok']:raise ValueError('Independent population/retention verification failed')


if __name__=='__main__':main()
