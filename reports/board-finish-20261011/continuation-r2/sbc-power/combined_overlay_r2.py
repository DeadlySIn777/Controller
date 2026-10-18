"""Host overlay of root's exact serialized combined ownership, before refill."""
import json,re,copy,hashlib,math
from pathlib import Path
from shapely.geometry import Point
from shapely.affinity import rotate,translate
import joint_model_r2 as J
L=J.L;p=J.p
BOARD=L.OUT.parent/'combined-power-source-native-r1/combined-power-source-host-only.kicad_pcb'
SHA='65065e41b8243fe150a2231c17bbe8203dd0c4bb3fdbb2b1e0554ff9e14fbd41'
def chunks(data,token):
    out=[]
    for m in re.finditer(rb'\('+token+rb'\s',data):
        depth=0;quote=False;escape=False
        for i in range(m.start(),len(data)):
            ch=data[i]
            if quote:
                if escape:escape=False
                elif ch==92:escape=True
                elif ch==34:quote=False
            elif ch==34:quote=True
            elif ch==40:depth+=1
            elif ch==41:
                depth-=1
                if depth==0:out.append(data[m.start():i+1]);break
    return out
def fields(ch):return {m[1].decode():json.loads(b'"'+m[2]+b'"') for m in re.finditer(rb'\(property "([^"]+)" "((?:[^"\\]|\\.)*)"',ch)}
def pose(ch):
    row=[float(x) for x in re.search(rb'\(at\s+([^\)]+)\)',ch)[1].split()];return tuple(row+[0.]*(3-len(row)))
