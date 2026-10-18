"""Exact seven pose replacements and new local Cu; no board reserialization.

Source BOM changes are already integrated in the explicitly pinned parent.
"""
import ast,hashlib,importlib.util,json,math,re
from pathlib import Path
import inspect_integrated_source as I
HERE=Path(__file__).resolve().parent
BOARD=HERE.parent/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb'
SHA='1beb9a2296ae451daed4b905383ccc5bd3ee083b3400cf5ef2e3ab2e7b7dae6b'
OUT=HERE/'owned-native-parts-r4'
def sha(b):return hashlib.sha256(b).hexdigest()
def top_spans(s):
    depth=0;quote=False;escape=False;start=None;out=[]
    for i,c in enumerate(s):
        if quote:
            if escape:escape=False
            elif c=='\\':escape=True
            elif c=='"':quote=False
            continue
        if c=='"':quote=True;continue
        if c=='(':
            if depth==1:start=i
            depth+=1
        elif c==')':
            depth-=1
            if depth==1 and start is not None:out.append((start,i+1));start=None
            if depth<0:raise ValueError('Unbalanced chunk')
    assert depth==0 and not quote
    return out
def parser():
    ns={'re':re};tree=ast.parse(I.PARSER.read_text(encoding='utf-8'));ds=[n for n in tree.body if (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='TOKEN') or (isinstance(n,ast.FunctionDef) and n.name in ('sexpr_parse','child','children','atom','norm'))];exec(compile(ast.Module(body=ds,type_ignores=[]),'source-parser','exec'),ns);return ns
def num(v):
    v=round(float(v),6);s=f'{v:.6f}'.rstrip('0').rstrip('.');return s if s!='-0' else '0'
