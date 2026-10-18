"""Fresh complete incremental audit of corrected joint minimal operations."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_REG_U25_T4_R7_DIC_current_full_r358.py').read_text(encoding='utf-8')
s=s.replace('REG-U25-T4-R7-corrected-DIC262-sparse-current-composition-r356','REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364')
s=s.replace('REG-U25-T4-R7-DIC-current-independent-full-audit-r358','REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r365')
s=s.replace("br['model_SHA256']","br['model_sha256']")
old="d=pickle.loads((R/'new-owned-discrete.pkl').read_bytes());"
new="""import restore_field_current_mixed_precision_states_r366 as MP
 precision=MP.restore_bound_field_current_precision_states(b,q);write(O/'exhaustive-mixed-role-WKB-precision-restoration.json',precision)
 f=H/'REG-U25-corrected-DIC262-sparse-current-composition-r359/new-owned-discrete.pkl';fd=pickle.loads(f.read_bytes());sp=H.parent/'sbc-power/T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r273';assert sha(sp/'receipt.json')=='97bc789fb90e688dc2b78c6f24a4877d4b7497055023a1748935c55a4a274692';sd=pickle.loads((sp/'only-owned-new-discrete-and-four-exact-deletes.pkl').read_bytes());d={'tracks':fd['tracks']+sd['tracks'],'vias':fd['vias']+sd['vias'],'removed':fd['removed']+sd['removed']};"""
assert s.count(old)==1;s=s.replace(old,new)
needle=" bad=errors or any(c['old_layer_key_partition_losses']for c in contacts)"
replacement=""" lg=K.root(groups['/LOGIC_GND'],'J11001','2');sref=K.source_refs(lg);sbc_newrefs=[]
 import guarded_power_projection_r44 as Z
 for t in sd['tracks']:
  body=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);gap=body.difference(sref[t['layer']]);gf=O/(t['uuid']+'-SBC-new-full-body-reference-gap.wkb');gf.write_bytes(gap.wkb);sbc_newrefs.append({'UUID':t['uuid'],'raw_net':t['net'],'layer':t['layer'],'full_body_gap_mm2':gap.area,'gap_empty':gap.is_empty,'gap_sha256':sha(gf)})
 sbc_groundpads={pin:any(r['kind']=='pad'and(r['ref'],str(r['pin']))==('U1001',pin)for r in lg)for pin in ('T1','T4','R7')}
 write(O/'all-ten-SBC-new-drilled-fullbody-reference-rows.json',sbc_newrefs);write(O/'SBC-restored-three-GND-pad-source-rows.json',sbc_groundpads)
 bad=any(not r['gap_empty']for r in sbc_newrefs)or not all(sbc_groundpads.values())or errors or any(c['old_layer_key_partition_losses']for c in contacts)"""
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace("'new_health_reference_rows':newhealth,","'new_health_reference_rows':newhealth,'all_ten_SBC_new_body_reference_rows':sbc_newrefs,'SBC_three_ground_source_rows':sbc_groundpads,")
s=s.replace('R358','R365')
exec(compile(s,str(H/'audit_REG_U25_T4_R7_DIC_current_full_r358.py'),'exec'))
