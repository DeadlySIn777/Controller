"""Save actual native completion, loss census and running continuation."""
import datetime,hashlib,json,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
prior=H/'checkpoint-r37.json';c=read(prior);live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');assert sha(live)==c['live_r07_sha256'];c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(prior)
c['continuing_work'].update({
 'field_native_selected':'R667 actual selected LG/FG/FB CPP fill COMPLETE, receipt295628230c4f177383160514f061929a4e17a460f55a929c8bb705ccf508402e; actualgeometry583183a5. All discrete post-fill errors0 and prior actual R157 ground FlashLayer losses0. This is not automatic credit for all original23 layer flags or finite landing/source/contact/reference/current: R669 fresh actual all-drilled audit RUNNING and must decide those independently. No save/adoption/full-native unselected qualification.',
 'field_signed_current':'R693 maps all75 FB signed current terms and152 endpoint choices to actual J11005.2, all663 contact ports/420 plated ports retained. R695 complete solve failed KCL .00390625, preserved. R697 explicitly omits1.26e-11 mm² of14 numerical In1 triangles (actual Cu never trimmed) and strict KCL1.2627e-8 yields conditional hot25umCu/20umplating/125C return drop.194055V; an ordinary .5/.2 old7a9206b1 barrel at47.748/206.5 carries up to3.3571A fromIn4 toB. R699 independent review explicitly does NOT upper-bound physical electrode voltage or barrel current and does NOT qualify combined positive-feed+return .48policy, current/material/thermal/contact/fault remainOPEN. Exact-source parallel-stitch reinforcement and unchanged-matrix diagonal scaling are next; no equalsharing/rating assumption.',
 'actual_remaining_connections':'R282 exact full native census:1188API unconnected,1177 pad-island joins across745 splitnets;550nets needonejoin,106 nearest-common-surface pairs≤5mm. This is a candidate ranking, not route/current proof. R287 rebinds original17 r07 losses to actual R157 native partitions:6 original relationships recovered,11 remain, zero original pad-net authority changes. Remaining DI6,DI15,PEN_ENABLE,AO1_ENABLE,OBS34_A,DOB_FLT_HOST,XF_REQUEST,DOA_Q0,DOA_SDO,AO1_VREF,AO1_DAC_CS. New host packets not credited until native remeasurement.',
 'ROOT_actual_postfill_continuation':'Independent R691 static review68a85577 freezes corrected R278/279/280; R281 supervisor waits exact original R275 PID/create/cmdline then runs those host audits sequentially with all scripts/inputpins, affinity16-27/BelowNormal/numerical2. No extra native job/save/adoption. R275 still actual LG/FG/IO3 main1 fill; original full R157 CLI still shared1. R284 and R285 bounded no-via .20 STEP8/HDMI screens both foundno route; correctedfillreader failureR283 preserved. R285 retains all real Cu/planner025/drill275/sourcewholebody constraints while removing unrequested source025 navigation margin. R286 actual endpoints all source-supported/foreign-copper-axis legal; fixed existing walls disconnect the bounded free regions, no oldCu carve/borrowed cap/phantom source.',
 'CORE_current':'R38567 real R7035 legal source-supported poses. R38634 fullIO3 F paths but no complete F ENC3 reconnect after1004 attempts; no pose adopted. R387 exact original JD12.B3 pad16e8ee74 at81.047/21.2 has actual all-drilled Cu onIn2/In3/B. One ordinary ENC3 signal dive paired with existing real two-plane LG return is being screened; R371 remote no-holeIO3 bridge and all earlier CORE14body/CORE93/R7/current/native failures retained.',
 'Q0_DIC_latest':'R554 constructive10track/3newvia pose successor and R556 minimalcurrent model95d1636e frozen. R558 six literal extra-negative primitive/reserve witnesses preserved rawFAIL; padrecord source reader failed and was fixed inR560. Exact STRtree direct-contact broadphase R562 completes82 cached/current net plus coupledG0FAULT scopes with0 lost oldphysical groups and165 truegeometry checks0errors; source/direct/strict full-dimension oldreference/newbody/scope witness results still closing. No native/adoption; Q0R526/R536 scoped recipe retained.'})
