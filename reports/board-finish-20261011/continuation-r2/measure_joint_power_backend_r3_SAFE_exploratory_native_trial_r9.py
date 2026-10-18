"""Full native refill/DRC of the exact source, reset and CM staging candidate."""
import collections,datetime,hashlib,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(HERE))
import native_pose_signal_contract as H
C=H.C
STAGE=Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261011\\continuation-r2\\SAFE-exploratory-native-trial-r9');OUT=STAGE/'measure'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def check(pins):
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen native measurement input changed: '+p)
def state(phase,**d):
    record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':phase,'adopted':False,**d}
    write(OUT/'status.json',record);print(json.dumps(record),flush=True)
def old_relationships(before,after,source_moved):
    # New parts do not excuse a loss between any unchanged original pads.
    memberships={p:(net,i) for net,groups in after['nets'].items() for i,g in enumerate(groups) for p in g}
    lost=[];omitted=[];checked=0
    for net,groups in before['nets'].items():
        for group in groups:
            moved=[p for p in group if p in source_moved]
            retained=[p for p in group if p not in source_moved]
            if moved:omitted.append({'net':net,'group':group,'explicitly_source_reassigned_pads':moved})
            if len(retained)<2:continue
            checked+=1
            absent=[p for p in retained if p not in memberships]
            partitions=collections.defaultdict(list)
            for p in retained:
                if p in memberships:partitions[memberships[p]].append(p)
            if absent or len(partitions)>1:lost.append({'net_before':net,'old_retained_group':retained,'missing_pads':absent,'after_groups':[{'net':k[0],'group_index':k[1],'pads':v} for k,v in partitions.items()]})
    return {'verdict':'PASS_UNCHANGED_PAD_RELATIONSHIPS' if not lost else 'FAIL_UNCHANGED_PAD_RELATIONSHIPS','old_multi_pad_groups_checked':checked,'losses':lost,'source_reassigned_pad_obligations':omitted,'source_reassigned_pads_do_not_receive_an_all_net_no_loss_verdict':True}
