"""Preserve exact continuation evidence while native and constructive jobs run."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def write_new(p,value):
    if p.exists():raise ValueError('Evidence already exists: '+str(p))
    p.write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')
def main():
    previous=H/'checkpoint-r6.json';c=read(previous)
    live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb')
    assert sha(live)==c['live_r07_sha256']
    c['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();c['previous_checkpoint_sha256']=sha(previous)
    paths=[H/'all-copper-native-contract-r2/receipt.json',H/'field-signed-port-allocation-r4/receipt.json',H/'field-signed-group-bounds-r1/receipt.json',H/'field-power/field-io3-crossing-contact-audit-r15e/receipt.json',H/'field-power/complete-local-field-return-contact-audit-r10/receipt.json',H/'field-power/local-via-aperture-audit-r14/receipt.json',H/'sbc-power/core-retained-f-feeds-r17/receipt.json',H/'coupled-recovery/ao1-reference-coupled-r7.json',H/'protected24-source-census-r2/receipt.json',H/'protected24-source-layer-inventory-r1/receipt.json',H/'protected24-dogbones-r4/stop-receipt.json',H/'protected24-dogbones-r5-derivation.json']
    for p in paths:
        if not p.exists():raise ValueError('Required exact receipt missing: '+str(p))
    copper=read(paths[0]);allocation=read(paths[1]);bounds=read(paths[2]);crossing=read(paths[3]);contact=read(paths[4]);aperture=read(paths[5])
    assert copper['verdict'].startswith('PASS_') and allocation['verdict'].startswith('PASS_') and bounds['verdict'].startswith('PASS_')
    c['all_discrete_native_contract']={'board_sha256':copper['candidate_sha256'],'native_source_pose_and_every_raw_Cu_UUID_geometry':'PASS','counts':copper['copper_contract']['counts'],'scope':'Exact dc936 field-only trial before refill; final power/analog proposals excluded'}
    c['field_signed_current_allocation']={'verdict':allocation['verdict'],'terms':len(allocation['terms']),'physical_endpoint_and_KCL_ledger_sha256':sha(paths[1]),'allocation':'Unknown nonnegative simplex current sharing with all eligible physical pads; no equal-sharing assumption','ground_source_roots':['J11003.2','J11005.2'],'return_mesh_current_drop_thermal_and_active_path_bounds':'OPEN','actual_schematic_paths':'Four wetting resistor paths traced through TLP3640A LED pins1/2 only; isolated output3/4 never treated as conductive'}
    c['field_group_current_bounds']={'verdict':bounds['verdict'],'scope':'Exact r15e physical groups, per-group signed intervals; cannot sum independent group extrema as simultaneous loads','receipt_sha256':sha(paths[2]),'later_ground_and_protected_supply_revisions':'Excluded; must rebind and recompute'}
    c['continuing_work']={
      'field_power':'R15e mutual crossing audit passes against exact r5 composed geometry, not original198b CORE. R6/r8/r9 proposal reaches224 FA and251 FB named pads at actual roots, with8 FA/2 FB small groups remaining. R10 fails one LOGIC contact group (4307+3 split) and r14 rejects multiple weak SMD/new-new drill sites; these unadopted additions are being corrected, including one .15-mm stub. No native acceptance.',
      'SBC_power':'R17 CORE feeds restore the original large CORE group and join9 further load groups;18 groups/54 pads remain. Confined inner-feed construction runs on the complete proposed overlay. Actual source markers are CORE R11022.2, CORE1V2 L2001.2, IO3 R18001.2 after the15mOhm current shunt fed by L2002.2; old SW-node diagnostics are rejected.',
      'r06_recovery':'Twelve original r06 pad groups remain lost in latest completed full native trial; all unchanged-original pad-group gates retained.',
      'analog':'R7 full-reference prefilter finds9 VREF sites but no SDI site on its .1-mm grid simultaneously reaches retained F/In3 reference. Finer boundary search and an exact coupled physical recipe are running; stale withdrawn-via fill credit is not assumed. No analog board emitted.',
      'protected_24V':'All12 unrooted positive supply groups are outer-only and require ordinary fanouts. R4 intentionally stopped as a diagnostic: its all-drill plane obstacle erased the source vias own plated annuli, and its SMD/new-new guards were weak. Frozen R5 corrects these without changing any native rule and searches explicit source-rooted bridges with only new owned same-domain return cuts. All signed current/barrel/contact/native gates mandatory.',
      'power_connector':'CM5 test-pad supply harness/return-sharing proposal remains separate and unadopted; mechanical/module/ground/RF/current qualification open.',
    }
    c['field_crossing_contact_audit']={'verdict':crossing['verdict'],'scope':'Exact r5 composed geometry to r15; original198b CORE requires separate check','receipt_sha256':sha(paths[3])}
    c['field_local_return_gate']={'contact_verdict':contact['verdict'],'aperture_verdict':aperture['verdict'],'adopted':False,'correction_running':True}
    state=read(H/'field-power-native-trial-r1/measure/status.json');c['running_native_field_trial']['state']=state
    c['protected24_constructor']={'revision':'R5','exec_session_id':50979,'board_written':False,'native_jobs':0,'same_raw_PTH_source_plane_overlap':'Positive annular contact required; source plated hole is not a foreign copper barrier','SMD_and_all_old_previous_new_drill_guard_mm':.275,'all_full_contact_mutual_source_current_native_gates':'OPEN'}
    for name in ('resource-monitor-r9','resource-monitor-r10'):
        folder=H/name;rows=[json.loads(s) for s in (folder/'resource-samples.jsonl').read_text().splitlines()]
        c['resource_watches'][name]={'status':read(folder/'resource-status.json'),'samples_at_checkpoint':len(rows),'cpu_max_percent':max(r['cpu_percent'] for r in rows),'GPU_max_C':max(r['gpu_c'] for r in rows),'GPU_max_W':max(r['gpu_w'] for r in rows),'breach_samples':sum(bool(r['breached']) for r in rows),'last_sample':rows[-1]}
    c['evidence_sha256'].update({str(p.resolve()):sha(p) for p in paths});write_new(H/'checkpoint-r7.json',c)
    docs=[B/'CURRENT_STATUS.json',B/'CURRENT_STATUS.txt',B/'README.md'];backups={}
    for p in docs:
        target=H/('checkpoint-r7-before-'+p.name)
        if target.exists():raise ValueError('Prior status backup exists')
        target.write_bytes(p.read_bytes());backups[str(p.resolve())]={'path':str(target.resolve()),'sha256':sha(target)}
    status=read(docs[0]);status['continuation_r7']=c;status['updated_utc']=c['utc'];docs[0].write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    text=('Board finish continuation: '+c['utc']+'\nLatest completed full native trial1beb9a22:1354 missing pad joins,1365 uncapped API items,0 ordinary DRC errors,186 warnings;12 r06 groups remain lost.\nNative dc936 source/pose and ALL86161 segments/7907 vias exact raw/net geometry PASS before refill. Full refill/DRC phase: '+state['phase']+'. Field-only exploratory scope; final SBC/local-ground/protected/analog work excluded.\nSigned FA/FB planning allocation:146 terms,299 physical pad/net pairs, KCL and exact endpoints PASS. Mesh/current/thermal qualification OPEN.\nField local-ground proposals:224 FA/251 FB source-rooted pads,10 groups remain. Reject r8 until stronger SMD/new-new drill and .20-mm trace fixes pass; reject r10 LOGIC split until repaired.\nCORE main group restored with9 extra feeds;18 groups/54 pads remain. Protected24 ordinary source-rooted dogbone constructor R5 running; AO1 exact coupled search running.\nSource ERC0 errors/92 warnings, review OPEN. Live board/project/rules unchanged; no adoption/fabrication release. Four KiCad slots and12 reserved CPUs; alarms active. See continuation-r2/checkpoint-r7.json.\n')
    docs[1].write_text(text,encoding='utf-8');old=docs[2].read_bytes();i=old.find(b'\n')+1
    note=('\nContinuation checkpoint '+c['utc']+'\n\nNative source/pose/all-discrete geometry gate passes on the exact field-only exploratory trial; refill/DRC '+state['phase']+'. Signed field planning allocation now binds146 terms and299 physical pad/net pairs. Later ground/CORE/protected/analog construction remains gated; weak proposed apertures and one LOGIC contact split are rejected and being corrected. Latest full native trial still has1354 missing joins and12 r06 losses. Source board unchanged; no fabrication release. See [checkpoint-r7](continuation-r2/checkpoint-r7.json).\n\n').encode();docs[2].write_bytes(old[:i]+note+old[i:])
    assert sha(live)==c['live_r07_sha256']
    write_new(H/'checkpoint-document-receipt-r7.json',{'backups':backups,'after':{str(p.resolve()):sha(p) for p in docs},'all_prior_README_bytes_preserved':docs[2].read_bytes().replace(note,b'',1)==old,'live_unchanged':True,'adopted':False})
    print(json.dumps({'checkpoint':str(H/'checkpoint-r7.json'),'full_native_phase':state['phase'],'live_unchanged':True}))
if __name__=='__main__':main()
