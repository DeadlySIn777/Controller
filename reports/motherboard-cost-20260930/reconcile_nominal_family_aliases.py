"""Report-only review of five incomplete cost-tool alias whitelists.

Run with KiCad Python. Check frozen native pad identities and library filenames;
do not modify the old issued cost receipt or claim new manufacturer geometry.
"""
from pathlib import Path
import json,hashlib
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'reports/motherboard-cost-20260930/source-r20b-2663-complete-cost-v5'
OUT=ROOT/'reports/motherboard-cost-20260930/nominal-family-alias-reconciliation-r01.json'
assert not OUT.exists(),OUT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
model=json.loads((OLD/'inputs/hardware/motherboard/design.json').read_text())
old=json.loads((OLD/'PARTS_SOURCING_REVIEW.json').read_text())
expected={'ISO1212DBQR':16,'LTC2962HUD#PBF':17,'74LVC07APW,118':14,'TLP3640A(TPL,E':4,'TLP4176A(TP,F':4}
assert {p['mpn'] for p in old if p['nominal_family_screen_pass'] is False}==set(expected)
records=[]
for mpn,count in expected.items():
    parts={r:p for r,p in model['components'].items() if p['mpn']==mpn}
    aliases=[]
    for libid in sorted(set(p['footprint'] for p in parts.values())):
        lib,name=libid.split(':')
        folder=OLD/'inputs/hardware/motherboard'/(lib+'.pretty')
        if not folder.exists():folder=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')/(lib+'.pretty')
        path=folder/(name+'.kicad_mod')
        assert path.is_file(),libid
        fp=pcbnew.FootprintLoad(str(folder),name)
        assert fp is not None,libid
        pads=[p for p in fp.Pads() if p.GetNumber()]
        numbers={p.GetNumber() for p in pads}
        assert numbers==set(str(i) for i in range(1,count+1)),(libid,numbers)
        for ref,p in parts.items():
            if p['footprint']==libid:assert set(p['pins'])==numbers,(ref,libid)
        aliases.append(dict(library_id=libid,footprint_sha256=sha(path),native_distinct_electrical_pad_count=len(numbers),
            pads=[dict(number=p.GetNumber(),x_mm=p.GetPosition().x/1e6,y_mm=p.GetPosition().y/1e6,size_x_mm=p.GetSize().x/1e6,size_y_mm=p.GetSize().y/1e6) for p in pads]))
    records.append(dict(mpn=mpn,physical_references=sorted(parts),family_alias_whitelist_was_incomplete=True,
        actual_pad_identity_pass=True,manufacturer_geometry_reverified_here=False,
        genuine_package_mismatch_established=False,aliases=aliases))
record=dict(scope='Report-only reconciliation of cost-tool library qualifiers, using exact frozen r20b footprints. Not a manufacturer pad-size or layout release.',
    cost_snapshot=OLD.name,cost_receipt_sha256=sha(OLD/'receipt.json'),source_design_sha256=sha(OLD/'inputs/hardware/motherboard/design.json'),
    groups=records,pass_result=True,issued_price_arithmetic_unchanged=True,source_hardware_changed=False,
    native_ERC_DRC=False,manufacturing_ready=False,
    corrected_live_cost_tool_sha256=sha(ROOT/'tools/motherboard_cost_audit.py'),
    note='Future cost receipts recognize these explicit reviewed source-library aliases. The immutable v5 whitelist false results are not actual geometry/pin mismatch evidence; manufacturer land/pin qualification remains in electrical child/native reviews.')
OUT.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(path=str(OUT),groups=len(records),aliases=sum(len(r['aliases']) for r in records),pass_result=True)))
