"""Save the current continuation, preserving prior evidence and live board."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write_new(p,d):
    assert not p.exists();p.write_text(json.dumps(d,indent=1)+'\n',encoding='utf-8')
def main():
    previous=H/'checkpoint-r8.json';c=read(previous)
    live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
    assert sha(live)==c['live_r07_sha256']
    c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(previous)
    paths=[H/'field-power/local-and-b5-return-audit-r25/receipt.json',H/'field-power/additive-ground-b5-native-recipe-r27/receipt.json',H/'sbc-power/five-core-and-b5-checkpoint-r32/receipt.json',H/'sbc-power/five-core-and-b5-checkpoint-r32/model.pkl',H/'ao1-native-diagnostic-r1/receipt.json',H/'ao1-native-diagnostic-r1/scoped-native-fill/receipt.json',H/'coupled-recovery/ao1-native-com-reference-independent-r2.json',H/'coupled-recovery/ao1-native-com-boundary-and-gap-diagnostic-r3.json',H/'field-signed-group-bounds-r2-r25/receipt.json',H/'protected24-dogbones-r7/receipt.json',H/'protected24-dogbones-r7/proposed-discrete.pkl',H/'protected24-dogbones-r7/proposed-zones.pkl',H/'protected24-dogbones-r7/owned-new-return-zone-updates.pkl',H/'field-power/field-supply-census-r40/receipt.json',H/'compose_protected24_joint_r1.py',H/'stage_joint_power_native_r1.py',H/'measure_joint_power_native_r1.py']
    # Preserve the exact actually named boundary diagnostic instead of guessing
    # a filename if the recovery agent emitted a differently named resource.
    if not paths[7].exists():
        matches=[p for p in (H/'coupled-recovery').glob('*r3.json') if 'native' in p.name and 'com' in p.name and read(p).get('native_jobs',0)==0]
        paths.pop(7)
        for p in matches:
            if p not in paths:paths.append(p)
    for p in paths:assert p.is_file(),str(p)
    field=read(paths[0]);protected=read(H/'protected24-dogbones-r7/receipt.json');ao=read(H/'ao1-native-diagnostic-r1/scoped-native-fill/receipt.json')
    assert field['verdict'].startswith('PASS_')
    c['field_local_return_gate']={'verdict':field['verdict'],'new_vias':field['new_vias'],'new_segments':field['new_segments'],'source_root_status':field['source_root_status'],'strong_SMD_all_drill_edge_guard_mm':.275,'trace_floor_mm':.20,'receipt_sha256':sha(paths[0]),'B5_all_four_named_groups_rooted_host':True,'R27_F_In4_native_flash_obligations_bound':True,'existing_LOGIC_187_In3_flash':'Prospective; native fresh-fill required','final_CORE_protected_coupled_signal_walls_current_and_native_gates':'OPEN','adopted':False}
    c['protected24_constructor']={'revision':'R7','receipt_sha256':sha(H/'protected24-dogbones-r7/receipt.json'),'complete':True,'new_vias':protected['new_vias'],'new_stubs':protected['new_stubs'],'new_bridges':protected['new_inner_source_bridges'],'bounded_negatives':len(protected['remaining']),'target_rows':len(protected['rows']),'independent_R19_audit_session':47847,'latest_R32_joint_rebase_session':60942,'protected_current_authority':'57-term exact-output ledger; constructor connector current metadata is not an output allocation','native_current_and_full_mutual_contact_gates':'OPEN','board_written':False,'native_jobs':0,'adopted':False}
    c['AO_scoped_native_diagnostic']={'candidate_sha256':read(H/'ao1-native-diagnostic-r1/receipt.json')['candidate_sha256'],'selected_COM_zones':8,'post_fill_all_Cu_errors':len(ao['all_discrete_post_fill_errors']),'geometry_sha256':ao['geometry_sha256'],'actual_flash_sha256':ao['actual_via_flashes_sha256'],'scope':'Only eight selected AO1_COM zones freshly refilled; all other zone fills unvalidated. Independent native COM source/paired-return topology retains checked relationships; two tiny new SDI gaps remain in R18. R19 shifts two F intermediate points25um and is being audited. Whole-board continuity/DRC/SI/electrical gates OPEN.','adopted':False}
    c['continuing_work']={
      'field_power':'R25 corrected25-via/108-track host local+B5 gate passes; B5 four named groups rooted. Remaining4 FA/2 FB ground groups need scoped signal-wall repairs. U11015 ILIM/DVDT/ground repair remains diagnostic; C10036 ground/gate candidate is under independent audit. Actual FIELD5 and A3/B3/BDO3 regulated supplies have further disconnected groups; construction continues with exact source ports.',
      'SBC_power':'Five CORE physical feed proposals frozen in R32 8bd79b82 plus current B5. Fresh complete graph corrects planner count:15 unrooted named groups/30pads remain, including two candidate target clusters still detached. Source/annulus attachment diagnosis prioritized; no contact/source PASS. CORE ded2b949 carve and all prior feeds preserved.',
      'analog':'R18 scoped native eight-COM-zone refill complete. Five stale SDI cache voids healed; two tiny actual SDI F gaps remain outside the transition disk. A25um intermediate-node correction is being audited on actual native source-rooted COM. Original local SCLK reference unchanged; tiny contour boundary set differences documented without waiver.',
      'protected_24V':'R7 complete12 ordinary vias/12stubs/10In1 bridges with no target negatives. Independent R19 mutual/source/contact gate and replay onto newer R32 CORE/B5 running; original outlines and existing Cu unchanged. Root57term output-current allocation authority retained; no equal-sharing, barrel, mesh, thermal or native acceptance.',
      'r06_recovery':'Latest completed full native trial remains1beb, with12 unchanged-r06 losses. Native dc936 full DRC pending; its fresh partitions have explicit CORE/IO3/SBC loss closure obligations.',
      'power_connector':'CM harness/contact/ground allocation proposal remains separate and unadopted; module mechanics/RF/hot current qualification OPEN.'}
    c['field_signed_current_group_map']=read(H/'field-signed-group-bounds-r2-r25/receipt.json')
    c['running_native_field_trial']['state']=read(H/'field-power-native-trial-r1/measure/status.json')
    folder=H/'resource-monitor-r11';samples=[json.loads(s) for s in (folder/'resource-samples.jsonl').read_text().splitlines()]
    c['resource_watches']['resource-monitor-r11']={'status':read(folder/'resource-status.json'),'samples_at_checkpoint':len(samples),'cpu_max_percent':max(x['cpu_percent'] for x in samples),'GPU_max_C':max(x['gpu_c'] for x in samples),'GPU_max_W':max(x['gpu_w'] for x in samples),'breach_samples':sum(bool(x['breached']) for x in samples),'last_sample':samples[-1]}
    c['evidence_sha256'].update({str(p.resolve()):sha(p) for p in paths});write_new(H/'checkpoint-r9.json',c)
    docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
    for p in docs:
        target=H/('checkpoint-r9-before-'+p.name);assert not target.exists();target.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(target.resolve()),'sha256':sha(target)}
    status=read(docs[0]);status['continuation_r9']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    note=('Continuation checkpoint '+c['utc']+'\n\nR25 corrected local+B5 host gate passes (25vias/108tracks); all four B5 named groups rooted, four FA and two FB ground groups remain. Protected24 R7 finished12vias/12stubs/10In1 bridges, no target negatives; independent host audit and latest CORE/B5 joint replay running. Five CORE physical feeds frozen; fresh full graph corrects earlier planner count to15 unrooted named groups/30pads, two attachments under diagnosis. AO R18 source/API and scoped eight-COM-zone refill complete, paired returns/source topology preserved; two tiny SDI gaps need the R19 node correction. Regulated field supplies and local walls still being routed. Latest completed full native board remains1beb:1354missing/1365API/0ordinary errors/186warnings,12r06 losses. dc936 full DRC pending. Resource watch R11 active through01:38UTC; original live source unchanged. No adoption/fabrication release. See continuation-r2/checkpoint-r9.json.\n')
    docs[1].write_text(note,encoding='utf-8');old=docs[2].read_bytes();i=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:i]+insert+old[i:])
    assert sha(live)==c['live_r07_sha256']
    write_new(H/'checkpoint-document-receipt-r9.json',{'backups':backups,'after':{str(p.resolve()):sha(p) for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
    print(json.dumps({'checkpoint':str(H/'checkpoint-r9.json'),'protected_constructed':len(protected['rows']),'field_gate':field['verdict'],'native_DRC':c['running_native_field_trial']['state']['phase'],'live_unchanged':True}))
if __name__=='__main__':main()
