"""Continue saved work; bind completed native/host evidence without adoption."""
import datetime,json,hashlib,psutil
from pathlib import Path
H=Path(__file__).resolve().parent; B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists(); p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
prior=H/'checkpoint-r38.json'; c=read(prior)
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
assert sha(live)==c['live_r07_sha256']; c['previous_checkpoint_sha256']=sha(prior); c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
c['continuing_work'].update({
 'ROOT_actual_postfill_continuation':'R275 actual selected LG/FG/IO3 native fill COMPLETE. R281 reviewed pinned postfill chain COMPLETE. R278: zero oldgroup/direct/source-key/newbody/ordinary-return/moved-SMD/terminal/prior-mask losses, HOST groups2→1, LG94→93, FG30→29; 1871 literal strict old-reference losses remainFAIL. R279:315 source-gain guards,281 failures and9 literal owner-coverage failures held against full-before foreign filled Cu. Candidate-wide all-net refill required, no selected-cache/full-array substitution. R280 actual HOST original .575 aperture finite same-In4 SOURCE transfer PASS: whole.20body on actualJ1, sourceboundarygap.030627mm/capgap.0063838mm. R289 exact decimal circles/Fraction coordinate authority certifies all14 checked bodies without expanded polygon caps; parent failures remain.',
 'field_native_selected':'R667 selectedLG/FG/FB COMPLETE; R669 all23 missing-layer contacts/22 oldbarrels now source-rooted with no old source-key/group/direct/prior-actual-mask losses. 1832 strict oldref losses and15 source-fill-loss layer ledgers remainFAIL. R709 exact attribution:245 foreign arrays FULL-before→BLANK-selected-after,197 selectedground arrays changed outside local landing windows. This requires one full all-net refill; no fill-array substitution or raw waiver.',
 'field_signed_current':'R715 adds exactly one .8/.4 ordinary FBG via at47.948/204.2 and one .5 B stub; R719 prospective group/ref audit and R723 exact128cap all-drilled stub directsource support pass. R721 inscribed-vs-round body rawFAIL and In4 gap preserved separately. R727 byte/source/tree consistent. R729 same75signed terms/152endpointchoices/212unitresponses, KCL1.27069e-8A. Conditional oldbarrel3.35708→1.28753A/newbarrel2.20683A/remainingordinarymax2.32999A; return.194055→.191517V. Same explicit numerical-subset omissions; no physical upperbound, barrel rating, material/convergence/native or combined.48V loop pass. Minimal full FIELD native replay manifest next.',
 'Q0_DIC_latest':'Q0R536 scoped sparse recipe preserved. DICR562 checks83 scopes (82 zone plus coupled G0FAULT),0oldrelationship/source/strictoldreference/newbody failures/165truegeometry0. Six raw Boolean negative-scope witnesses stayFAIL; R564 exact binary64 Fraction arrangement proves zero operational outside individual-cut/reserve points, no tolerance/grid waiver. R566 minimal locked2oldG0track+8unacceptednewDICtrack+3newvia replacement packet with Q0/R552 dependencies frozen. DI6R578 adds only10newtracks/2newordinaryvias, three fill families receive exactnormalantipads/remove-only cuts. R58084oldrelationship/89geometry gates pass so far, source/target/newbody/references still closing; no native/adoption credit.',
 'CORE_current':'R398 real R7035 180-degree root81.147/27.7 plus5new.20tracks/3new.5/.2vias; ordinary ENCpair81.0/28.8→81.95/28.8 and IO3endpointpair83.675/23.877276→old3945@84.15/24.7 both.95mm. R7036 unchanged. R399 actual native pad UUIDs/rawnets/pose/masks PASS, R400 changed3source-bank oldkeys/groups0loss and6otherbanks exact/hole-disjoint; R401 resumes indexed oldref checks only. Minimal native dependencies R379nineIO3/oneLG plusR398. R390 CORE5 handoff16exacttracks/14rawgaps sum70.439157mm² distinct from older wholeCORE93.041959mm²; ROOTR290 actual fullnative In1 shadow blocker screen in progress. No source carve/overlay adoption.'})
