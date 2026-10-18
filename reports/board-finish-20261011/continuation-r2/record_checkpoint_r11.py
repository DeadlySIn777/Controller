"""Checkpoint concrete continuation evidence without adopting a PCB trial."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write_new(p,x):
    assert not p.exists();p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
previous=H/'checkpoint-r10.json';c=read(previous)
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
assert sha(live)==c['live_r07_sha256']
c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(previous)
c['continuing_work']={
 'field_power':'R25/B5 retained. U11015 R44 exact6oldtrack removal/3ordinaryvia12segment replacement has independent physical/contact proof and R48 exact native recipe. Its outward circular antipad correction is explicit and must be replayed after final projection. R53 two planes restore six inherited LOGIC contacts; R55 full audit pending. Regulated R41 constructed20vias20stubs18planes; ten pad groups remain unjoined, final joint geometry/current/native pending.',
 'SBC_power':'R38 corrected two per-layer source attachment bugs with two ordinary .6/.3 CORE vias and short inner source bridges. All five target groups/33pads now source-rooted in full host graph;13 CORE groups/20pads remain. Native dc936 IO3/CMclock crossing is an exact two-owned-track replacement obligation; current source-connected bypass search is running. Final zone union and circumscribed antipad projector are being prepared.',
 'analog':'AO R19 exact7deleted20added Cu recipe shifts two SDI intermediate nodes25um. Native clone8ec9f37a and eight actual COM-zone refill completed; independent R4 finds0new SDI/VREF/MON reference gaps and both actual source-rooted paired returns.85 inherited strict contour boundary slivers remain explicitly open; whole-board source/DRC/current/SI/analog qualification open.',
 'protected_24V':'R7 all12dogbones retained. Independent R19 audit found FA return splits; later R32 audit found four owned protected bridges conflict with CORE. R9 constructs exact replacements on corrected R38, preserving all12vias12stubs and six other bridges; session83830 running. Return restoration R2 and actual-R9 all-zone audit R2 are prepared for its exact output. No acceptance of stale R7 geometry or ground graph.',
 'r06_recovery':'Latest completed full native trial dc936 failed11ordinary errors/5 unchanged r07,C9,1beb relationship losses/17r06 losses. Previous error-free full trial1beb remains separate, not the latest completed. C10036 exact5gate-track replacement+ordinary groundvia has physical proof; nearby rooted return requires scoped DOB_FIELD_3V3 track75409711 reroute after continuous legal-site diagnosis. No global rip-up.',
 'power_connector':'Full current reservation and source-port allocations retained; module mechanics/RF/harness contact, transient, barrel, mesh and thermal qualification remain open.'}
c.pop('running_native_field_trial',None)
c['corrected_CORE_checkpoint']={'model_sha256':'91710ee78e3b35c7903bc590292af2fd3eccbb514589fd9a7553a76772f6f4db','five_target_groups_rooted_named_pads':33,'remaining_unrooted_groups':13,'remaining_unrooted_named_pads':20,'full_mutual_current_and_native':'OPEN'}
c['AO_scoped_native_diagnostic']={'candidate_sha256':'8ec9f37a2402ca7b9f3860904534369a2def03e8ad6a2bd290c1cd828a463368','selected_COM_zones':8,'independent_R4_receipt_sha256':sha(H/'coupled-recovery/ao1-native-com-reference-independent-r4.json'),'new_full_body_reference_gaps':0,'paired_actual_source_ground_returns':'PASS_LOCAL_NATIVE','inherited_strict_boundary_slivers_open':85,'whole_board_source_DRC_current_SI_analog':'OPEN','adopted':False}
c['root_running_constructor']={'script':'reroute_protected_on_latest_core_r9.py','session':83830,'four_owned_new_positive_planes_replaced':True,'final_receipt':'PENDING','repair_protected_field_returns_r2':'PREPARED_NOT_RUN','audit_protected_joint_model_r2':'PREPARED_NOT_RUN'}
paths=[H/p for p in ['sbc-power/actual-core-cross-layer-source-bridge-r38/receipt.json','coupled-recovery/ao1-reference-coupled-r19.json','coupled-recovery/ao1-reference-coupled-r19-independent-native-bound-r19.json','coupled-recovery/ao1-native-reference-gap-diagnostic-r3.json','coupled-recovery/ao1-native-com-reference-independent-r4.json','ao1-native-diagnostic-r2/receipt.json','ao1-native-diagnostic-r2/scoped-native-fill/receipt.json','field-power/u11015-reverse-companion-repair-r44/receipt.json','field-power/u11015-native-recipe-r48/receipt.json','field-power/logic-core-split-repair-r53/receipt.json','field-power/regulated-field-source-feeds-r41/receipt.json','protected-joint-core-b5-audit-r1/receipt.json','protected24-on-corrected-core-r8-stop.json','reroute_protected_on_latest_core_r9.py','repair_protected_field_returns_r2.py','protected-joint-audit-r2-derivation.json','resource-monitor-r12/derivation.json']]
assert all(p.exists() for p in paths),[str(p) for p in paths if not p.exists()]
c['evidence_sha256'].update({str(p.resolve()):sha(p) for p in paths})
for name in ('resource-monitor-r11','resource-monitor-r12'):
    folder=H/name;row={'status':read(folder/'resource-status.json')}
    sp=folder/'resource-samples.jsonl'
    if sp.exists():
        xs=[json.loads(s) for s in sp.read_text().splitlines()]
        if xs:row.update(samples_at_checkpoint=len(xs),cpu_max_percent=max(x['cpu_percent'] for x in xs),GPU_max_C=max(x['gpu_c'] for x in xs),GPU_max_W=max(x['gpu_w'] for x in xs),breach_samples=sum(bool(x['breached']) for x in xs),last_sample=xs[-1])
    c['resource_watches'][name]=row
write_new(H/'checkpoint-r11.json',c)
docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backs={}
for p in docs:
    q=H/('checkpoint-r11-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backs[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
status=read(docs[0]);status['continuation_r11']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
note=('Continuation checkpoint '+c['utc']+'\n\nLatest completed full-board native trial dc936:1357missing joins/1382API,11ordinary errors,258warnings,0source parity;5unchanged r07/C9/1beb losses,17r06 losses. Previous zero-error full trial1beb is historical. AO19 native eight-COM-zone refill and independentR4 pass new reference/paired return checks;85inherited boundary slivers remain open. CORE38 now roots all five target groups/33pads,13groups20pads remain. U11015 exact replacement and two LOGIC contact-restoring planes constructed; regulated41 adds20vias20stubs18planes with10groups unjoined. Protected R9 replaces four owned bridge conflicts on exact CORE38; return repair and all-zone audit follow its completed geometry. C10036 nearby return needs exact scoped DOB supply-track reroute. R12 CPU/GPU alarm active through02:38UTC; unchanged four KiCad slots and12-thread cap. Original live/source preserved. No adoption or fabrication release. See continuation-r2/checkpoint-r11.json.\n')
docs[1].write_text(note,encoding='utf-8');old=docs[2].read_bytes();i=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:i]+insert+old[i:])
assert sha(live)==c['live_r07_sha256']
write_new(H/'checkpoint-document-receipt-r11.json',{'backups':backs,'after':{str(p.resolve()):sha(p) for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
print(json.dumps({'checkpoint':str(H/'checkpoint-r11.json'),'live_unchanged':True,'native_gate':'FAIL_11_ERRORS','protected_r9':'RUNNING'}))
