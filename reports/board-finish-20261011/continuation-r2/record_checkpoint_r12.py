"""Preserve the continuing board work and exact scoped evidence."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
previous=H/'checkpoint-r11.json';c=read(previous)
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');assert sha(live)==c['live_r07_sha256']
c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(previous)
c['continuing_work']={
 'CORE':'R48 full guarded projection and independent R54 root all ten new branch target sets and retain earlier CORE source contacts. Exactly U9001.10/R17031.1/U11007.6 remain detached. R38 historical census correction:13groups21pads, not20pads.',
 'protected24':'R9 completed four replacements preserving12vias12stubs/six held bridges. Both protected sources root every named pad:FA47/FB44. Independent R2 fails retained LOGIC/FAG/FBG group splits and four plane-to-discrete gaps, including the prospective CORE placeholder disposition; final latest CORE composition/outward guards and existing-annulus ground restoration remain pending.',
 'field':'U11015 exact R48 native recipe and LOGIC R57 outward-bound host contact/clearance repair pass. Regulated R41 proposal remains unqualified; full final10 protected hard screen finds three proposed regulated via/plane conflicts now explicitly relocated with own stubs. C reference protected R62 mask retained. No uncorrected R41 emission.',
 'IO3':'Selected native R2 exact two-owned-track replacement/one via/two tracks/one IO3 plane passes source/allCu/API/settings/rings and independent fresh-selected source pair/annulus. Wholeboard final contact/DRC/current pending.',
 'C10036':'R24 coupled6existingtrack-delete/6track2via1FBGplane addition passes independent host R30. Frozen native ledger R32 staged on eedf clone9910b29; source/all86161tracks7909vias/raw/IU/API pass, .25 local zone settings/rings and selected FBG native refill pass. Independent actual-native reference/source/annulus review running; other power proposals excluded.',
 'signal_recovery':'AO19 local native proof retained with85inherited boundary slivers open. DI6 exact current source ordinary escape nomination avoids withheld114.65/119.45 via and keeps fault copper intact; rooted fullbody reference/contact/native gates pending.',
 'final_tools':'SBC settings-aware canonical new-zone union R55/projection R58/emitter R57 prepared. Explicit differing-settings and old-native same-priority conflicts must be resolved; full native stager needs coupled owned removals and perzone declared settings. All full-board no-loss/current/refill/DRC gates remain open.'}
c['corrected_CORE_checkpoint']={'model_sha256':'3e4e42806786d7d15f66f8029f674db50c4df235adcea16d2f5d7a19b7757baa','ten_new_branch_target_source_membership':'PASS_R54','prior_non_target_source_contacts':'PASS_R54','remaining_unrooted_named_pads':['U9001.10','R17031.1','U11007.6'],'earlier_R38_census_correction':'13groups21pads;20was arithmetic error','full_mutual_current_and_native':'OPEN'}
c['protected_R9']={'receipt_sha256':sha(H/'protected24-on-corrected-core-r9/receipt.json'),'model_sha256':'a2b249dee9bf6b7672fbafdcfee602bfc6be47e6690c360aef0a42a5c923763b','completed_positive_planes':10,'ordinary_vias_and_stubs':[12,12],'actual_protected_FA_FB_rooted_named_pads':[47,44],'independent_host_audit':'FAIL_RETAINED_GROUND_SPLITS_AND_FOUR_PLANE_GAPS','return_restoration':'PREPARED_NOT_RUN','current_native_final':'OPEN'}
c['root_running_constructor']={'R9':'COMPLETE_UNADOPTED','R10':'INTENTIONALLY_STOPPED_NO_ACCEPTED_GEOMETRY','C10036_selected_native':'COMPLETE_INDEPENDENT_REFERENCE_OPEN','alarm_R13':'SCHEDULED_02:38UTC'}
c['IO3_scoped_native_diagnostic']=read(H/'io3-native-diagnostic-r2/independent-selected-IO3.json')
c['C10036_scoped_native_diagnostic']=read(H/'c10036-native-diagnostic-r1/receipt.json')
paths=[H/p for p in ['protected24-on-corrected-core-r9/receipt.json','protected24-r9-independent-joint-audit-r2/receipt.json','sbc-power/remaining-core-feeds-r48/receipt.json','sbc-power/core-source-walls-and-protected-second-r54/receipt.json','field-power/logic-outward-guard-repair-r57/receipt.json','field-power/regulated-peer-reference-protected-base-r62/receipt.json','coupled-recovery/c10036-r24-independent-complete-r30.json','coupled-recovery/c10036-native-owned-ledger-r32/receipt.json','c10036-native-diagnostic-r1/native-zones.json','c10036-native-diagnostic-r1/scoped-native-fill/receipt.json','c10036-native-diagnostic-derivation-r1.json','resource-monitor-r13/prior-watch-receipt.json']]
assert all(p.exists() for p in paths);c['evidence_sha256'].update({str(p.resolve()):sha(p) for p in paths})
for name in ('resource-monitor-r12','resource-monitor-r13'):
 f=H/name;s=f/'resource-status.json';row={'status':read(s) if s.exists() else read(f/'schedule-status.json')}
 sp=f/'resource-samples.jsonl'
 if sp.exists():
  xs=[json.loads(x) for x in sp.read_text().splitlines()]
  if xs:row.update(samples_at_checkpoint=len(xs),cpu_max_percent=max(x['cpu_percent'] for x in xs),GPU_max_C=max(x['gpu_c'] for x in xs),GPU_max_W=max(x['gpu_w'] for x in xs),breach_samples=sum(bool(x['breached']) for x in xs),last_sample=xs[-1])
 c['resource_watches'][name]=row
put(H/'checkpoint-r12.json',c)
docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backs={}
for p in docs:
 q=H/('checkpoint-r12-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backs[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
s=read(docs[0]);s['continuation_r12']=c;s['updated_utc']=c['utc'];docs[0].write_text(json.dumps(s,indent=2)+'\n')
note=('Continuation checkpoint '+c['utc']+'\n\nLatest completed full-board trial dc936 remains FAILED:11ordinary errors,1357missing joins,1382uncappedAPI,258warnings,0parity. Protected R9 roots all47FA/44FB pads, but independent audit finds ground splits/four plane gaps. Ten CORE branches now source-rooted; only U9001.10/R17031.1/U11007.6 remain. Historical CORE38 census corrected to13groups21pads. LOGIC R57 host guards/contacts pass. IO3 selected native and independent actual-source annulus pass. C10036 exact coupled R24/R30 host pass; native clone9910b29 source/allCu/settings/selected FBG refill pass, independent actual reference review pending. Regulated proposal final10 screen identified3proposed via conflicts for relocation. Latest CORE/protected/field composition and all full-board current/reference/no-loss/DRC gates open. CPU/GPU alarms unchanged: R12 through02:38UTC,R13 automatic rearm scheduled. Claude/live/source originals preserved; no adoption or fabrication release. See continuation-r2/checkpoint-r12.json.\n')
docs[1].write_text(note);old=docs[2].read_bytes();i=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:i]+insert+old[i:]);assert sha(live)==c['live_r07_sha256']
put(H/'checkpoint-document-receipt-r12.json',{'backups':backs,'after':{str(p.resolve()):sha(p) for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
print(json.dumps({'checkpoint':str(H/'checkpoint-r12.json'),'live_unchanged':True,'latest_full_native_gate':'FAIL11','protected_targets_rooted':[47,44]}))