paths=[
 'R275-actual-selected-native-five-net-source-body-reference-audit-r278/receipt.json',
 'R275-actual-source-gains-versus-full-before-native-foreign-filled-Cu-r279/receipt.json',
 'R275-HOST575-fresh-actual-native-In4-finite-source-transfer-r280/receipt.json',
 'R275-pinned-actual-native-postfill-audit-continuation-r281/receipt.json',
 'R275-actual-source-body-exact-named-circular-cap-authority-r289/receipt.json',
 'field-power/R667-actual-native-three-ground-local-landings-source-contact-reference-r669/receipt.json',
 'field-power/R667-original-native-fill-array-and-locality-attribution-r709/receipt.json',
 'field-power/R157-high-current-FBG-actual-source-parallel-stitch-nomination-r715/receipt.json',
 'field-power/R715-FBG-parallel-stitch-actual-baseline-source-reference-independent-r719/receipt.json',
 'field-power/R715-new-stub-explicit-round-cap-direct-source-supplement-r723/receipt.json',
 'field-power/R715-round-stub-exhaustive-byte-bindings-and-returned-tree-consistency-r727/receipt.json',
 'field-power/R715-one-prospective-barrel-full-signed-explicit-numeric-subset-redistribution-r729/receipt.json',
 'coupled-recovery/DIC-R562-literal-subtraction-scope-arrangement-r564/receipt.json',
 'coupled-recovery/DIC-policy-coupled-exact-sparse-host-scope-supplement-r566/receipt.json',
 'sbc-power/CM79-R397-exact-five-tracks-three-ordinary-vias-R7035-real-pose-r398/receipt.json',
 'sbc-power/CM79-R398-native-R7035-real-pose-three-via-mask-readonly-r399/receipt.json']
for name in paths:
 p=H/name; assert p.is_file(),name; c['evidence_sha256'][str(p.resolve())]=sha(p)
c['native_scope_jobs']={}
try:
 proc=psutil.Process(54240); args=proc.cmdline(); assert 'R155-known-reference-native-diagnostic-r157/measure/drc.json'.lower() in ' '.join(args).replace('\\','/').lower()
 c['native_scope_jobs']['R157_full_CLI']={'PID':54240,'create_time':proc.create_time(),'CPU_seconds':sum(proc.cpu_times()[:2]),'affinity':proc.cpu_affinity(),'cmdline':args,'running':proc.is_running()}
except psutil.NoSuchProcess: c['native_scope_jobs']['R157_full_CLI']={'PID_completed_before_snapshot':54240,'outputs_need_inspection':True}
c['native_scope_jobs']['R275_root_selected']={'native_CPP_complete':True,'postfill_chain_R281_complete':True,'no_full_board_or_adoption_credit':True}
c['native_scope_jobs']['R667_selected_ground']={'native_CPP_complete':True,'actual_audit_R669_complete_raw_FAIL_retained':True,'no_full_board_or_adoption_credit':True}
for rev in ('r33','r34'):
 folder=H/('resource-monitor-'+rev); p=folder/'resource-status.json'
 if p.exists():
  samples=[json.loads(x)for x in(folder/'resource-samples.jsonl').read_text().splitlines()]
  c['resource_watches'][folder.name]={'status':read(p),'samples_at_checkpoint':len(samples),'cpu_max_percent':max(x['cpu_percent']for x in samples),'GPU_max_C':max(x['gpu_c']for x in samples),'GPU_max_W':max(x['gpu_w']for x in samples),'breach_samples':sum(bool(x['breached'])for x in samples),'last_sample':samples[-1]}
 else: c['resource_watches'][folder.name]={'scheduled':read(folder/'prior-watch-receipt.json')}
fresh(H/'checkpoint-r39.json',c); docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md']; backups={}
for p in docs:
 q=H/('checkpoint-r39-before-'+p.name); assert not q.exists(); q.write_bytes(p.read_bytes()); backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
status=read(docs[0]); status['continuation_r39']=c; status['updated_utc']=c['utc']; docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
note='Continuation '+c['utc']+'\n\nSaved Claude revisions continue; live R07 unchanged. R275 and R667 selected native fills are complete. Fresh ROOT source/group/new-body/ordinary-return gates pass; actual HOST finite original-aperture return and all14 exact-circle body caps pass. Literal oldreference/sourcegain and full-versus-selected foreign-fill conflicts remainFAIL pending combined all-net refill. Field one-via/one-stub reinforcement reduces conditional overloaded-barrel current3.357→1.288A; current/thermal/complete loop qualification remainsopen. DIC83oldrelationship scopes pass and exact scope/sparse supplement is frozen; DI6 new10track/2via source audit closes next. Actual R7035 movedpose/pad/via API checks pass, R7036 unchanged, saved encoder/source gates pass so far. CORE5 actual In1 positive-shadow blockers are being checked against saved16track/14gap handoff. Native R157 remains1188unconnected/1177pad-island joins and11originalr07losses remain. Original fullnativeCLI is uninterrupted. CPU70%/GPU80C350W alarms retained withR34scheduled. No adoption/fabrication release. See continuation-r2/checkpoint-r39.json.\n'
docs[1].write_text(note,encoding='utf-8'); old=docs[2].read_bytes(); at=old.find(b'\n')+1; insert=('\n'+note+'\n').encode(); docs[2].write_bytes(old[:at]+insert+old[at:]); assert sha(live)==c['live_r07_sha256']
fresh(H/'checkpoint-document-receipt-r39.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
print('R39_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