def rec(sh):return [[list(q.exterior.coords),[list(x.coords) for x in q.interiors]] for q in p.hubs.components(sh)]
def model(new_root_base=False):
    board=(L.OUT.parent/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb') if new_root_base else BOARD
    sha='1beb9a2296ae451daed4b905383ccc5bd3ee083b3400cf5ef2e3ab2e7b7dae6b' if new_root_base else SHA
    g,h,tail=J.model();scope,native,prior,omit=tail;raw=board.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;parent=p.base.inventory(raw);old=p.base.inventory(L.live.COMBINED.read_bytes());field=json.loads((L.OUT.parent/'field-power/candidate-recipe-r1/receipt.json').read_text());clones={x['ref']:x['clone'] for x in field['new_field_footprint_additions']};clones['C11094']='C11088'
    oldfoot={p.base.ref_of(ch):ch for ch in old[3].values() if p.base.pcbtext.chunk_kind(ch)=='footprint'};newfoot={p.base.ref_of(ch):ch for ch in parent[3].values() if p.base.pcbtext.chunk_kind(ch)=='footprint'}
    own={'U11012','C11061','C11062','C11063','C15001','C15002','R11049','C11094'};pads=list(h['pads']);feet=list(h['footprints']);fp_rows=[]
    for ref,ch in newfoot.items():
        if ref in oldfoot and ch==oldfoot[ref]:continue
        props=fields(ch)
        if ref in own:
            # Root's C61 BOM update is composed with our later pose; C94 already
            # exists at its exact source-bound target geometry in the local model.
            for f in feet:
                if f['ref']==ref:f['value']=props.get('Value',f['value'])
            continue
        proto=clones.get(ref,ref);oldch=oldfoot[proto];oa=pose(oldch);na=pose(ch);flipped=p.base.pcbtext.chunk_layer(oldch)!=p.base.pcbtext.chunk_layer(ch)
        assert not flipped or ref=='C11068',('unsupported side change',ref)
        def tx(sh):return translate(rotate(sh,oa[2]-na[2],origin=oa[:2]),na[0]-oa[0],na[1]-oa[1])
        newpads=chunks(ch,b'pad');by_num={}
        for q in newpads:by_num.setdefault(re.match(rb'\(pad "([^"]*)"',q)[1].decode(),[]).append(q)
        transformed=[]
        for q in g['pads']:
            if q['ref']!=proto:continue
            nativepad=by_num[q['num']].pop(0);qq=copy.deepcopy(q);qq['ref']=ref;qq['uuid']=re.search(rb'\(uuid "([^"]+)"',nativepad)[1].decode();qq['net']=p.netname(nativepad) if b'(net "' in nativepad else q['net']
            padtx=tx
            if flipped:
                oldpad=next(x for x in chunks(oldch,b'pad') if re.search(rb'\(uuid "([^"]+)"',x)[1].decode()==q['uuid']);oldpa=pose(oldpad);newpa=pose(nativepad);theta=math.radians(-na[2]);cx=na[0]+newpa[0]*math.cos(theta)-newpa[1]*math.sin(theta);cy=na[1]+newpa[0]*math.sin(theta)+newpa[1]*math.cos(theta)
                def padtx(sh):return translate(rotate(sh,oldpa[2]-newpa[2],origin=(q['x'],q['y'])),cx-q['x'],cy-q['y'])
            pt=padtx(Point(q['x'],q['y']));qq['x'],qq['y']=round(pt.x,6),round(pt.y,6);qq['layers']={('F.Cu' if lay=='B.Cu' else 'B.Cu' if lay=='F.Cu' else lay) if flipped else lay:[r for sh in p.base.polygons(rs) for r in rec(padtx(sh))] for lay,rs in q['layers'].items()};qq['hole']=[r for sh in p.base.polygons(q.get('hole') or []) for r in rec(padtx(sh))] or None;transformed.append(qq)
        pads=[q for q in pads if q['ref']!=ref]+transformed;f=copy.deepcopy(next(q for q in g['footprints'] if q['ref']==proto));f.update(ref=ref,x=na[0],y=na[1],value=props.get('Value',f['value']));f['courtyard']={(('F' if lay=='B' else 'B' if lay=='F' else lay) if flipped else lay):[r for sh in p.base.polygons(rs) for r in rec(tx(sh))] for lay,rs in f['courtyard'].items()};f['side']=p.base.pcbtext.chunk_layer(ch).split('.')[0];feet=[q for q in feet if q['ref']!=ref]+[f];fp_rows.append({'ref':ref,'prototype':proto,'target_pose':na,'pads':len(transformed),'native_side_flip':flipped})
    tracks={t['uuid']:t for t in h['tracks']};vias={v['uuid']:v for v in h['vias']};removed=set(old[4])-set(parent[4]);changed=[]
    actualpath=L.OUT.parent/('combined-reset-cm-native-r5-cache-refresh/native-parity.json.actual-vias.json' if new_root_base else 'combined-power-native-diagnostic-r2/native-parity.json.actual-vias.json')
    actual=json.loads(actualpath.read_text());actual_rows=actual.get('rows',actual.get('vias',[])) if isinstance(actual,dict) else actual;actualmap={r.get('uuid',r.get('expected',{}).get('uuid')):r for r in actual_rows}
    for uid in removed:tracks.pop(uid,None);vias.pop(uid,None)
    for uid,ch in parent[4].items():
        if old[4].get(uid)==ch:continue
        assert uid not in omit,('shared ownership conflict',uid);kind=p.base.pcbtext.chunk_kind(ch);changed.append(uid)
        if kind=='segment':tracks[uid]={'uuid':uid,'net':p.netname(ch),'a':p.numbers(ch,'start'),'b':p.numbers(ch,'end'),'w':p.scalar(ch,'width'),'layer':p.base.pcbtext.chunk_layer(ch),'locked':b'(locked yes)' in ch}
        elif kind=='via':
            at=p.numbers(ch,'at');v={**vias.get(uid,{}),'uuid':uid,'net':p.netname(ch),'x':at[0],'y':at[1],'d':p.scalar(ch,'size'),'drill':p.scalar(ch,'drill'),'span':g['copper_layers']}
            if uid in actualmap:v['flashed']=actualmap[uid].get('actual_flashed_layers',actualmap[uid].get('flashed',[]))
            elif uid not in vias:raise ValueError(('Missing actual parent via mask',uid))
            vias[uid]=v
        else:raise ValueError(('unsupported changed copper',kind,uid))
    domains=dict(h['domains_normalized'])
    for net in {p.norm(q['net']) for q in pads}|{p.norm(q['net']) for q in tracks.values()}|{p.norm(q['net']) for q in vias.values()}:
        if not net:
            # Unassigned mechanical pads retain their native holes and shape.
            # They are not a newly introduced electrical net/domain.
            continue
        if net not in domains:
            if 'FIELD_B' in net or 'U11038' in net or net=='DOB_DO_FIELD_3V3':domains[net]='DOM_FIELD_B'
            else:raise ValueError(('new net domain requires explicit source',net))
    h={**h,'pads':pads,'footprints':feet,'tracks':list(tracks.values()),'vias':list(vias.values()),'domains_normalized':domains};return g,h,tail,{'parent_board':str(board.resolve()),'parent_board_sha256':sha,'changed_parent_FPs':fp_rows,'changed_parent_Cu':changed,'removed_parent_Cu':sorted(removed),'actual_parent_added_vias_file':str(actualpath.resolve()),'actual_parent_added_vias_sha256':hashlib.sha256(actualpath.read_bytes()).hexdigest(),'refill_not_claimed':True}
if __name__=='__main__':
    g,h,tail,r=model();(L.OUT/'combined-overlay-binding-r2.json').write_text(json.dumps(r,indent=2)+'\n');print('COMBINED_OVERLAY',len(r['changed_parent_FPs']),len(r['changed_parent_Cu']),len(r['removed_parent_Cu']))