def atrow(row,newangle):return '(at '+num(row[1])+' '+num(row[2])+' '+num(newangle)+')'
def main():
    assert not OUT.exists(),'Use fresh frozen directory';data=BOARD.read_bytes();assert sha(data)==SHA
    spec=importlib.util.spec_from_file_location('native_pcbtext',I.PARSER.parent/'pcbtext.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);head,chunks,tail=P.split(data);byid={P.chunk_uuid(ch):ch for ch in chunks if P.chunk_uuid(ch)}
    ns=parser();parse,child,children,atom,norm=(ns[k] for k in ('sexpr_parse','child','children','atom','norm'))
    fps={re.search(rb'\(property "Reference" "([^"\r\n]+)"',ch)[1].decode():(P.chunk_uuid(ch),ch) for ch in chunks if P.chunk_kind(ch)=='footprint'}
    registry={}
    for n in re.findall(rb'\(net "([^"\r\n]+)"\)',data):
        raw=n.decode();key=norm(raw)
        if key in registry:assert registry[key]==raw,('normalized native net collision',registry[key],raw)
        registry[key]=raw
    local=json.loads((HERE/'completed-local-operation-recipe-r2.json').read_text());poseplan={r['ref']:r['target_native_at_mm_deg'] for r in local['move_native_footprints']};poseplan['R11049']=json.loads((HERE/'PG-pullup-local-move-r3.json').read_text())['R11049_target_pose'];OUT.mkdir();rows=[]
    for ref,target in poseplan.items():
        uid,old=fps[ref];text=old.decode();root=parse(text);oldat=child(root,'at');angle=float(oldat[3]) if len(oldat)>3 else 0.;delta=float(target[2])-angle;changes=[]
        # Only exact root pose, immediate-pad absolute angles and owned text
        # absolute angles change. Local coordinates and all other atoms stay.
        for a,b in reversed(top_spans(text)):
            q=parse(text[a:b]);fragment=text[a:b]
            if q[0]=='at':
                new='(at '+' '.join(num(v) for v in target)+')';changes.append({'kind':'footprint_pose','before':q[1:],'after':[num(v) for v in target]});text=text[:a]+new+text[b:]
            elif q[0] in ('pad','property','fp_text'):
                for aa,bb in reversed(top_spans(fragment)):
                    n=parse(fragment[aa:bb])
                    if n[0]!='at':continue
                    before=float(n[3]) if len(n)>3 else 0.;new=atrow(n,before+delta);changes.append({'kind':q[0]+'_absolute_angle','identity':q[1],'local_xy_retained':n[1:3],'before_deg':before,'after_deg':round(before+delta,6)});fragment=fragment[:aa]+new+fragment[bb:]
                text=text[:a]+fragment+text[b:]
        outroot=parse(text);assert [float(v) for v in child(outroot,'at')[1:]]==target
        oldpads={atom(q,'uuid'):q for q in children(root,'pad')};newpads={atom(q,'uuid'):q for q in children(outroot,'pad')};assert oldpads.keys()==newpads.keys();positions=[]
        for puid,q in newpads.items():
            oq=oldpads[puid];oldat=child(oq,'at');at=child(q,'at');assert at[1:3]==oldat[1:3];assert abs(float(at[3])-(float(oldat[3]) if len(oldat)>3 else 0.)-delta)<1e-8;oc=oq.copy();nc=q.copy();oc[oc.index(oldat)]=['at',*oldat[1:3]];nc[nc.index(at)]=['at',*at[1:3]];assert oc==nc,'Pad atoms outside angle changed'
            x,y=map(float,at[1:3]);theta=math.radians(-target[2]);absxy=[round(target[0]+x*math.cos(theta)-y*math.sin(theta),6),round(target[1]+x*math.sin(theta)+y*math.cos(theta),6)];positions.append({'uuid':puid,'pin':q[1],'position_mm':absxy,'absolute_angle_deg':float(at[3]),'net_raw':atom(q,'net')})
        # Exact reference/source/BOM properties and unchanged root fields.
        before_props={q[1]:q[2] for q in children(root,'property')};after_props={q[1]:q[2] for q in children(outroot,'property')};assert before_props==after_props;assert atom(root,'path')==atom(outroot,'path');assert atom(root,'layer')==atom(outroot,'layer');assert atom(root,'uuid')==atom(outroot,'uuid')
        f=OUT/(ref+'.footprint-chunk');f.write_bytes(text.encode());rows.append({'ref':ref,'uuid':uid,'original_parent_chunk_sha256':sha(old),'new_chunk_path':str(f.resolve()),'new_chunk_sha256':sha(f.read_bytes()),'old_pose_mm_deg':child(root,'at')[1:],'target_pose_mm_deg':target,'layer':atom(root,'layer'),'actual_native_pad_positions':positions,'exact_changed_fields':changes,'BOM_source_UUID_pad_nums_nets_local_geometry_preserved':True})
    removals=[]
    for r in local['remove_existing_item_chunks']:
        old=byid[r['uuid']];assert sha(old)==r['sha256'],('Owned old Cu changed by parent',r['uuid']);removals.append(r)
    joint=json.loads((HERE/'joint-local-quantized-r2.json').read_text());banks=json.loads((HERE/'joint-power-planes-r3.json').read_text())['new_CORE_bank_vias'];bulk=json.loads((HERE/'C94-bulk-feeds-r3.json').read_text())['new_vias'];pg=json.loads((HERE/'PG-local-dive-r5.json').read_text());pgnet='/motherboard_power_entry/SBC_SWITCH_PG'
    newtracks=[q for q in joint['new_tracks'] if q['net']!=pgnet]+pg['new_tracks'];newvias=[q for q in joint['new_vias'] if q['net']!=pgnet]+pg['new_vias']+banks+bulk;emitted=[];seen=set(byid)
    for kind,records in [('segment',newtracks),('via',newvias)]:
        for q in records:
            uid=q['uuid'];assert uid not in seen;seen.add(uid);raw=q['net'];assert registry[norm(raw)]==raw,('raw native net mismatch',raw)
            if kind=='segment':
                for xy in (q['a'],q['b']):assert xy==[round(v,6) for v in xy]
                text='\t(segment\n\t\t(start '+' '.join(num(v) for v in q['a'])+')\n\t\t(end '+' '.join(num(v) for v in q['b'])+')\n\t\t(width '+num(q['w'])+')\n\t\t(layer "'+q['layer']+'")\n\t\t(net "'+raw+'")\n\t\t(uuid "'+uid+'")\n\t)\n'
            else:
                assert q['x']==round(q['x'],6) and q['y']==round(q['y'],6);assert set(q['flashed'])=={'F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'}
                text='\t(via\n\t\t(at '+num(q['x'])+' '+num(q['y'])+')\n\t\t(size '+num(q['d'])+')\n\t\t(drill '+num(q['drill'])+')\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "'+raw+'")\n\t\t(uuid "'+uid+'")\n\t)\n'
            f=OUT/(uid+'.'+kind+'-chunk');f.write_bytes(text.encode());emitted.append({'kind':kind,'uuid':uid,'new_chunk_path':str(f.resolve()),'new_chunk_sha256':sha(f.read_bytes()),'native_model':q})
    fine=[q for q in newtracks if q['w']<.2];assert all(q['net']==pgnet and q['layer']=='F.Cu' and q['w']==.125 for q in fine);neck=sum(math.dist(q['a'],q['b']) for q in fine);assert neck<=1.5
    result={'verdict':'OWNED_PARTIAL_NATIVE_RECIPE_POWER_PLANES_AND_ALL_CONTACT_GATES_OPEN','parent_board_path':str(BOARD.resolve()),'parent_board_sha256':SHA,'native_coordinate_grid_nm':1,'footprint_replacements':rows,'old_Cu_removals':removals,'new_Cu_items':emitted,'new_via_count':len(newvias),'new_segment_count':len(newtracks),'raw_native_net_collision_count':0,'normalization_not_emitted':True,'source_BOM_already_owned_by_combined_parent':True,'exact_route_inputs':{str((HERE/n).resolve()):sha((HERE/n).read_bytes()) for n in ['joint-local-quantized-r2.json','PG-local-dive-r5.json','joint-power-planes-r3.json','C94-bulk-feeds-r3.json']},'PG_fine_neck':{'track_UUIDs':[q['uuid'] for q in fine],'cumulative_length_mm':neck,'cumulative_owned_gate_max_mm':1.5,'bulk_width_min_mm':.2,'native_literal_rule_not_yet_attested':True},'required_remaining':['Final coupled IO3 and LOGIC_GND restoration polygons','Independent cross-agent complete physical/pad/track/barrel/plane contact guard on parent1beb','Full current/fanout/return model','Native footprint pose/mask/body/ordinary-via and literal PG effective-rule check','Native refill dual connectivity and full ordinary DRC'],'native_jobs':0,'whole_board_written':False,'source_adopted':False};f=OUT/'receipt.json';f.write_text(json.dumps(result,indent=2)+'\n');assert sha(BOARD.read_bytes())==SHA;print('OWNED_NATIVE_PARTS',len(rows),len(removals),len(newtracks),len(newvias),neck,sha(f.read_bytes()))
if __name__=='__main__':main()
