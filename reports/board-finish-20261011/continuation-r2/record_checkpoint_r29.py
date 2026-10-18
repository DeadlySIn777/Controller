"""Persist continuation and newly identified failures without adopting a board."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
prior=H/'checkpoint-r28.json';c=read(prior)
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
assert sha(live)==c['live_r07_sha256']
c['previous_checkpoint_sha256']=sha(prior);c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
c['continuing_work'].update({
 'field':'R393 FIELD5 In2 replacement preserved direct sources but R395 failed original IO3 group3689 split3306+383 source keys,58 named pads;29 strict old references failed. R407 corrects only new FIELD5 gap to.625094458 without fixing source split. R423 original-rim restoration/R429 scoped source audit has all old LG/FG/FB contacts/direct sources intact,9FIELD5 rooted,FG/FB references0loss but21LG strict gaps. R431 distinguishes8 broadphase false positives with EXACT EMPTY direct formula from13 actual direct remainders totaling.0001411186958636mm2, all failures retained. R435 In3-only and R437 existing-barrel In3/In2 bridge no-path with original IO3 actualfill hard. Immutable-parent scoped replay underway; no accepted combined successor. U10009 R411 one-barrel feed roots targets but R419 loses24LGsourcekeys/203oldreferences. R433/R441 source-annulus finite alternatives no-path, R443 exact signed lower VS cut bound[0,2.008]A conditional; no current/thermal qualification. Four regulated pads still bare.',
 'U10003':'R153 original scoped source/contact pass retained but full-body reference failed. R176 diagnostic adds one ordinary signal via and one ground via,4track replacement of only2prospective In2 tracks,2FGplanes replacing2prospective roles,zero old actualfill edits and all originalB/In3/vias unchanged. New plane intentions/source seeded, inherited9physical-outside-intention failures retained. Supplemental exact R179 flags return distances.8266869/1.321091mm outside saved.90-1.0; R177 finds no legal ground via near new signal axis in finite search. R180 missing module path failed, fresh R181 fixed imports and B-only original-port-to-real-pad route no nominee. No adoption/integration/native job for these candidates.',
 'Q0_DIC':'Q0 R348 nominal legal Cu ports/actualFGreturns.97949/.94202 nonetheless fail frozen SBC5V no-track/no-via B reservation. R354 preserves failure and confirms all3DICport existing compliant LGreturns counts0/0/0. Existing ground reconnection,GATE andFstems retained as partial evidence; legal ports and three DIC return relocations underway. Exact R179 supplemental ledger binds3DICdesignated pairs.824996/.828431/.819985 outside saved.90-1.0 rule; original receipts unchanged, no exemption.',
 'CORE_current':'CM R283/R28449of51actual source rooted/115.20Ftracks34ordinaryvias scope no incremental old contact/reference or native-rule geometry loss;85raw new-body reference failures remain. R289 sparse currentR393 rebase inherits IO3 split/reference failures. Full-width CORE5 corridor for CM79 remains blocked; exact own CM49 barrel coupled relocation work ongoing without reservation waiver or width reduction. CORE full-body93.041959mm2raw gap/35mV/current/ROOT42/fullnative gates remain unfinished.'})
c['root_running_constructor'].update({'FIELD5_R393_R423_R429':'FAILED_IO3_383_SOURCE_SPLIT_AND_13_DIRECT_LG_REFERENCE_REMAINDERS_NO_ADOPTION','U10009_R411_R419':'FAILED_24_LG_SOURCE_SPLIT_203_OLD_REFERENCE_ROWS','Q0_R348_R354':'FAILED_FROZEN_SBC5V_TRACK_AND_VIA_KEEP_OUT_NEW_PORT_SEARCH','DIC_U10003_R179':'EXACT_SAVED_OPERATOR_RETURN_WINDOW_FAILURE_SUPPLEMENTAL_NO_RECEIPT_REWRITE','U10003_R176_R177_R181':'FAILED_RETURN_WINDOWS_NO_FINITE_B_ONLY_ALTERNATIVE','resource_R26_R27':'R26ACTIVE_TO163550UTC_R27SCHEDULED163540UTC'})
fragments=['FIELD5-R393-current-independent-all-contact-source-reference-audit-r395','FIELD5-R393-only-new-plane-margin-and-native-boundary-correction-r407','FIELD5-R385-minimal-R155-strict-aggregate-boundary-cut-rim-restoration-r423','FIELD5-R423-original-rim-fresh-drilled-source-reference-gate-r429','FIELD5-R423-remaining-strict-reference-rim-attribution-r431','FIELD5-inner-source-barrel-In3-only-original-IO3-preserving-replacement-nomination-r435','FIELD5-existing-ordinary-barrel-In3-In2-original-IO3-hard-nomination-r437','U10009-source-component-guided-nonempty-ordinary-landing-nomination-r441','U10009-exact-lower-VS-one-barrel-cut-signed-current-bound-r443','Q0-B-port-and-DIC-existing-return-diagnosis-r354','CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289','saved-operator-return-window-supplemental-failure-r179','U10003-preserved-branch-exact-two-port-reference-construction-r176','U10003-exact-actual-paired-new-signal-port-sub-mm-paired-return-faces-r177','U10003-B-only-fault-source-pad-nomination-r181']
all_receipts=list(H.rglob('receipt.json'))
for fragment in fragments:
 ps=[p for p in all_receipts if p.parent.name==fragment];assert len(ps)==1,(fragment,ps)
 c['evidence_sha256'][str(ps[0].resolve())]=sha(ps[0])
for rev in ['r26','r27']:
 f=H/('resource-monitor-'+rev);status=f/'resource-status.json'
 if status.exists():
  xs=[json.loads(x) for x in(f/'resource-samples.jsonl').read_text().splitlines()]
  c['resource_watches'][f.name]={'status':read(status),'samples_at_checkpoint':len(xs),'cpu_max_percent':max(x['cpu_percent']for x in xs),'GPU_max_C':max(x['gpu_c']for x in xs),'GPU_max_W':max(x['gpu_w']for x in xs),'breach_samples':sum(bool(x['breached'])for x in xs),'last_sample':xs[-1]}
 else:c['resource_watches'][f.name]={'scheduled':read(f/'prior-watch-receipt.json')}
c['native_jobs_snapshot']={}
for n in ['R155-known-reference-native-diagnostic-r157/measure/status.json','R9-failed-flash-native-DRC-diagnostic-r113/status.json']:
 p=H/n
 if p.exists():c['native_jobs_snapshot'][n]=read(p)
fresh(H/'checkpoint-r29.json',c)
docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r29-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
s=read(docs[0]);s['continuation_r29']=c;s['updated_utc']=c['utc'];docs[0].write_text(json.dumps(s,indent=2)+'\n')
note=('Continuation '+c['utc']+'\n\nClaude saved work continued; liveR07 unchanged. Current R157 exact-source/allCu diagnostic full nativefill and originalR113 fullCLI still running on existing slots without stop/restart. FIELD5 In2 repaired nominal margin but IO3 loses383sourcekeys; structural original-record replay underway for13actualLGreference remnants. U10009 target-rooted diagnostic loses24LGsourcekeys/203oldreference rows and finite alternatives remain no-path. CM49/51actualgrounds rooted;2hardpads/fullbodyreference/current remain. Saved operator.90-1.0mm return window adds explicit3DIC and U10003diagnostic failures, no exemptions or rewritten historical receipts. Q0 earlier ports violate frozenBno-via rule; legal coupled ports underway. Four regulated pads bare, CORE93mm2reference/current/ROOT42/native qualification incomplete. CPU70%/GPU80C350W alarms R26active/R27scheduled, fourKiCadslots/12CPUcap unchanged. No adoption or fabrication release. See continuation-r2/checkpoint-r29.json.\n')
docs[1].write_text(note);old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:])
assert sha(live)==c['live_r07_sha256']
fresh(H/'checkpoint-document-receipt-r29.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
print('R29_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
