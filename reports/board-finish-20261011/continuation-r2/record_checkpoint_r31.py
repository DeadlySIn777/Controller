"""Save continuing exact repairs without overwriting source or prior evidence."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def fresh(p,x):
 assert not p.exists();p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
prior=H/'checkpoint-r30.json';c=read(prior)
live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
assert sha(live)==c['live_r07_sha256']
c['previous_checkpoint_sha256']=sha(prior);c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
c['continuing_work'].update({
 'TMR_native_keepout':'R515 minimal two-owned-zone/two-current-fill packet model4f70c827 receipt06a86329 replaces only FA7ef3 and IO3In2 4f297 exact R155 roles. FA47/47 sources retained; IO3 existing-barrel1mm/36.969mm bypass restores all8 R14045 keys and594/594 source pads, zero old IO3 source/group losses; R513 receipt39e74ace reports zero true geometry/no-zone errors and all3ground arrays/reference roles exact. Raw R505/507/509 literal canonical-gain failures preserved with individual converter-local100nm negative witnesses. Complete unchanged-net/direct delta certificate running; no native/current/adoption credit.',
 'U10003':'Exact R196 modeldfb8050d restores U10003.9 actual FG source with9 new tracks/3ordinary vias/7exact original-track replacements. R197 ae56bcd5: all98 true geometry checks pass, three-net physical/source contacts zero loss. R199 ba3f1880:2386 untouched nets exact and new holes disjoint, but one strict old FFAULT reference loses literal2.25764e-16mm2 around original A antipad; retained FAIL. New full-body ground/fault/clock references and clock return window remain failed. R198/R200/R201 finite return/relocation searches no-path. R202 attributes otherwise legal clock sites to one original F LOGIC eeb33 wall; R203 coupled clock/one exact logic-wall route finite no-path, no edits applied. Physical/reference cause diagnosis continues.',
 'CORE_current':'CM79 R315 sparse diagnostic adds six tracks/two ordinary power ports, preserves CM49 and reaches50/51 actual source grounds. R316 bb93a32c audits all2388 actual nets/contact/direct/ninesource geometry with zero loss/errors, but three original B reference bodies lose .0194064mm2 each under power antipads. R3179e67f02a additionally finds both retained original F anchors lose .7195600mm2 each; native LG local .25 clearance requires .525 antipad radius. R318 protects every B/F supported body. Exact original-middle-only alternate CORE5 source topology test follows, preserving full1.25 F anchors/allold keys; current/drop/capacity not inferred. J15001.1 and full power/current/native remain open.',
 'Q0_DIC':'Q0 R404 freezes legal SENSE/Q0 stems and paired actual returns. R4088e81dd97 proves FLT F endpoints remain in separate physical components even withdrawing exact7bb power wall; reserved FLT departure also disconnects power detour. Agent nominates ordinary FLT dive in actual reachable F component with all old power retained. DIC two return relocations local pass, third full-annulus blocked and new-only reroute remains open. No native adoption.',
 'native':'R113 completed diagnostic on failed R9:499 capped unconnected,0parity,1TMR ordinary error298warnings; in-memory CLI Cu not saved and original missing187In3/three oldgroup losses still FAIL. R157 full native refill remains running existing sharedslot since15:06UTC; frozen inputs unchanged. No restart/new slot. TMR repair packet is a later exact sparse delta, not applied to running job.'})
c['root_running_constructor'].update({'U10003_R196_R197':'98_GEOMETRY_ZERO_LOSS_PASS_NEW_REFERENCE_AND_OLD_REFERENCE_ONE_LITERAL_FAIL','CM_R315_R316_R317':'50OF51_ALL2388_CONTACT_PASS_THREE_B_AND_TWO_RETAINED_F_REFERENCE_FAIL','TMR_R515':'TWO_OWNED_ZONE_SCOPED_SOURCE_NOZONE_PASS_FULL_DELTA_CERTIFICATE_OPEN','Q0_R408':'FINITE_PHYSICAL_SPLIT_NEW_ORDINARY_DIVE_SEARCH','resource_R28_R29':'R28_ACTIVE_TO183530UTC_R29_SCHEDULED183520UTC'})
names=['U10003-compliant-clock-fault-ground-independent-drilled-source-geometry-r197','U10003-R196-unchanged-net-physical-identity-and-strict-oldrefs-r199','U10003-clock-and-exact-logic-wall-rework-nomination-r203','CM79-exact-R289-existing-return-fullwidth-sparse-diagnostic-r315','CM79-R315-retained-original-F-anchor-before-supported-reference-r317','FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515','IO3-TMR-minimal-union-independent-source-geometry-r513','Q0-power-FLT-coupled-exact-components-r408']
receipts=list(H.rglob('receipt.json'))
for n in names:
 xs=[p for p in receipts if p.parent.name==n];assert len(xs)==1,n;c['evidence_sha256'][str(xs[0].resolve())]=sha(xs[0])
# Resolve the unique completed all-net CM gate by its receipt contents, avoiding guessed paths.
xs=[p for p in receipts if p.parent.name.endswith('-r316') and 'CM79' in p.parent.name]
assert len(xs)==1;c['evidence_sha256'][str(xs[0].resolve())]=sha(xs[0])
for rev in ['r28','r29']:
 f=H/('resource-monitor-'+rev);p=f/'resource-status.json'
 if p.exists():
  xs=[json.loads(x)for x in(f/'resource-samples.jsonl').read_text().splitlines()]
  c['resource_watches'][f.name]={'status':read(p),'samples_at_checkpoint':len(xs),'cpu_max_percent':max(x['cpu_percent']for x in xs),'GPU_max_C':max(x['gpu_c']for x in xs),'GPU_max_W':max(x['gpu_w']for x in xs),'breach_samples':sum(bool(x['breached'])for x in xs),'last_sample':xs[-1]}
 else:c['resource_watches'][f.name]={'scheduled':read(f/'prior-watch-receipt.json')}
c['native_jobs_snapshot']={n:read(H/n)for n in['R155-known-reference-native-diagnostic-r157/measure/status.json','R9-failed-flash-native-DRC-diagnostic-r113/status.json']}
fresh(H/'checkpoint-r31.json',c)
docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
for p in docs:
 q=H/('checkpoint-r31-before-'+p.name);assert not q.exists();q.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(q.resolve()),'sha256':sha(q)}
s=read(docs[0]);s['continuation_r31']=c;s['updated_utc']=c['utc'];docs[0].write_text(json.dumps(s,indent=2)+'\n')
note=('Continuation '+c['utc']+'\n\nClaude saved revisions continued; live R07 unchanged. Scoped TMR FA/IO3 repair removes native converter keepout overlaps and restores all eight R14045 IO3 keys with594 retained source pads, no new holes/discrete Cu. Full delta certificate still open. CM79 reaches50/51 grounds and passes all2388 host contact graphs, but three old B references and both retained F anchors lose supported copper; rejected pending exact repair. U10003 all98 geometry/three-net contact/source checks pass, but clock/new-body references and one literal old-antipad reference failure remain. Q0 bounded component diagnosis continues ordinary dive search. R157 native fill still runs on frozen existing sharedslot. R28 CPU70%/GPU80C350W watch active, R29 scheduled; four allocated KiCad slots and12CPU cap unchanged. Full board/source/reference/current/native/physical/manufacturing gates remain incomplete. No adoption or fabrication release. See continuation-r2/checkpoint-r31.json.\n')
docs[1].write_text(note);old=docs[2].read_bytes();at=old.find(b'\n')+1;insert=('\n'+note+'\n').encode();docs[2].write_bytes(old[:at]+insert+old[at:]);assert sha(live)==c['live_r07_sha256']
fresh(H/'checkpoint-document-receipt-r31.json',{'backups':backups,'after':{str(p.resolve()):sha(p)for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(insert,b'',1)==old,'live_unchanged':True,'adopted':False})
print('R31_CHECKPOINT',c['utc'],'LIVE_UNCHANGED',flush=True)
