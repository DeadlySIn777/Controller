"""Freeze actual-bias-screened C95 BOM without overwriting any prior proof."""
import copy,json,re,math
from shapely.geometry import box,Point
from shapely import affinity
from contact_layout import load,footprint_shape
from inventory import HERE,BOARD,sha
from compose_source import sym
from source_precheck import precheck
from verify_source import verify_variant
OLD=HERE/'ab-local-bypass-source';OUT=HERE/'ab-local-bypass-source-r2'
def main():
 if OUT.exists():raise ValueError('Immutable source already exists')
 local=json.loads((HERE/'new-local-bypass-r1.json').read_text(encoding='utf-8'));r=json.loads((OLD/'receipt.json').read_text(encoding='utf-8'));part=local['new_component'];oldfields={'Value':part['value'],'MPN':part['mpn']};newfields={'Value':'1uF 50V X7R','MPN':'C1608X7R1H105K080AB'}
 inp=[OLD/'receipt.json',OLD/'host-precheck.json',HERE/'new-local-bypass-r1.json',HERE/'cap-primary/C1608X7R1H105K080AB-DC-bias.csv',HERE/'cap-primary/c1608x7r1h105k080ab_b_ltspice.zip',BOARD]+list((OLD/'source').iterdir());before={str(p):sha(p) for p in inp}
 csv=(HERE/'cap-primary/C1608X7R1H105K080AB-DC-bias.csv').read_text(encoding='utf-8-sig');assert '"C1608X7R1H105K080AB"' in csv
 vals=[(float(a),float(b)) for a,b in re.findall(r'^"([0-9.E+-]+)","([0-9.E+-]+)"$',csv,re.M)];assert vals and dict(vals)[6.]==9.32406e-7
 interpolate=dict(vals)[4]+(5.1-4)/2*(dict(vals)[6]-dict(vals)[4]);cap_plan=1e-6*.9*.85*.9*.8
 g,b=load();oldf,court=footprint_shape(g,'C11053');selected=next(x for x in local['candidates'] if x['local_all_paths_found']);xy=selected['pose_mm'];rot=selected['rotation_deg'];newcourt=affinity.translate(affinity.rotate(court,-(rot-180),origin=(oldf['x'],oldf['y'])),xy[0]-oldf['x'],xy[1]-oldf['y']);body=affinity.rotate(box(xy[0]-.9,xy[1]-.5,xy[0]+.9,xy[1]+.5),-rot,origin=xy);assert newcourt.covers(body)
 # Native IPC nominal 0603 pad geometry is retained: 1.55mm pitch, 0.90x0.95mm
 # pads, .65mm gap. Min-length 1.5mm part, .2mm min termination => full .2mm
 # terminal overlap; min-width .7mm part is covered by .95mm pad width.
 assert .325 <= 1.5/2-.2 and 1.225>=1.8/2 and .95>=.7
 qualification={'verdict':'PASS_BOM_BIAS_AND_0603_BODY_TERMINATION_FIT_PLANNING_SCREEN','part':'C1608X7R1H105K080AB','product_status':'Production on primary detail page 2026-10-11','primary_detail_url':'https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1H105K080AB','primary_spec_url':'https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/specification/mlccspec_commercial_general_midvoltage_en.pdf','primary_graph_csv_sha256':sha(inp[3]),'primary_bias_model_sha256':sha(inp[4]),'rated_v':50,'nominal_f':1e-6,'initial_tolerance_fraction':.10,'temperature_class':'X7R -55..125C +/-15% without bias','bias_nominal_f_at4V':dict(vals)[4],'bias_nominal_f_at6V':dict(vals)[6],'interpolated_nominal_f_at5p1V_reference_only':interpolate,'planning_bias_retention':.9,'planning_aging_retention_reservation':.8,'planning_effective_f_after_tolerance_temp_bias_and_aging':cap_plan,'TPS7A16_minimum_input_f':.1e-6,'TPS7A16_input_recommendation_f':10e-6,'minimum_margin_multiple':cap_plan/.1e-6,'recommendation_scope':'Local1uF exceeds minimum; existing remote2.2uF C76 is retained but not credited as local bypass.10uF is recommended by TI, not asserted supplied by this1uF. Input impedance/transient bench qualification still required.','manufacturer_graph_is_typical_not_guaranteed_combined_corner':True,'footprint':'Capacitor_SMD:C_0603_1608Metric','native_pad_pitch_mm':1.55,'native_pad_length_width_mm':[.9,.95],'native_pad_gap_mm':.65,'body_max_mm':[1.8,1.,1.],'body_max_within_native_courtyard':True,'minimum_termination_overlap_mm':.2,'primary_reflow_recommended_gap_pad_length_pad_width_mm':[[.6,.8],[.6,.8],[.6,.8]],'assembly_note':'Retained KiCad IPC nominal pads are .10/.15mm larger than manufacturer recommended reflow pad length/width upper examples; they cover every stated body/termination bound. Confirm paste/fillet with turnkey assembly footprint review. No terminal, polarity or land location changed.'}
 local=copy.deepcopy(local);local.update(supersedes_sha256=sha(HERE/'new-local-bypass-r1.json'),capacitance_gate=qualification,source_contract_next='AB-local-bypass-source-r2/combined-power-source-r2 exact contracts; original14+4/14+5/r1combined preserved.');local['new_component'].update(value=newfields['Value'],mpn=newfields['MPN'],primary_part_reference=qualification['primary_detail_url']);(HERE/'new-local-bypass-r2.json').write_text(json.dumps(local,indent=1)+'\n',encoding='utf-8')
 OUT.mkdir();dest=OUT/'source';dest.mkdir()
 for p in (OLD/'source').iterdir():(dest/p.name).write_bytes(p.read_bytes())
 p=dest/'motherboard_power_entry.kicad_sch';text=p.read_text(encoding='utf-8');uid,(a,b,t,n)=sym(text,'C11095')
 for k,v in newfields.items():
  t,c=re.subn(r'\(property "'+k+r'" "'+re.escape(oldfields[k])+r'"','(property "'+k+'" "'+v+'"',t);assert c==1
 text=text[:a]+t+text[b:];p.write_text(text,encoding='utf-8',newline='')
 r=copy.deepcopy(r);r.update(schema='root106-field-AB-local-bypass-exact14plus5-r2',variant=OUT.name,supersedes_source_receipt_sha256=sha(OLD/'receipt.json'),C11095_BOM_qualification=qualification,new_component_clone_property_exceptions={'C11095':{'Value':{'clone':oldfields['Value'],'actual':newfields['Value']},'MPN':{'clone':oldfields['MPN'],'actual':newfields['MPN']}}});r['new_components']['C11095'].update(value=newfields['Value'],mpn=newfields['MPN']);r['files']={str(x.relative_to(OUT)):sha(x) for x in sorted(dest.iterdir())};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8')
 object_gate=precheck(OUT);pin_gate=verify_variant(OUT);assert object_gate['verdict']==pin_gate['verdict']=='PASS';assert before=={p:sha(p) for p in before}
 check={'verdict':'PASS_HOST_EXACT14PLUS5_BOM_R2','object_gate':object_gate,'independent_pin_graph':pin_gate,'BOM_qualification':qualification,'originals_before':before,'originals_after':{p:sha(p) for p in before},'native_jobs':0,'board_written':False};(OUT/'host-precheck.json').write_text(json.dumps(check,indent=1)+'\n',encoding='utf-8');print(json.dumps({'source_receipt_sha256':sha(OUT/'receipt.json'),'nominal_at5p1_uF':interpolate*1e6,'planning_effective_uF':cap_plan*1e6,'minimum_margin':cap_plan/.1e-6,'host_verdict':check['verdict']}))
if __name__=='__main__':main()
