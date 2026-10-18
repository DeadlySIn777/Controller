"""Preserve R89, add only exact R92 SBC pad-union relocation classification."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
s=(H/'audit_full_power_sources_r89.py').read_text()
def replace(a,b):
    global s
    assert s.count(a)==1;(s:=s.replace(a,b))
replace("OUT=L.OUT/'full-power-source-contact-audit-r89'", "OUT=L.OUT/'full-power-source-contact-audit-r94'")
replace("fp_ledger=json.loads(fp_ledger_path.read_text());relocated=[r for r in fp_ledger if r['kind']=='pad']", """fp_ledger=json.loads(fp_ledger_path.read_text());relocated=[r for r in fp_ledger if r['kind']=='pad']
    sbcf=L.OUT/'sbc-owned-pad-only-relocation-proof-r92/receipt.json';assert sha(sbcf)=='27e7a34fb927aa8bc77f80557eaf800eee1b7d13d8e1e033c574fa67f02c1658'
    sbc_authorized=json.loads(sbcf.read_text())['rows']""")
replace("else:entirelylost.append(record)", """else:
                        sbc_match=[r for r in sbc_authorized if r['layer']==layer and r['old_union_part']==oldindex and r['old_WKB_sha256']==hashlib.sha256(oldpiece.wkb).hexdigest()] if net=='/motherboard_power_entry/SBC_5V' else []
                        if sbc_match:
                            assert len(sbc_match)==1;auth=sbc_match[0]
                            assert auth['exact_integer_grid_original_union_equals_only_authorized_moved_pads'] and auth['no_original_track_via_zone_fill_excluded']
                            for moved in auth['owned_moved_pads']:
                                currentpad=next(q for q in h['pads'] if q['uuid']==moved['uuid'])
                                assert json.loads(json.dumps(currentpad))==moved['exact_replacement_geometry']
                                assert lookup[moved['uuid']]==root
                            record.update({'exact_authorized_pad_only_union_ledger_file':str(sbcf.resolve()),'exact_authorized_pad_only_union_ledger_sha256':sha(sbcf),'original_union_only_authorized_moved_pad_UUIDs':[q['uuid'] for q in auth['owned_moved_pads']],'replacement_named_pads_actual_source_rooted':True,'no_unowned_Cu_relationship_excluded':True});authorized_relocated_old_parts.append(record)
                        else:entirelylost.append(record)""")
out=H/'audit_full_power_sources_r94.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec');print('AUDITOR_R94_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
