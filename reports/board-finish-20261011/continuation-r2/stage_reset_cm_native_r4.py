"""Compose exact reset aperture and independently audited coupled CM repair."""
import datetime,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import native_pose_signal_contract as H
from shapely.ops import unary_union
C=H.C
OUT=HERE/'combined-reset-cm-native-r4'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_raw(raw):return hashlib.sha256(raw).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    if OUT.exists():raise ValueError('Fresh combined candidate required')
    prior=HERE/'combined-power-source-native-r3-c92'
    pins=json.loads((prior/'inputs.json').read_bytes())
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Frozen prior input changed: '+p)
    receipt=json.loads((prior/'receipt.json').read_bytes())
    if receipt['verdict']!='PASS_SOURCE_NATIVE_API_AND19_POSES':raise ValueError('Native parent rejected')
    parent=prior/'combined-power-source-c92-corrected.kicad_pcb'
    raw=parent.read_bytes();iv=C.inventory(raw)
    old_path=HERE/'ground-escape-audit-r7/audit.json'
    reset_path=HERE/'reset-smd-aperture-audit-r8/audit.json'
    old_reset=json.loads(old_path.read_bytes());reset=json.loads(reset_path.read_bytes())
    if reset['verdict']!='HOST_READY_NATIVE_ELECTRICAL_OPEN' or reset['errors'] or reset['existing_plane_contacts_removed']:raise ValueError('Strengthened reset audit rejected')
    for p,h in reset['inputs'].items():
        if sha(p)!=h:raise ValueError('Frozen reset input changed: '+p)
    reset_old={r['uuid']:r['raw_chunk'].encode() for r in old_reset['new_items']}
    reset_new={r['uuid']:r['raw_chunk'].encode() for r in reset['new_items']}
    if len(reset_old)!=16 or len(reset_new)!=16 or any(iv[4].get(u)!=ch for u,ch in reset_old.items()):raise ValueError('Owned old reset16 differs')
    cmroot=HERE/'coupled-recovery'
    cmpath=cmroot/'cm-complete-independent-audit-r4-r2.json'
    cm=json.loads(cmpath.read_bytes())
    if cm['verdict']!='HOST_COMPLETE_CANDIDATE_AUDIT_PASS_NATIVE_SI_OPEN':raise ValueError('Independent coupled CM rejected')
    for key in ['pad_relationship_failures','surviving_contacts_failures','changed_item_clearance_errors','reference_errors','return_errors','controlled_bulk_and_scoped_terminal_errors']:
        if cm[key]:raise ValueError('Independent CM obligation failed: '+key)
    for p,h in cm['read_files_sha256'].items():
        if sha(p)!=h:raise ValueError('Frozen CM input changed: '+p)
    cm_source=Path('reports/board-finish-20261011/power-audit/fag-r07-repair/staged/r07-four-path-fag-repaired.kicad_pcb').resolve()
    cm_board=cmroot/'cm-coupled-returns-r4-host-only.kicad_pcb'
    if sha(cm_source)!=cm['source_sha256'] or sha(cm_board)!=cm['candidate_sha256']:raise ValueError('CM board identity differs')
    src=C.inventory(cm_source.read_bytes());ci=C.inventory(cm_board.read_bytes())
    removed=set(cm['removed_owned_uuids']);added=set(cm['added_uuids'])
    if len(removed)!=15 or len(added)!=28 or set(src[3])-set(ci[3])!=removed or set(ci[3])-set(src[3])!=added:raise ValueError('CM exact delta inventory differs')
    if src[0]!=ci[0] or src[2]!=ci[2] or any(src[3][u]!=ci[3][u] for u in set(src[3])&set(ci[3])):raise ValueError('CM mutated unowned source')
    if any(iv[4].get(u)!=src[4][u] for u in removed) or added&set(iv[3]):raise ValueError('CM operations conflict with current owned source')
    if (removed|added)&set(reset_old)|((removed|added)&set(reset_new)):raise ValueError('Owned recipe UUID overlap')
    cmchunks=[src[4][u] for u in removed]+[ci[4][u] for u in added]
    other=[]
    for u in set(src[4])|set(iv[4]):
        if u in removed or src[4].get(u)==iv[4].get(u):continue
        for inv in (src,iv):
            if u in inv[4]:other.append(inv[4][u])
    other.extend(reset_new.values())
    separation=unary_union([H.body(ch) for ch in cmchunks]).distance(unary_union([H.body(ch) for ch in other]))
    if separation<2:raise ValueError('CM repair intersects other owned changes')
    delete=removed|set(reset_old)
    additions={u:ch for u,ch in reset_new.items()}
    additions.update({u:ci[4][u] for u in added})
    retained=[ch for ch in iv[1] if C.pcbtext.chunk_uuid(ch) not in delete]
    for u in set(iv[3])-delete:
        if u in additions:raise ValueError('New UUID collides with retained item')
    result=iv[0]+b''.join(retained)+b''.join(additions.values())+iv[2];ni=C.inventory(result)
    if ni[0]!=iv[0] or ni[2]!=iv[2] or any(ni[3].get(u)!=ch for u,ch in iv[3].items() if u not in delete):raise ValueError('Unowned complete candidate entity changed')
    H.N.SourceNets(raw).assert_chunks(ni[4]);H.N.SourceNets(raw).assert_no_collisions(result)
    OUT.mkdir();candidate=OUT/'combined-reset-cm-host-only.kicad_pcb';candidate.write_bytes(result)
    copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';shutil.copy2(candidate,board)
    for ext in ['.kicad_pro','.kicad_dru']:shutil.copy2((prior/'copy/board.kicad_pcb').with_suffix(ext),board.with_suffix(ext))
    r07=C.inventory(Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb').read_bytes())
    vias=[]
    for u,ch in ni[4].items():
        if u in r07[4] or C.pcbtext.chunk_kind(ch)!='via':continue
        obj=H.F.S.overlay_tool if hasattr(H,'F') else None
        import ordinary_routes as F
        tool=F.S.overlay_tool
        vias.append({'uuid':u,'net':F.S.norm(tool.netname(ch)),'at':tool.numbers(ch,'at'),'d':tool.scalar(ch,'size'),'drill':tool.scalar(ch,'drill')})
    if len(vias)!=19:raise ValueError('Expected19 new/restored-from-r07 ordinary vias')
    spec=OUT/'native-via-spec.json';write(spec,{'board_sha256':sha(candidate),'added_vias':vias})
    prior_command=json.loads((prior/'invocation.json').read_bytes())['command']
    helper=Path(prior_command[4]);ledger=Path(prior_command[5]);parser=Path(prior_command[6])
    fresh=HERE/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net'
    command=prior_command[:4]+[str(helper),str(ledger),str(parser),str(spec.resolve()),str(board.resolve()),'--netlist',str(fresh.resolve()),'--no-connectivity','--examples','40',str((OUT/'native-parity.json').resolve())]
    extra=[Path(__file__),parent,prior/'receipt.json',old_path,reset_path,cmpath,cm_board,cm_source,cmroot/'cm-coupled-returns-r4.json',candidate,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),spec,helper,ledger,parser,fresh]
    pins.update({str(p.resolve()):sha(p) for p in extra})
    write(OUT/'inputs.json',pins)
    write(OUT/'construction.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'parent_sha256':sha(parent),'candidate_sha256':sha(candidate),'reset_old16_removed_exactly':True,'reset_new16_from_stronger_aperture_audit':True,'CM15_removed28_added_exactly':True,'unowned_top_level_entities_header_trailer_and_FPs_byte_exact':True,'CM_to_other_changed_Cu_separation_mm':separation,'original_DRC_rule_bytes_preserved':True,'terminal_controlled_rule_proposal_installed':False,'new_and_restored_via_count':len(vias),'native_refill_DRC_dual_connectivity':'NOT_EXECUTED','adopted':False})
    write(OUT/'invocation.json',{'command':command,'existing_slot':'test-only1','new_heavy_slots':0,'board_save':False,'refill':False,'DRC':False})
    env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
    with (OUT/'native.log').open('w',encoding='utf-8') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    for p,h in pins.items():
        if sha(p)!=h:raise ValueError('Native frozen input changed: '+p)
    api=json.loads((OUT/'native-parity.json').read_bytes()) if (OUT/'native-parity.json').exists() else {}
    passed=run.returncode==0 and api.get('summary',{}).get('parity_defects')==0 and api.get('source_owned_native_poses',{}).get('verdict')=='PASS' and api.get('added_via_annuli',{}).get('verdict')=='PASS'
    record={'verdict':'PASS_SOURCE_NATIVE_API_19_POSES_19_VIAS' if passed else 'FAIL_NATIVE_GATE','candidate_sha256':sha(candidate),'native_exit_code':run.returncode,'native_summary':api.get('summary'),'native_pose_count':api.get('source_owned_native_poses',{}).get('footprints'),'native_added_restored_via_count':len(api.get('added_via_annuli',{}).get('rows',[])),'refill_DRC_allnet_connectivity':'OPEN','adopted':False}
    write(OUT/'receipt.json',record);print(json.dumps(record),flush=True)
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
