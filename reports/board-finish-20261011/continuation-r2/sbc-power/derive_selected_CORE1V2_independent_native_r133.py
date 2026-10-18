"""Derive exact-source/actual-annuli review of immutable selected native fill."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent;s=(H/'audit_io3_selected_native_r1.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
replace("d=H/'io3-native-diagnostic-r2';out=d/'independent-selected-IO3.json'", "d=H/'core1v2-native-diagnostic-r132';out=d/'independent-selected-CORE1V2-r133.json'")
replace("'6f5447d29114cb527f13b44ab7f001bbcb18e581bb9484025919323e78e5b2f3'", "'65e55826c5b925fdcfb98114b1f6d04f0ca49e67b3025db21157436cee71f6eb'")
replace("'de2d00a03e24a2799d3cabffb2a01f58ea2a0385f526926d019a81325376695a'", "'13571e6204e78f9aab1f2858ff123b6ef72f3aab766edb2587bc8155954f8ec7'")
replace("mp=H/'sbc-power/owned-io3-layer-escape-repair-r42/model.pkl'", "mp=H/'sbc-power/frozen-regional-source-exit-replay-r129/model.pkl'")
replace("'dc06d1688f700a4c0232ee948ebbdfba6d4af931a9918f5521b1914de194ce68'", "'8f4db80497693186388d622a45508cdf39eb5e0f51a9ee359061bb7d6428ad93'")
s=s.replace("'/IO_3V3'","'/CORE_1V2'")
replace("('R18001','2')", "('L2001','2')")
replace("('R11049','1')", "('U1001','J7')")
replace("via='4df659b6-03b2-580c-b6b8-1cc10e70c2c8';need={'F.Cu','In1.Cu'}", "via='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92';need={'F.Cu','In3.Cu','In4.Cu'}")
anchor="    okay=index[target['uuid']]==root"
i=s.index(anchor)
s=s[:i]+'''    # Repeat pad/track/via source membership with the independent integer
    # contact implementation, rather than credit the fast graph's 2 nm glue.
    sys.path.insert(0,str(H/'sbc-power'));import io3_contact_restore_r2 as Q
    Q.NET=raw;exact_groups,exact_parts,exact_assign=Q.groups(g,return_details=True)
    exact_root=next(i for i,xs in enumerate(exact_groups) if any((p['ref'],p['pad'])==('L2001','2') for p in xs))
    exact_source_keys={p['uuid'] for p in exact_groups[exact_root]}
    expected=json.loads((H/'sbc-power/frozen-regional-source-exit-replay-r129/source-scope-checkpoint.json').read_bytes())['joined_pad_keys']
    missing_expected=set(expected)-exact_source_keys
    landing='13ace114-2da3-479c-9c70-bee7d15da004';lv=next(q for q in vias if q['uuid']==landing)
    la=Point(lv['x'],lv['y']).buffer(lv['d']/2,quad_segs=64).difference(Point(lv['x'],lv['y']).buffer(lv['drill']/2,quad_segs=64))
    lphysical=unary_union([q['shape'] for q in groups[root] if q['layer']=='In4.Cu' and q['kind']!='via'])
    landing_overlap=la.intersection(lphysical).area
''' + s[i:]
replace("okay=index[target['uuid']]==root and index[via]==root and need<=actual and all(q['source_rooted_other_Cu_annular_overlap_mm2']>1e-8 for q in annular)", "okay=index[target['uuid']]==root and index[via]==root and need<=actual and all(q['source_rooted_other_Cu_annular_overlap_mm2']>1e-8 for q in annular) and not missing_expected and landing_overlap>1e-8 and 'In4.Cu' in flashes[landing]")
s=s.replace('IO3','CORE1V2').replace("'actual_source':'R18001.2'", "'actual_source':'L2001.2'").replace("'target':'R11049.1'", "'target':'U1001.J7'").replace('required_actual_F_In1_annuli','required_actual_F_In3_In4_annuli')
s=s.replace("'scope':'Only31 exact CORE1V2 zones freshly filled; no other R38 power proposals or other-zone refill credit'", "'scope':'Only3 exact CORE1V2 zones freshly filled; complete owned CORE notch and other power proposals excluded. This proves selected source/barrel geometry, not wholeboard or PDN qualification.'")
anchor="    out.write_text(json.dumps(report,indent=1)"
i=s.index(anchor)
s=s[:i]+'''    report.update({'independent_exact_integer_source_group':exact_root,'exact_integer_expected25_pad_keys_source_retained':not missing_expected,'missing_expected_exact_pad_keys':sorted(missing_expected),'target_landing_In4_annular_overlap_mm2':landing_overlap,'original_f6_F_In3_actual_masks_retained':{'F.Cu','In3.Cu'}<=actual,'additional_f6_In4_actual_native_flash':('In4.Cu' in actual),'landing_via_actual_In4_flash':('In4.Cu' in flashes[landing]),'exact_no_host_contact_tolerance':True,'complete_current_or_thermal_capability_granted':False})
''' + s[i:]
out=H/'audit_core1v2_selected_native_r133.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
print('CORE1V2_INDEPENDENT_NATIVE_AUDITOR_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
