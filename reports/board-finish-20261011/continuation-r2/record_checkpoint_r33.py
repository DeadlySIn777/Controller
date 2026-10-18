"""Preserve new scoped evidence, raw failures and the continuing native job."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
prior=H/'checkpoint-r32.json';c=read(prior)
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
assert sha(live)==c['live_r07_sha256']
c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(prior)
c['continuing_work'].update({
 'TMR_native_keepout':'R218 selected FA/IO3 C++ refill completed, clone6befbca6; all86396 tracks/8006 vias retained. R5630f693990 actual all8535 drills: IO3 source594/21groups and FA47/4, R515/R155 sourcekeys/prior groups0loss,605 genuine BEFORE fill-to-native-metal contacts0loss, R14045 exact8rooted, old498 actualIn2 annulus.2119457436mm2. Repaired27 intended outlines and both owned physical/intended roles clear. STRICT native no-zone FAIL remains: ORIGINAL IO3 zone54921f4b touches closed native triangle boundary y130.35 with15.677012mm LineString; area-zero is not waived. No whole-board DRC/current/adoption credit.',
 'FIELD5':'R543474949d4 preserves original IO3 while completing all9FIELD5 host targets through139.287897mm/.50 In2 feed. R545327869c6 all old groups/10prior sourcekeys/50directFGcontacts0loss,19true geometry checks/native nozone0. All3ground source-constituent In1/In4 UUID/layer/WKBsets exact;12 raw nonempty ref differences retained as FAIL. R547a37acbb6 independent identical BEFORE primitive controls establish no incremental reference-set change without geometry/area waiver. R55198294873 contained-sheet.36A/25um/125C conditional feed.07376/.10653V for .05/.025meshes (~10%gridchange), barrel.001015V. NewFIELD5 cachedIn1 fullbody gap28.70499mm2 remains; upstream/return/plating/thermal/current/native open.',
 'U10003':'R21780c1819d exact rational closed-set arrangement of all5 bbox-selected actual J3In1 source arrays over six oldref witnesses:328points0real loss; omitted all157 pieces exact bbox-bound byR216. Independently reviewed including zero-dimensional boundaries; scoped supplement only, R199rawFAIL and other reference/native/current gates retained. R220eee449f4 twelve rigid R10007 logic-side poses have actual LGIn4 full-pad refs and real ground B reconnects. R225a1c4c584 complete56-key HOSTgroup B-target search all12finite poses no signal route; R224 binds complete source not earlier cropped witness. R226 existing actual two-plane LG-return ordinary HOST B/F port screen running; no footprint/Cu edits or adoption.',
 'CORE_current':'R332 In1 andIn4 full1.25 alternatives zero routes; R331c401779c56realLGports/721legal ordinary endpoints/zero detached-right fullwidthF spurs into actual In2 source-component. R333ce105c4f minimal CM49 replay onto exactR543/TMR-repairedhead f9df6606:115tracks34vias0deletes, exactR515q4f before roles asserted; no whole older head/role/fill overlay. Next necessary attributed q4f-only owned corridor. All old/native/source/ref/current/rawFAIL gates remain.',
 'Q0_DIC':'R450681b07ac materially different saved-work recovery:22tracks/3ordinaryvias, R10016 rigid(-.5,-.5), ONLY4olddeletes(GATE9963/ff87,SENSE6faa/7b). Every original POWER/FLT item retained. Q0 F/In3/F7.693mm; SENSEF/In2/F25.922mm between original1730/5a barrels with exact oldB terminal subsets/naturalF/Bflags retained. Ordinary Q0returnpairs.97949/.95 nominal source pass; scoped SAME_PLANE In1 and independent full source/contact/ref/current/native proof OPEN. RejectedR426/R442 losses preserved. ThreeDICordinaryreturn failures still held.',
 'native':'Full R157 native3e6b099d still runs on its original shared slot; R218 selectedFA/IO3 native complete with scopedR563 source/contact proof and original boundary nozoneFAIL. R113 failedR9 still499cappedunconnected/0parity/1ordinaryTMRerror298warnings; no savedfillednativeCu. LiveR07/nativeparent untouched; no manufacturing release.'})
c['evidence_scope_correction']={'prior_checkpoints_preserved':True,'R517_R368_cached_physical_net_dictionary_entries':78,'prior_R31_R32_all81_wording_incorrect_for_this_field_cache':True,'not_an_all2388_net_recomputation':True,'remaining_exact_unchanged_net_identity_and_new_hole_disjointness_required':True,'R563_selected_native_check_is_only_FA_and_IO3_not_fullboard':True}
c['root_running_constructor'].update({'TMR_R218_R563':'SELECTED_NATIVE_SOURCE_CONTACT_PASS_ORIGINAL_BOUNDARY_LINESTRING_NOZONE_FAIL','FIELD5_R543_R551':'HOST_SOURCE_CONTACT_PASS_FEED_CONDITIONAL_REFERENCE_RETURN_CURRENT_NATIVE_OPEN','U10003_R217':'EXACT_INDIVIDUAL_SOURCE_NO_LOSS_SCOPED_SUPPLEMENT_INDEPENDENTLY_REVIEWED','U10003_R220_R225_R226':'12POSES_GROUND_B_PASS_HOST_B_NO_ROUTE_ORDINARY_HOST_B_F_PORT_SCREEN_RUNNING','Q0_R450':'SAVED_GATE_SENSE_EXISTING_BARREL_ALTERNATIVE_CONSTRUCTED_FULL_GATES_OPEN','CM_R331_R333':'56REAL_PORT_721ENDPOINT_CENSUS_NO_ROUTE_CURRENT_FIELD_MINIMAL_REPLAY_COMPLETE_COUPLED_Q4F_NEXT','resource_R30_R31':'R30ACTIVE_TO203510UTC_R31SCHEDULED203500UTC'})
paths=[
 'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218/receipt.json',
 'field-power/TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r563/receipt.json',
 'field-power/FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/receipt.json',
 'field-power/FIELD5-R543-full-exact-net-source-contact-reference-geometry-r545/receipt.json',
 'field-power/FIELD5-R545-identical-reference-primitive-paired-before-controls-r547/receipt.json',
 'field-power/FIELD5-R543-actual-source-Cu-finite-target-annulus-contained-sheet-r551/receipt.json',
 'U10003-old-reference-exact-all-source-rational-arrangement-r217/receipt.json',
 'U10003-R10007-shared-return-logic-side-source-reference-rigid-pose-nomination-r220/receipt.json',
 'R10007-complete-actual-SDI-B-source-r224/receipt.json',
 'U10003-R10007-source-reference-B-complete-source-reconnection-nomination-r225/receipt.json',
 'coupled-recovery/Q0-saved-GATE-SENSE-existing-barrels-r450/receipt.json',
 'sbc-power/CM79-external-full1p25-F-spur-exact-old-Cu-novel-margin-nominations-r331/receipt.json',
 'sbc-power/CM79-external-larger-power-port-full1p25-In4-actual-source-route-nominations-r332/receipt.json',
 'sbc-power/CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333/receipt.json',
 'screen_R10007_HOST_existing_return_B_F_ports_r226.py']
for name in paths:
 p=H/name;assert p.is_file(),name;c['evidence_sha256'][str(p.resolve())]=sha(p)
for rev in ('r29','r30','r31'):
 f=H/('resource-monitor-'+rev);p=f/'resource-status.json'
 if p.exists():
  xs=[json.loads(x)for x in(f/'resource-samples.jsonl').read_text().splitlines()]
  c['resource_watches'][f.name]={'status':read(p),'samples_at_checkpoint':len(xs),'cpu_max_percent':max(x['cpu_percent']for x in xs),'GPU_max_C':max(x['gpu_c']for x in xs),'GPU_max_W':max(x['gpu_w']for x in xs),'breach_samples':sum(bool(x['breached'])for x in xs),'last_sample':xs[-1]}
 else:c['resource_watches'][f.name]={'scheduled':read(f/'prior-watch-receipt.json')}
c['native_jobs_snapshot']={n:read(H/n)for n in ['R155-known-reference-native-diagnostic-r157/measure/status.json','R9-failed-flash-native-DRC-diagnostic-r113/status.json','FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218/status.json']}
fresh(H/'checkpoint-r33.json',c);docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r33-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
s=read(docs[0]);s['continuation_r33']=c;s['updated_utc']=c['utc'];docs[0].write_text(json.dumps(s,indent=2)+'\n')
note='Continuation '+c['utc']+'\n\nClaude saved work continued; live R07 unchanged. R218 selectedFA/IO3 native refill completed; R563 source594IO3/47FA and605 genuine older fill-metal contacts pass, but ORIGINAL IO3 zone touches closed TMR boundary as15.677mm LineString: strict nozoneFAIL retained. FIELD5R543 all9targets/older contacts pass; return/fullbody/native/current remain open. Q0R450 reuses savedGATEdetour and existingSENSEbarrels, preserves allPOWER/FLTCu; independent gates open. CM49 sparse replay ontoR543 preserves exactTMRrepair; ownedq4f corridor next. R10007 twelve supported poses have ground reconnects; complete HOST B-source finite route fails, ordinary B/F port search runs. R217 exact allsource rational arrangement independently closes only six oldref witness false losses; rawFAILs preserved. Correction: fieldR517cachednet dictionary has78entries, not81as stated in prior notes. FullR157 native continues unchanged. CPU70%/GPU80C350W R30alarm active/R31scheduled, four allocatedKiCadslots/12CPU cap unchanged. No adoption/fabrication release. See continuation-r2/checkpoint-r33.json.\n'
docs[1].write_text(note);old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256']
fresh(H/'checkpoint-document-receipt-r33.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
print('R33_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