def main():
    if OUT.exists():raise ValueError('Fresh measurement required')
    receipt=json.loads((STAGE/'receipt.json').read_bytes())
    if receipt['verdict']!='PASS_JOINT_POWER_SOURCE_ALL_CU_ALL_NEW_ZONES_API_ONLY':raise ValueError('Native API candidate rejected')
    pins=json.loads((STAGE/'inputs.json').read_bytes());check(pins)
    candidate=STAGE/'copy/board.kicad_pcb'
    if sha(candidate)!=receipt['candidate_sha256']:raise ValueError('Candidate changed')
    OUT.mkdir();project=OUT/'project';project.mkdir();copy=OUT/'copy';copy.mkdir()
    original=BASE/'recovery-composite/c06/four-fag/inputs/project'
    for p in original.iterdir():
        if p.is_dir():shutil.copytree(p,project/p.name)
        else:shutil.copy2(p,project/p.name)
    shutil.copy2(STAGE/'copy/board.kicad_pro',project/'board.kicad_pro.good')
    shutil.copy2(STAGE/'copy/board.kicad_dru',project/'board.kicad_dru')
    fresh=HERE/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net'
    shutil.copy2(fresh,project/'sch.net')
    source=HERE/'combined-source-erc-r3/source'
    sourcepins={str(p.resolve()):sha(p) for p in source.rglob('*') if p.is_file()}
    for p in source.iterdir():
        if p.name=='fp-lib-table':continue
        if p.is_dir():shutil.copytree(p,copy/p.name)
        else:shutil.copy2(p,copy/p.name)
    # Give CLI schematic parity a real matching-stem root without changing its bytes.
    shutil.copy2(source/'motherboard.kicad_sch',copy/'board.kicad_sch')
    wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavy.sh')
    prefix=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad','C:/Program Files/KiCad/10.0/bin/kicad-cli.exe']
    export=prefix+['sch','export','netlist','--format','kicadsexpr','--output',str((OUT/'matching-stem-fresh.net').resolve()),str((copy/'board.kicad_sch').resolve())]
    step=Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261011\\continuation-r2\\SAFE-exploratory-native-trial-r9\\step_measure_all_native_r3.sh')
    measure=['C:/Program Files/Git/usr/bin/sh.exe',str(step),candidate.resolve().as_posix(),OUT.resolve().as_posix(),project.resolve().as_posix()]
    baselines={
      'dc936':(HERE/'field-power-native-trial-r1/field-power-native-trial.kicad_pcb',HERE/'field-power-native-trial-r1/measure/partitions.json'),
      '1beb':(HERE/'combined-reset-cm-native-r5-cache-refresh/combined-reset-cm-cache-refreshed.kicad_pcb',HERE/'combined-reset-cm-native-r5-cache-refresh/measure/partitions.json'),
      'r07':(Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb'),Path('Z:/pcb-runs/claude-finish/integrate/measure/r07-ripup-signals-1/partitions.json')),
      'r06':(Path('Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb'),Path('Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2/partitions.json')),
      'c9':(HERE/'cap-signal-native-r1/cap-signal-host-only.kicad_pcb',HERE/'cap-signal-native-r1/measure/partitions.json')}
    pinned=[Path(__file__),STAGE/'receipt.json',STAGE/'construction.json',STAGE/'native-parity.json',candidate,fresh,wrapper,step,Path(prefix[3]),Path('Z:/pcb-runs/claude-finish/tools/net_partitions.py'),Path('Z:/pcb-runs/claude-finish/tools/step_summary.py')]
    pinned.extend([Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261011\\continuation-r2\\native_final_partitions_contract_r2.py'),Path('C:\\Users\\Gluis\\OneDrive\\Documents\\ChatGPT\\Controller\\reports\\board-finish-20261011\\continuation-r2\\SAFE-exploratory-native-trial-r9\\native-postfill-via-obligations.json'),Path('Z:\\pcb-runs\\claude-finish\\tools\\step_measure.sh')])
    for bp,pp in baselines.values():pinned.extend([bp,pp])
    pinned.extend(p for p in project.rglob('*') if p.is_file());pinned.extend(p for p in copy.rglob('*') if p.is_file())
    pins.update(sourcepins);pins.update({str(p.resolve()):sha(p) for p in pinned});check(pins)
    write(OUT/'inputs.json',{'pins':pins,'commands':[export,measure],'source_matching_stem_root_bytes_exact':True,'new_heavy_slots':0,'project_rule_sha256':sha(project/'board.kicad_dru'),'source_fresh_sha256':sha(fresh)})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];env['HEAVY']='heavy.sh'
    state('MATCHING_STEM_FRESH_SOURCE_EXPORT')
    with (OUT/'matching-stem-export.log').open('w',encoding='utf-8') as log:exp=subprocess.run(export,env=env,stdout=log,stderr=subprocess.STDOUT)
    check(pins)
    if exp.returncode:raise ValueError('Matching stem schematic export failed')
    sys.path.insert(0,str(BASE/'parity-repair'))
    from host_parity import load_parser
    from fresh_export import canonical
    parser=load_parser(BASE/'parity-repair/root106/tools/netlist_parity.py')
    expected=canonical(parser['read_netlist'](fresh));actual=canonical(parser['read_netlist'](OUT/'matching-stem-fresh.net'))
    if actual!=expected:raise ValueError('Matching root filename changes source semantics')
    write(OUT/'matching-stem-source-proof.json',{'verdict':'PASS','export_sha256':sha(OUT/'matching-stem-fresh.net'),'source_sha256':sha(fresh),'exact_canonical_components_raw_net_attributes_and_pin_membership':True})
    state('NATIVE_FULL_REFILL_DRC_RUNNING',candidate_sha256=sha(candidate))
    with (OUT/'measure.log').open('w',encoding='utf-8') as log:run=subprocess.run(measure,env=env,stdout=log,stderr=subprocess.STDOUT)
    check(pins)
    if run.returncode:raise ValueError('Native measurement tool failed: '+str(run.returncode))
    actual_contract=json.loads((OUT/'actual-full-refill-contract.json').read_bytes())
    if actual_contract['verdict']!='PASS_ACTUAL_FULL_NATIVE_FILL_ALL_CU_AND_EXPLICIT_FLASH_CONTRACT' or actual_contract['postfill_Cu_or_flash_errors']:raise ValueError('Actual full native Cu/flash contract failed')
    if actual_contract['candidate_sha256']!=sha(candidate):raise ValueError('Actual full native geometry belongs to a different candidate')
    summary=json.loads((OUT/'summary.json').read_bytes());after=json.loads((OUT/'partitions.json').read_bytes())
    if after['sha256']!=sha(candidate) or not after['refilled'] or summary['board_sha256']!=sha(candidate):raise ValueError('Native receipts stale')
    netlist=parser['read_netlist'](fresh)
    current=C.inventory(candidate.read_bytes());changed_pads=set();changed_ledger=[]
    # Native API binds exact source nets. Identify only original source pad reassignment.
    old_board=C.inventory(baselines['c9'][0].read_bytes())
    for uid,ch in old_board[3].items():
        if C.pcbtext.chunk_kind(ch)!='footprint' or current[3].get(uid)==ch:continue
        roots=[parser['sexpr_parse'](s.decode()) for s in [ch,current[3][uid]]]
        props={p[1]:p[2] for p in parser['children'](roots[0],'property')}
        ref=props['Reference'];seen=collections.Counter();maps=[]
        for root in roots:
            mapping={}
            for pad in parser['children'](root,'pad'):
                puid=parser['atom'](pad,'uuid');net=parser['child'](pad,'net')
                mapping[puid]={'number':pad[1],'net':net[1] if net else ''}
            maps.append(mapping)
        if set(maps[0])!=set(maps[1]):raise ValueError('Original physical pad inventory changed')
        for pad in parser['children'](roots[0],'pad'):
            puid=parser['atom'](pad,'uuid');pin=pad[1];name=ref+'.'+pin+'#'+str(seen[pin]);seen[pin]+=1
            oldpad,newpad=maps[0][puid],maps[1][puid]
            if oldpad['number']!=newpad['number']:raise ValueError('Original physical pad number changed')
            if oldpad['net']!=newpad['net']:
                changed_pads.add(name);changed_ledger.append({'physical_pad_uuid':puid,'partition_pad':name,'before_net_raw':oldpad['net'],'after_net_raw':newpad['net']})
    if len(changed_ledger)!=14:raise ValueError('Unexpected original source pad-reassignment count')
    relation_proofs={}
    for role,(bp,pp) in baselines.items():
        before=json.loads(pp.read_bytes())
        if before['sha256']!=sha(bp) or not before['refilled']:raise ValueError('Baseline native partitions stale')
        relation_proofs[role]=old_relationships(before,after,changed_pads)
    guard_spec=importlib.util.spec_from_file_location('frozen_partition_guard',BASE/'gate-repair/partition_guard.py');guard=importlib.util.module_from_spec(guard_spec);guard_spec.loader.exec_module(guard)
    selected=['/motherboard_compute/CM_CAN_SPI_SCLK','/motherboard_compute/CM_CAN_SPI_MOSI','/FPGA_CRESET_N']
    selected_proofs={}
    for role,(bp,pp) in baselines.items():
        before=json.loads(pp.read_bytes())
        def subset(d):
            nets={n:d['nets'][n] for n in selected};missing=sum(len(v)-1 for v in nets.values())
            return {'sha256':d['sha256'],'refilled':True,'nets':nets,'pad_island_joins':missing,'api_unconnected_count':missing}
        selected_proofs[role]=guard.compare(subset(before),subset(after))
    drc=json.loads((OUT/'drc.json').read_bytes());log=(OUT/'drc.log').read_text(errors='replace')
    parity='NOT_EXECUTED' if 'Failed to fetch schematic netlist' in log or 'Schematic parity tests require' in log else 'MATCHING_STEM_CANONICAL_SOURCE_AVAILABLE; native CLI completion must be assessed from report and log'
    record={'verdict':'NATIVE_COMPLETE_SOURCE_TRANSITION_CONTINUITY_REVIEW_OPEN','candidate_sha256':sha(candidate),'actual_full_refill_contract':actual_contract,'actual_full_refill_contract_sha256':sha(OUT/'actual-full-refill-contract.json'),'actual_full_refill_geometry_sha256':sha(OUT/'actual-full-refill-geometry.json'),'actual_full_refill_via_flashes_sha256':sha(OUT/'actual-full-refill-via-flashes.json'),'summary':summary,'unchanged_original_pad_relationships':relation_proofs,'selected_CM_MOSI_RESET_exact_net_guards':selected_proofs,'exact14_source_reassigned_pad_ledger':changed_ledger,'source_reassigned_pad_relationships_require_new_power_design_verification':True,'cli_schematic_parity_execution':parity,'cli_schematic_parity_diagnostics':drc.get('schematic_parity'),'original_DRC_rules_exact_prefix_with_only_scoped_PG_rule_appended':True,'controlled_terminal_profile_installed':False,'adopted':False,'manufacturing_ready':False}
    write(OUT/'receipt.json',record)
    state('COMPLETE_REVIEW_OPEN',summary=summary)
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        if OUT.exists():state('FAILED',reason=str(e))
        raise
