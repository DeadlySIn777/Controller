"""Preserve scoped progress, exact failed receipts and unchanged live board."""
import datetime,hashlib,json,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
prior=H/'checkpoint-r34.json';c=read(prior);live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');assert sha(live)==c['live_r07_sha256'];c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(prior)
c['continuing_work'].update({
 'TMR_native_keepout':'R613 actual selected native R587 proof PASS: IO3 594 source pads / 21 groups, FA47 / 4; R515/R155/R218 source keys and actual old groups preserved, both 605 direct-contact sets retained. Physical and intended no-zone hits zero. Only original5492 outline correction; all original Cu/source/profile/settings held. Exact sparse replay onto current native head and full-board qualification still open.',
 'native_zone_overlaps':'R631 minimal four same-net/profile unions kept all original Cu and unrelated arrays. Fresh R635 all78 old relationships,147 direct touches,11 source banks zero loss; literal old routed reference FAIL for LGc02cc590 and FG04a66006/568f24b5. R637 attributes exact integer-corner losses. R639 explicitly declared positive corner additions proposed; true foreign guards/source/ref/native not yet qualified. R631/R635 remain diagnostic and failed; no native stage.',
 'U10003':'R605 finite .20/.005 same-In4 path qualifies exact original HOST .575 own terminal scope, native/current/SI remain open. R243 two source-seeded FG roles and R245 per-net drilled bodies passed their local nomination. R246 rebuilds joint repair freshly from cleanR262:13tracks/4ordinaryvias/6exact original FLT replacements and restores original CLOCK track. R247 explicitly binds raw boolean precision, no hidden global regrid/native emission credit. Fresh R248 current source/contact/reference audit is running. Its geometry found one HOST segment .271189 guarded drill gap vs .275 required. R250 local five-micrometre bend of two NEW HOST segments passes discrete/all-hole/rule screen; fresh joint fill/ref/native audit remains required.',
 'Q0_DIC':'R492/R494 provenance defect retained: wrapper audited R478 rather than R488. R496 corrected exact current check. R504 current model f738f9a4 has independent R506 all81/source/reference incremental PASS, R508 six-role/direct320/exterior-empty PASS and R510 exact finite same-plane path binding. R512 sparse22track/3via/4originaldelete/native recipe frozen with locked=yes on two GATE replacements; actual locking API gate open. R516 no-hole FGIn1 1.666336mm2 positive shielding covers BOTH moved R10016 pads and overlaps actual J3 source. Only NEW protectedFA7ef role must retreat; legal joint composition/source/direct/ref/current/native open. DIC three-return fix remains.',
 'CORE_current':'R353 current CORE5 large-port route nomination rejected by fresh R354: actual old IO3 3689-key group splits,1484 old source keys detached. All2388 other-net checks/direct old contacts/strict old routed refs/actual retained full1.25 anchors retain zero incremental loss, but14 raw NEW body reference failures remain. R355 diagnoses source2205/detached1484 and existing native port candidates, no-hole actual IO3 bypass search underway. No whole stale overlay or adoption.',
 'native':'R157 pinned FULL refill completed:1188 unconnected/1177 joins, geometry421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b. ALL22 postfill contract errors are missing original-parent via actual In1/In4 flashes; original discrete Cu exact. Full native CLI DRC measurement still running under original wrapper. No adoption. R587 selected native completed. Four allocated KiCad slots total and12 eligible CPU cap unchanged. LiveR07 unchanged; no fabricated/manufacturing release.'})
c['physical_census_correction']={'R368_and_R517_cached_physical_net_count':78,'ALL81_other_Q0_audit_scope':'separate actual78 plus affected3, not81 cached graphs'}
paths=[
 'field-power/original-IO3-TMR-R587-fresh-native-completed-proof-r613/receipt.json',
 'field-power/ROOT-HOST-original575-exact-own-guard-same-In4-finite-source-r605/receipt.json',
 'field-power/four-minimal-owned-unions-actual-all-drill-source-contact-reference-r635/receipt.json',
 'coupled-recovery/Q0-exact-scoped-current-native-recipe-r512/receipt.json',
 'coupled-recovery/Q0-R504-explicit-final-current-r506/receipt.json',
 'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354/receipt.json',
 'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r246/receipt.json',
 'U10003-HOST-field-joint-current-exact-raw-precision-bound-r247/receipt.json',
 'HOST-two-new-segment-single-bend-minimal-drill-guard-nominations-r250/receipt.json',
 'U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r248/true-copper-new-incremental-analytic-errors.json',
 'audit_U10003_HOST_joint_actual_fresh_r248.py',
 'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-contract.json',
 'R155-known-reference-native-diagnostic-r157/measure/partitions.json']
for name in paths:
 p=H/name;assert p.is_file(),name;c['evidence_sha256'][str(p.resolve())]=sha(p)
for rev in('r31','r32'):
 f=H/('resource-monitor-'+rev);p=f/'resource-status.json'
 if p.exists():
  xs=[json.loads(x)for x in(f/'resource-samples.jsonl').read_text().splitlines()];c['resource_watches'][f.name]={'status':read(p),'samples_at_checkpoint':len(xs),'cpu_max_percent':max(x['cpu_percent']for x in xs),'GPU_max_C':max(x['gpu_c']for x in xs),'GPU_max_W':max(x['gpu_w']for x in xs),'breach_samples':sum(bool(x['breached'])for x in xs),'last_sample':xs[-1]}
 else:c['resource_watches'][f.name]={'scheduled':read(f/'prior-watch-receipt.json')}
c['native_jobs_snapshot']={'R157':read(H/'R155-known-reference-native-diagnostic-r157/measure/status.json')}
c['native_jobs_snapshot']['R157_postfill_contract']=read(H/'R155-known-reference-native-diagnostic-r157/measure/actual-full-refill-contract.json');c['native_jobs_snapshot']['R157_original_filler_process_completed']=not psutil.pid_exists(78640)
fresh(H/'checkpoint-r35.json',c);docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r35-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
s=read(docs[0]);s['continuation_r35']=c;s['updated_utc']=c['utc'];docs[0].write_text(json.dumps(s,indent=2)+'\n')
note='Continuation '+c['utc']+'\n\nClaude saved work continues; the live R07 board remains unchanged. The original IO3 outline repair passed selected native fill, source and both 605-contact checks. The four plane unions retain source contacts but still lose three strict old trace references; explicitly bounded corner additions are under review. Q0 source/contact checks pass on its exact current model, but both moved resistor pads still need the nominated no-hole FG shield and legal protected-power retreat. CORE5/CM79 is rejected because it splits the old IO3 group; an existing-port bypass is being searched. The fresh joint U10003/HOST audit is running. One new HOST bend misses the planner drill margin; a 5 um local bend passes its discrete screen and needs a fresh fill/reference check. The pinned full native refill finished with 1188 unconnected items / 1177 joins; all 22 postfill contract errors are lost original In1/In4 via flashes, requiring real plane repairs. Full CLI DRC is still measuring. CPU 70% and GPU 80 C/350 W alarms remain armed, with four KiCad slots and the 12-CPU cap unchanged. No adoption or fabrication release. See continuation-r2/checkpoint-r35.json.\n'
docs[1].write_text(note);old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256'];fresh(H/'checkpoint-document-receipt-r35.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False});print('R35_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
