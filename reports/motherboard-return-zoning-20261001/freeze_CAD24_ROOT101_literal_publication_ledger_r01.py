from pathlib import Path
import json,hashlib
D=Path('reports/motherboard-cad-publication-20261001/CAD24-to-ROOT101-ledger-r01');r=json.loads((D/'receipt.json').read_text());j=json.loads((D/'literal-footprint-and-pad-delta.json').read_text());r['publication_allowed']=False;r['Source27_adopted']=False
text=f'''This is a read-only publication ledger for published CAD 20260930-24 and the prospective ROOT101 work-in-progress board. It does not publish, export manufacturing files, or declare readiness.

Both boards contain exactly 2,688 physical source footprints with the same footprint and pad UUID populations. The outline stays 460 × 340 mm and six copper layers. The requested 1.600 mm stackup/rules are now explicit; supplier approval and impedance verification remain separate.

Copper changes: {r['old_Cu_unchanged']:,} prior items have identical semantic geometry, {r['old_Cu_modified']:,} were explicitly modified, {r['old_Cu_retired']:,} were retired, and {r['new_Cu_added']:,} were added. Total tracks/vias grow from {r['Cu_before']:,} to {r['Cu_after']:,}. These figures do not claim all original copper was retained; the full literal per-UUID ledger records every changed or retired item.

{r['footprint_poses_changed']:,} footprint poses changed. The only physical pin-net corrections are R14069.2 and R14072.2, from the old probe-IN nodes to their actual SENSE nodes. Source24–26 account for the precise two-pin, five capacitor procurement/value and three fuse-footprint corrections. Manufacturer land/drill changes are limited to C14746's two pads and the three fuseholder instances' four lands/holes each. No footprint/pad UUID or module architecture changes occurred. R14602/R14626 native value strings are corrected from stale274k labels to the already-selected267k source values; these are display reconciliation, not new electrical source selections.

There are {r['zone_after']:,} native zones/rule areas rather than five legacy fills. Zone definitions, generated fill, actual Source anchoring and per-route return coverage remain distinct checks. The exact added and modified definitions are recorded separately from native derived fill.

Native regular DRC is zero errors/zero warnings with no ignored checks. Uncapped missing copper joins fall from4,753 to3,528 (1,225 fewer). This is still a partially routed prototype design. The prospective board is SHA{r['target_board_sha256']}; root combined Source/connectivity,106-loop/retained-route and regression proofs must close before publication. Source27 remains unadopted. Full power/drop/thermal, FPGA vendor implementation, measured20ms behavior, mechanical qualification, manufacturing files and physical validation are not credited by this ledger.
'''
(D/'README.txt').write_text(text)
files=[p for p in D.iterdir()if p.is_file()and p.name!='freeze.json'];freeze=dict(passed=True,scope='Read-only exact WIP publication ledger',published_revision='20260930-24',target_board_sha256=r['target_board_sha256'],files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in files},publication_allowed=False,combined_target_adoption_pending=True,manufacturing_ready=False);(D/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');print(json.dumps({k:r[k]for k in('old_Cu_unchanged','zone_definitions_modified','zone_definitions_removed')}));print(hashlib.sha256((D/'freeze.json').read_bytes()).hexdigest())
