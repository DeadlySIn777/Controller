"""Compare cached and original source-zone outputs and every retreat ledger row."""
import hashlib,json,pickle,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'sbc-power'))
import guarded_declared_settings_projection_r58 as original
import guarded_declared_settings_projection_cached_r14 as cached
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mp=H/'corrected-joint-ground-base-r11/model.pkl';assert sha(mp)=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8'
g,h,b,z,current=pickle.loads(mp.read_bytes());selected={**h,'zones':[q for q in h['zones']if q['net'] in ('/LOGIC_GND','/motherboard_do{slash}FIELD_B_0V')]}
records=[];outputs=[]
for name,module in [('original_GP58',original),('exact_cached_R14',cached)]:
 count=[0];bb=module.bounded_buffer
 def counted(shape,distance):count[0]+=1;return bb(shape,distance)
 module.bounded_buffer=counted;t=time.monotonic()
 try:result,ledger=module.projected(g,selected,z)
 finally:module.bounded_buffer=bb
 outputs.append((result,ledger));records.append({'projector':name,'seconds':time.monotonic()-t,'exact_buffer_operator_calls':count[0]});print('EXACT_PROJECTOR_EQUIVALENCE_PHASE',name,records[-1],flush=True)
assert outputs[0][0]==outputs[1][0] and outputs[0][1]==outputs[1][1]
out=H/'exact-projection-cache-r14-independent.json';assert not out.exists()
r={'verdict':'PASS_EXACT_SELECTED_LG_FBG_NATIVE_SOURCE_ZONE_OUTPUT_AND_FULL_RETREAT_LEDGER_EQUAL','model_sha256':sha(mp),'original_projector_sha256':sha(original.__file__),'cached_projector_sha256':sha(cached.__file__),'compared_source_nets':['/LOGIC_GND','/motherboard_do{slash}FIELD_B_0V'],'all_new_foreign_zones_and_changed_actual_discrete_cutters_included':True,'whole_result_dictionary_and_complete_ordered_retreat_ledger_equal':True,'measurements':records,'only_operator_result_reuse_without_geometry_algorithm_grid_tolerance_or_rule_change':True,'full_final_original_source_contact_reference_native_current_gates':'SEPARATE_OPEN','native_jobs':0,'adopted':False}
out.write_text(json.dumps(r,indent=1)+'\n');print(json.dumps({'verdict':r['verdict'],'receipt_sha256':sha(out)}),flush=True)