paths=[
 'field-power/R157-minimal-local-three-ground-landings-selected-native-r667/selected-ground-fill/receipt.json',
 'field-power/R157-actual-FBG-complete-signed-real-barrel-mesh-input-r693/receipt.json',
 'field-power/R157-actual-FBG-explicit-stable-numerical-subset-full-signed-current-r697/receipt.json',
 'field-power/R157-full-FBG-conditional-current-independent-review-and-reinforcement-obligation-r699/receipt.json',
 'field-power/ROOT-R278-R279-R280-corrected-independent-static-review-r691/receipt.json',
 'R275-pinned-actual-native-postfill-audit-continuation-r281/launch-and-inputs.json',
 'R157-actual-native-remaining-pad-joins-same-surface-census-r282/receipt.json',
 'R157-two-actual-no-via-surface-signal-bridge-constructive-screen-r283/failure.json',
 'R157-two-actual-no-via-surface-signal-bridge-constructive-screen-r284/receipt.json',
 'R157-two-actual-no-via-surface-signal-bridge-constructive-screen-r285/receipt.json',
 'R157-two-no-via-signal-terminal-actual-source-and-Cu-blockers-r286/receipt.json',
 'original-r07-seventeen-lost-joins-actual-native-R157-residual-r287/receipt.json',
 'sbc-power/CM79-R371-R7035-valid-rigid-poses-actual-network-terminal-source-reference-route-nominations-r386/receipt.json',
 'sbc-power/CM79-R371-ENC3-actual-existing-lower-layer-source-port-attribution-r387/receipt.json',
 'resource-watch-arm-derivation-r34.json']
for name in paths:
 p=H/name;assert p.is_file(),name;c['evidence_sha256'][str(p.resolve())]=sha(p)
for rev in ('r32','r33','r34'):
 folder=H/('resource-monitor-'+rev);p=folder/'resource-status.json'
 if p.exists():
  samples=[json.loads(x)for x in(folder/'resource-samples.jsonl').read_text().splitlines()];c['resource_watches'][folder.name]={'status':read(p),'samples_at_checkpoint':len(samples),'cpu_max_percent':max(x['cpu_percent']for x in samples),'GPU_max_C':max(x['gpu_c']for x in samples),'GPU_max_W':max(x['gpu_w']for x in samples),'breach_samples':sum(bool(x['breached'])for x in samples),'last_sample':samples[-1]}
 else:c['resource_watches'][folder.name]={'scheduled':read(folder/'prior-watch-receipt.json')}
c['native_scope_jobs']={}
for key,pid,needle in [('R157_full_CLI',54240,'R155-known-reference-native-diagnostic-r157/measure/drc.json'),('R275_root_selected',79128,'native_joint_selected_LG_FG_IO3_fill_r275.py')]:
 try:
  process=psutil.Process(pid);args=process.cmdline();assert needle.lower()in' '.join(args).replace('\\','/').lower();c['native_scope_jobs'][key]={'PID':pid,'create_time':process.create_time(),'CPU_seconds':sum(process.cpu_times()[:2]),'affinity':process.cpu_affinity(),'cmdline':args,'running':process.is_running()}
 except psutil.NoSuchProcess:c['native_scope_jobs'][key]={'PID_completed_before_snapshot':pid,'outputs_need_inspection':True}
c['native_scope_jobs']['R667_selected_ground']={'native_CPP_complete':True,'native_receipt_SHA256':sha(H/paths[0]),'actual_audit_R669':'RUNNING'}
fresh(H/'checkpoint-r38.json',c);docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r38-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
status=read(docs[0]);status['continuation_r38']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
note='Continuation '+c['utc']+'\n\nSaved Claude work continues; live R07 is unchanged. The separate ground-landing native fill has completed with0 discrete-copper errors and0 prior actual ground-mask losses; its actual finite source/contact/reference audit is running. Full native R157 remains1188 unconnected/1177 pad-island joins across745 splitnets. Six of the original17 r07 lost relationships are recovered in that native candidate;11 remain and are listed exactly. The conditional full signed FB return solve identifies a3.3571A ordinary barrel obligation; its .194055V return number is not a physical bound or a complete .48V rail-policy pass. A source-preserving parallel reinforcement is next. ROOT selected native fill and original full CLI DRC continue; reviewed actual postfill audits are pinned to run after the original ROOT fill exits. The encoder pull-up now has an actual lower-layer source for one paired dive after F-only attempts failed. DIC all82 oldgroup/165geometry scopes pass so far; remaining raw scope/reference/body gates retained. R33 CPU70%/GPU80C350W alarm active, R34 scheduled with10second overlap. No board adoption or fabrication release. See continuation-r2/checkpoint-r38.json.\n'
docs[1].write_text(note,encoding='utf-8');old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256'];fresh(H/'checkpoint-document-receipt-r38.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False});print('R38_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
