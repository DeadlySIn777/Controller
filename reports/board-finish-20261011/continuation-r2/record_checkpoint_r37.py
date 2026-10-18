"""Preserve current continuation evidence; never replace the live board."""
import datetime,hashlib,json,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
prior=H/'checkpoint-r36.json';c=read(prior);live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');assert sha(live)==c['live_r07_sha256'];c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(prior)
c['continuing_work'].update({
 'native_zone_overlaps':'R687 adds exactly two declared B3 intent corner triangles totaling1.063455996793e-6 mm², changing only one vertex by(-1,+1)nativeIU. Literal old-intent loss and physical excess EMPTY; new true guards/nozone/intersection0. All current physical roles, filled arrays, h/g/pads/drills/holes byte-identical, so R645 source/contact/reference scopes rebind by identity. Sparse distinct-outer native recipe frozen; native adoption/fill/current of added intent OPEN.',
 'Q0_DIC':'Shielded Q0 R526/R536 remains scoped PASS/native-current open. R550 constructive locked G0FAULT F detour plus legal .90–1.0 DIC pair initially left a target reference void from the abandoned new55ab cutter. R552 proved exact new55ab absent original eedf, retired only its three cutter families and restored only portions also inside the exact pre-DIC source primitive. Every current filled array retained literally as prefix and all unrelated arrays/roles/header/FP untouched. Restored In1/In4 fragments each.865951475588mm² are actual J1-rooted with0 prior source-key loss. R554 route successor source, contact, strict reference and new body gates RUNNING/OPEN; no model adoption.',
 'CORE_current':'R371/R373/R379 remote IO3 plus positive LG shadow recipe remains sparse/no-hole/source-preserving/nativeAPI scoped PASS. R381 freezes R7035 CRCW0603680RFKEA680Ω0603/source nets IO_3V3 and ENC3_A_P/two pad UUIDs/four old contacts. R382791 small translations no legal pose. R383 two genuinely rotated180° poses (+1.5X,-.3 or-.4Y) have whole-pad actual source support and courtyard/Cu clearance but direct reconnect stubs fail. R38426 reference-constrained reconnect targets no legal Froute. Wider genuine pose search continues under all old-Cu/source/ref hard guards; zero adoption. Earlier14 CORE5 body refs/CORE93/R7/current/native FAILs remain.',
 'U10003_native_after_binding':'R276 exact R155/R157 parent header plus only ROOT13tracks4via6FLTdeletes/R10007native pose/twoFGzones is frozen b1d133c5. It does NOT overlay older R253 whole-header Q0/DIC/core operations. R277 actual R157 full-native five-net BEFORE cache is frozen with LG/FG actual R663 and freshIO3/HOST/FLT groups/alldrills/masks. R278 actual after5-net source/contact/strict oldlines/body/caps/fourordinarypairs/nativeSMD support auditor prepared, not yet executed. R279 actual selected source gains versus full actual native foreign fills/owner local spacing and exact gain coverage prepared; R280 fresh actual native HOST575 finite sameIn4 transfer with literal.005 body guards prepared. All consume actual native R275 outputs only; raw witness not auto-waived. Native R275 three-net fill remains active main1.'})
paths=[
 'field-power/R645-B3-positive-intended-one-corner-qualified-sparse-native-recipe-r687/receipt.json',
 'coupled-recovery/DIC-policy-pair-two-locked-G0-FAULT-tracks-r550/receipt.json',
 'coupled-recovery/DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/receipt.json',
 'sbc-power/CM79-R371-exact-additive-nine-IO3-tracks-one-LG-full-profile-handoff-r379/receipt.json',
 'sbc-power/CM79-R371-R7035-exact-source-native-Cu-and-local-reference-scope-r381/receipt.json',
 'sbc-power/CM79-R371-R7035-small-genuine-rigid-translation-old-terminal-stubs-new-ordinary-return-nomination-r382/receipt.json',
 'sbc-power/CM79-R371-R7035-small-genuine-rigid-translation-old-terminal-stubs-new-ordinary-return-nomination-r383/receipt.json',
 'R275-exact-R155-parent-plus-only-ROOT-native-header-context-r276/receipt.json',
 'R275-exact-R155-parent-plus-only-ROOT-native-header-context-r276/context.pkl',
 'R275-actual-R157-fresh-five-net-BEFORE-cache-r277/receipt.json',
 'audit_ROOT_R275_actual_five_net_native_source_r278.py',
 'audit_ROOT_R275_actual_source_gain_foreign_Cu_r279.py',
 'audit_ROOT_R275_HOST575_actual_finite_source_r280.py']
for name in paths:
 p=H/name;assert p.is_file(),name;c['evidence_sha256'][str(p.resolve())]=sha(p)
for rev in ('r32','r33'):
 folder=H/('resource-monitor-'+rev);p=folder/'resource-status.json'
 if p.exists():
  samples=[json.loads(x)for x in(folder/'resource-samples.jsonl').read_text().splitlines()];c['resource_watches'][folder.name]={'status':read(p),'samples_at_checkpoint':len(samples),'cpu_max_percent':max(x['cpu_percent']for x in samples),'GPU_max_C':max(x['gpu_c']for x in samples),'GPU_max_W':max(x['gpu_w']for x in samples),'breach_samples':sum(bool(x['breached'])for x in samples),'last_sample':samples[-1]}
 else:c['resource_watches'][folder.name]={'scheduled':read(folder/'prior-watch-receipt.json')}
c['native_scope_jobs']={}
for key,pid,needle in [('R157_full_CLI',54240,'R155-known-reference-native-diagnostic-r157/measure/drc.json'),('R667_selected_ground',55204,'native_R157_selected_three_ground_landing_fill_r667.py'),('R275_root_selected',79128,'native_joint_selected_LG_FG_IO3_fill_r275.py')]:
 try:
  process=psutil.Process(pid);args=process.cmdline();assert needle.lower()in' '.join(args).replace('\\','/').lower();c['native_scope_jobs'][key]={'PID':pid,'create_time':process.create_time(),'CPU_seconds':sum(process.cpu_times()[:2]),'affinity':process.cpu_affinity(),'cmdline':args,'running':process.is_running()}
 except psutil.NoSuchProcess:c['native_scope_jobs'][key]={'PID_completed_before_snapshot':pid,'outputs_need_inspection':True}
fresh(H/'checkpoint-r37.json',c);docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r37-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
status=read(docs[0]);status['continuation_r37']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
note='Continuation '+c['utc']+'\n\nContinuing saved Claude work. Live R07 is unchanged. The B3 intended corner has a scoped source-preserving correction, exact old physical copper and source arrays unchanged. The DIC route repair now restores only the abandoned trial cutter within its original source and is being checked with a locked original-signal detour. The encoder pull-up move remains a search: two real poses clear pads and courtyard, but reconnect routes still fail; no pose accepted. ROOT native selected fill is bound to the exact R157 parent plus only its sparse patch, and actual before/after connectivity, reference, source-gain foreign clearance and finite HOST return checks are prepared. The full R157 CLI and separate field and ROOT selected fills continue on their existing slots. All native/current/CORE source failures remain visible; no board adoption or manufacture release. CPU70%/GPU80C350W alarms remain armed and scheduled. See continuation-r2/checkpoint-r37.json.\n'
docs[1].write_text(note,encoding='utf-8');old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256'];fresh(H/'checkpoint-document-receipt-r37.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False});print('R37_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
