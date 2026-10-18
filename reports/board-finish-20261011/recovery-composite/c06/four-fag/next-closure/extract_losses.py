"""Exact remaining native loss components and closest conductive-body witnesses.

No route proposal, native/API call, board mutation or adoption. Smallest means
the required component joins, not a claimed physically feasible route.
"""
import argparse,copy,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
STAGE=HERE.parent
sys.path.insert(0,str(STAGE));sys.path.insert(0,str(STAGE.parent));sys.path.insert(0,str(STAGE.parent/'alternate-r07'))
import validate_combined as V
import screen_c06 as S
import screen_r07 as R
sys.path.insert(0,str(V.REPORT/'gate-repair'))
import importlib.util
spec=importlib.util.spec_from_file_location('strict_native_loss_guard',V.REPORT/'gate-repair/partition_guard.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
from shapely.ops import unary_union,nearest_points

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expected',action='store_true',help='Host signal-group expectation only; native comparison still required')
    args=ap.parse_args()
    out=V.REPORT/'measure/r07-four-fag-shared'
    after_path=out/'partitions.json'
    if not args.expected and not after_path.is_file():raise ValueError('Native combined partitions not yet available; no source inference substituted')
    destination=HERE/('expected-r06-losses.json' if args.expected else 'remaining-r06-losses.json')
    if destination.exists():raise ValueError('Distinct immutable inventory required')
    candidate=V.FAG/'staged/r07-four-path-fag-repaired.kicad_pcb';construction=V.FAG/'staged/construction.json'
    V.validate_construction(construction,candidate)
    before=json.loads(S.read(R.R06_PART));live=json.loads(S.read(R.R07_PART))
    G.check_board(before,S.overlay_tool.base.BASE);G.check_board(live,R.R07)
    if args.expected:
        raw=None;after=copy.deepcopy(live)
        four=json.loads(S.read(V.FOUR/'audit.json'))
        for path in four['rows']:
            net=next(net for net in after['nets'] if S.norm(net)==S.norm(path['net']))
            groups=after['nets'][net];wanted={pid for group in path['physical_pad_groups'] for pid in group}
            selected=[group for group in groups if set(group)&wanted]
            if len(selected)!=2 or {pid for group in selected for pid in group}!=wanted:
                raise ValueError('Frozen two-component signal expectation differs from original native source')
            after['nets'][net]=[group for group in groups if group not in selected]+[sorted(wanted)]
        changes={}
        for net in before['nets']:
            common=G.common_groups(before['nets'][net],after['nets'][net])
            complete=len(before['nets'][net])-common;lost=len(after['nets'][net])-common
            if complete or lost:changes[net]={'completed':complete,'lost':lost}
        comparison={'evidence_class':'HOST_SIGNAL_TOPOLOGY_EXPECTATION_ONLY','per_net':changes,'lost':sum(row['lost'] for row in changes.values()),
                    'verdict':'NATIVE_GUARD_NOT_RUN','FIELD_return_additions_modeled':False}
        live_comparison={'verdict':'NATIVE_GUARD_NOT_RUN','evidence_class':'HOST_SIGNAL_TOPOLOGY_EXPECTATION_ONLY','lost':0,'signal_joins_expected':4}
    else:
        raw=S.read(after_path);after=json.loads(raw);G.check_board(after,candidate)
        comparison=G.compare(before,after);live_comparison=G.compare(live,after)
    for path in (Path(__file__),Path(V.__file__),Path(S.__file__),Path(R.__file__),Path(G.__file__)):
        S.read(path)
    g,old_targets,overlay=R.overlay_and_targets()
    old=R.composition.inventory(S.read(R.R07));new=R.composition.inventory(S.read(candidate))
    for uid,ch in new[4].items():
        if uid in old[4]:continue
        row=V.C.W.parse_copper(uid,ch)
        if row['kind']=='via':
            g['vias'].append({'uuid':uid,'net':row['net'],'x':row['at'][0],'y':row['at'][1],'d':row['d'],'drill':row['drill'],'span':['F.Cu','B.Cu'],'flashed':g['copper_layers']})
        else:g['tracks'].append({'uuid':uid,'net':row['net'],'a':row['a'],'b':row['b'],'w':row['width'],'layer':row['layer']})
    g['sha256']=sha(candidate.read_bytes());g['board']=str(candidate);g['refilled']=False
    reservations=json.loads(S.read(STAGE.parent/'alternate-r07/reserved-r07.json'));exempt={}
    for line in S.read(STAGE.parent/'alternate-r07/reserve/board.kicad_dru').decode().splitlines():
        match=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
        if match:exempt[match[1]]={S.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",match[2])}
    print('LOSS_COMPONENT_MODEL_START',flush=True);model=S.Model(g,reservations,exempt);print('LOSS_COMPONENT_MODEL_READY',flush=True)
    legacy=json.loads(S.read(STAGE.parent/'alternate-r07-small/feasibility.json'))
    previous={S.norm(row['net']):row for row in legacy['results']}
    controlled={S.norm(net):policy for net,policy in json.loads(S.read(S.CONTROLLED))['nets'].items()}
    rows=[]
    for net,delta in comparison['per_net'].items():
        if not delta['lost']:continue
        relationships=[]
        for original_group in before['nets'][net]:
            touched=[group for group in after['nets'][net] if set(group)&set(original_group)]
            if len(touched)>1:relationships.append({'r06_pad_relationship':original_group,'current_split_native_groups':touched})
        target={'net':net,'domain':g['nets'][net],'c05_groups':after['nets'][net],
                'lost_relationships':[{'r07_connected_pad_ids':relationships[0]['r06_pad_relationship']}]}
        record={'net':net,'domain':g['nets'][net],'native_lost_joins':delta['lost'],'relationships':relationships,
                'required_component_joins':delta['lost'],'controlled_policy':controlled.get(S.norm(net)),
                'current_path_status':'NO_ROUTE_PROPOSED','closest_conductive_body_witnesses':[]}
        try:
            if len(relationships)!=1 or len(relationships[0]['current_split_native_groups'])!=2:
                raise ValueError('Multiple-loss topology requires a distinct component spanning graph')
            groups=model.contact_groups(target)
            record['physical_current_components']=[group['pad_ids'] for group in groups]
            for layer in S.LAYERS:
                a=[row for row in groups[0]['records'] if row['layer']==layer]
                b=[row for row in groups[1]['records'] if row['layer']==layer]
                if not a or not b:
                    record['closest_conductive_body_witnesses'].append({'layer':layer,'status':'NO_SHARED_EXISTING_CONTACT_LAYER'});continue
                first=unary_union([row['shape'] for row in a]);second=unary_union([row['shape'] for row in b])
                pa,pb=nearest_points(first,second)
                owner_a=min(a,key=lambda row:row['shape'].distance(pa));owner_b=min(b,key=lambda row:row['shape'].distance(pb))
                record['closest_conductive_body_witnesses'].append({'layer':layer,'body_gap_mm':first.distance(second),
                    'endpoint_a_mm':list(pa.coords[0]),'endpoint_b_mm':list(pb.coords[0]),
                    'endpoint_a_owner_uuid':owner_a['uuid'],'endpoint_b_owner_uuid':owner_b['uuid'],
                    'endpoint_a_kind':owner_a['kind'],'endpoint_b_kind':owner_b['kind'],
                    'scope':'Geometric body distance only. No path, clearance, meaningful copper overlap, reference or current qualification.'})
        except ValueError as exc:record['physical_model_withheld']=str(exc)
        earlier=previous.get(S.norm(net))
        if earlier:
            record['prior_bounded_screen']={'source_sha256':legacy['source_board_sha256'],'verdict':earlier['verdict'],
                'zero_via':[{'layer':row['layer'],'reason':row.get('reason'),'search':row.get('search')} for row in earlier['zero_via_layers']],
                'landing_components':[{'component':row['component'],'layer':row['layer'],'area_mm2':row.get('reachable_via_landing_area_mm2'),'sampled_sites':row.get('sampled_sites')} for row in earlier['dive_landings']],
                'sampled_landing_pairs':earlier.get('sampled_landing_pairs'),
                'scope':'Original r07 24s/.1mm-grid/6-pair bound only; not a global no-path result or current combined qualification'}
        rows.append(record)
    for path,expected in S.READS.items():
        if sha(Path(path).read_bytes())!=expected:raise ValueError('Loss inventory input changed:'+path)
    result={'schema':'combined-r06-loss-components-v1','verdict':'HOST_EXPECTATION_PENDING_NATIVE' if args.expected else 'DIAGNOSTIC_COMPLETE_NATIVE_REGRESSION_FATAL',
            'candidate_sha256':sha(candidate.read_bytes()),'native_partition_sha256':None if raw is None else sha(raw),'against_r06':comparison,'against_actual_r07':live_comparison,
            'remaining_lost_nets':len(rows),'remaining_required_component_joins':sum(row['required_component_joins'] for row in rows),'rows':rows,
            'source_files_sha256':S.READS,'overlay':overlay,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,
            'limits':['Host expectation mode has NO fresh native proof and does not model new FIELD plane/contacts; must crosscheck actual partitions','Native loss diagnosis does not require final DRC success; final full gates still mandatory','Exact current combined copper/poses over conservative r06 fills for physical witness placement','Closest body witnesses must never be interpreted as authorized route endpoints or paths','Current controlled nets lacking pinned impedance geometry remain withheld; analog/power constraints remain separate','No old r07 item or current combined owned group is removed or modified']}
    destination.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'inventory':str(destination),'remaining_lost_nets':len(rows),'r06_lost':comparison['lost'],'r07_lost':live_comparison['lost']}))
if __name__=='__main__':main()
