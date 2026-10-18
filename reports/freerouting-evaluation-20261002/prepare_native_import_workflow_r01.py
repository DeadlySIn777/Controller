"""Freeze the exact copy-only native import/replay commands; no board writes."""
from pathlib import Path
import hashlib,json,sys

ROOT=Path.cwd().resolve()
R=ROOT/'reports/freerouting-evaluation-20261002'
PREP=R/'ROOT103-GPIO-config-convex-DSN-r03'
REVIEW=R/'ROOT103-GPIO-config-visual-allowlist-r04'
BASE=ROOT/'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31'
OUT=R/'ROOT103-native-import-workflow-r01'
PY='C:/Program Files/KiCad/10.0/bin/python.exe'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
assert not OUT.exists()
frozen=read(PREP/'prepare.json');coverage=read(PREP/'independent-exact-coverage-r01.json')
assert coverage['passed'] and coverage['every_original_obstacle_covered_without_area_tolerance']
assert frozen['selected_dsn_sha256']==sha(PREP/'selected.dsn')=='dd6fce893b7bd94207872bd97f4a904f5744f0c944cced16df3d35542d194e49'
assert sha(PREP/'base.kicad_pcb')==frozen['prepared_board_sha256']=='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
manifest=read(PREP/'manifest.json');source=read(REVIEW/'source-scope-review.json')
assert len(manifest['nets'])==source['actual_selected_unjoined_nets']==27
assert source['required_joins_before']==48
inputs=[PREP/'prepare.json',PREP/'selected.dsn',PREP/'base.kicad_pcb',PREP/'base.kicad_pro',PREP/'base.kicad_dru',PREP/'manifest.json',PREP/'design.json',PREP/'netlist.xml',PREP/'independent-exact-coverage-r01.json',PREP/'convex-conservative-coverage-review.json',REVIEW/'source-scope-review.json',REVIEW/'protected-native-manifest.json',REVIEW/'baseline-disposition.json',BASE/'final-binding-r02/current110-bypass-manifest.json',BASE/'final-scoped-freeze-r01.json',ROOT/'tools/hardware_route_ordinary_wip_r05.py',ROOT/'tools/hardware_verify_owned_bypass_batch.py',ROOT/'tools/hardware_validate_motherboard_return_planes_r06.py',ROOT/'reports/motherboard-return-zoning-20261001/check_final_health_unchanged_relative_power_r01.py',ROOT/'reports/motherboard-return-zoning-20261001/check_final_health_new_modified_drill_registration_r01.py',Path(__file__).resolve()]
hashes={str(p):sha(p)for p in inputs}
DEST=R/'ROOT103-GPIO-config-native-import-r01'
BOARD=DEST/'additive-route-candidate.kicad_pcb'
MAP=DEST/'source26-domain-map-r01/domain-map.json'
prefix=[PY,'-X','utf8']
commands={
 'strict_native_additive_import':prefix+[str(ROOT/'tools/hardware_route_ordinary_wip_r05.py'),'import','--prepared',str(PREP),'--session','<FROZEN_ACTUAL_SESSION_PATH>','--out',str(DEST),'--baseline-disposition',str(REVIEW/'baseline-disposition.json')],
 'fresh_complete_source_map':prefix+[str(ROOT/'tools/hardware_map_motherboard_domains.py'),'--board',str(BOARD),'--source',str(ROOT/'hardware/motherboard'),'--out',str(DEST/'source26-domain-map-r01')],
 'actual_literal_resources':prefix+[str(ROOT/'tools/hardware_validate_motherboard_return_planes_r06.py'),'--board',str(BOARD),'--map',str(MAP),'--out',str(DEST/'retained-native-resources-r01.json')],
 'retained110_bypass_loops':prefix+[str(ROOT/'tools/hardware_verify_owned_bypass_batch.py'),'--board',str(BOARD),'--owners',str(ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json'),'--receipt',str(BASE/'final-binding-r02/current110-bypass-manifest.json'),'--out',str(DEST/'retained110-bypass-proof-r01.json')],
 'unchanged_relative_power_guard':prefix+[str(ROOT/'reports/motherboard-return-zoning-20261001/check_final_health_unchanged_relative_power_r01.py'),'--board',str(BOARD),'--out',str(DEST/'unchanged-global-power-proof-r01.json')],
 'added_drill_registration_if_vias_added':prefix+[str(ROOT/'reports/motherboard-return-zoning-20261001/check_final_health_new_modified_drill_registration_r01.py'),'--before',str(PREP/'base.kicad_pcb'),'--board',str(BOARD),'--out',str(DEST/'added-drill-registration-r01.json')],
}
OUT.mkdir()
result=dict(passed=True,scope='Preparation only: frozen actual SES remains required. Exact native import and retained-circuit acceptance remain pending; no route/candidate is accepted by this workflow receipt.',input_sha256=hashes,exact_prepared_board_sha256=frozen['prepared_board_sha256'],selected_dsn_sha256=frozen['selected_dsn_sha256'],selected_nets=list(manifest['nets']),selected_net_count=27,actual_required_joins_before=48,commands=commands,
 gates=['Actual Java outcome and SES hash must be frozen; never substitute fabricated session output.','Native placement-only import control plus exact authoritative immutable restoration; every original footprint, pad, pose, old copper and zone definition retained.','Complete model/XML native source population and every preexisting native Source-pad cluster retained.','Every new signal segment and via passes exact source-derived return corridor, actual flashed annuli, native connected-layer and Source-backed same-domain stitch within1mm.','Native DRC zero errors/zero warnings/no ignored checks.','Uncapped native joins equal independent Source-cluster joins; zero actual orphan copper; require a real reduction from3521 joins.','All110 current owned loops and225 receiving returns plus actual188 anchored literal resources rechecked; no synthetic resource pass.','Frozen relative IO3/CORE guard passes; no topology, narrow-feature, source44/feed22 or protected-annulus waiver.','Each new conventional drilled via passes actual .15mm SMD registration clearance plus native foreign-copper/hole clearance.','Freeze exact new copper UUID/net/geometry ledger, per-net actual Source joining evidence and saved/refilled/fresh-reload physical cut controls before adoption.','Parent complete retained-circuit replay/full regression and bounded adoption remain separate.'],
 known_frozen_import_limitation='Frozen add_return_stitches does not mark its temporary new native via free before BuildConnectivity. Its final serialized/native-net identity guard remains strict. If the known net-reassignment defect appears, preserve the rejected import and use a separately reviewed wrapper changing only new Ground-via assignment; never alter frozen dependency bytes.',
 frozen_old_guards_unchanged=True,live_board_or_source_mutated=False,routing_accepted=False,manufacturing_ready=False)
(OUT/'workflow.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
assert all(sha(p)==h for p,h in hashes.items())
print(json.dumps(dict(passed=True,preparation_only=True,selected_nets=27,actual_before_joins=48,workflow=str((OUT/'workflow.json').resolve()))),flush=True)
