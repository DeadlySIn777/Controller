"""Freeze three SDI F replacement chunks on unchanged full R18 source operation."""
import sys,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
P,G,S,C,N=A.P,A.G,A.S,A.C,A.N
def main():
 out=HERE/'ao1-reference-coupled-r19.json';assert not out.exists()
 priorpath=HERE/'ao1-reference-coupled-r18.json';prior=json.loads(A.read(priorpath));assert C.sha(A.read(priorpath))=='dec4321581a1d9e3cdab41f556804e45469ff3a82850f772a5e22a98362e206f'
 diagpath=HERE/'ao1-native-reference-gap-diagnostic-r3.json';diag=json.loads(A.read(diagpath));assert C.sha(A.read(diagpath))=='29efaf67a301e8d969f63422235f674be3c63f595498a3836766267fe791aa00'
 assert diag['SDI_F_upward_025mm_nomination']['full_body_reference_nomination_pass']
 raw=A.read(G.SOURCE);assert C.sha(raw)==prior['source_sha256']==A.SOURCE_SHA;ident=N.SourceNets(raw)
 old={u:ch for u,ch in prior['exact_new_chunks'].items() if G.parse(u,ch.encode(),{})['net']=='/motherboard_analog_output/AO1_DAC_SDI' and G.parse(u,ch.encode(),{}).get('layer')=='F.Cu'};assert len(old)==3
 points=diag['SDI_F_upward_025mm_nomination']['points'];new={}
 for a,b in zip(points,points[1:]):
  u,ch=ident.serial_segment('/motherboard_analog_output/AO1_DAC_SDI','F.Cu',a,b,.2);new[u]=ch.decode()
 chunks={u:ch for u,ch in prior['exact_new_chunks'].items() if u not in old};chunks.update(new);assert len(chunks)==20
 report={'schema':'coupled-AO1-actual-native-gap-correction-r19','verdict':'EXACT_RECIPE_INDEPENDENT_FINAL_OPERATION_AUDIT_PENDING','source_sha256':prior['source_sha256'],'prior_r18_recipe':str(priorpath),'prior_r18_sha256':C.sha(priorpath.read_bytes()),'native_scope_diagnostic':str(diagpath),'native_scope_diagnostic_sha256':C.sha(diagpath.read_bytes()),'removed_owned_items':prior['removed_owned_items'],'exact_removed_chunks':prior['exact_removed_chunks'],'owned_r06_withdrawables_replaced':prior['owned_r06_withdrawables_replaced'],'exact_original_recovered_relation':prior['exact_original_recovered_relation'],'exact_new_chunks':chunks,'replaced_prior_r18_new_SDI_F_chunks':old,'replacement_SDI_F_chunks':new,'new_segments':16,'new_vias':4,'existing_native_attested_via_positions_dimensions_and_flashes_preserved':True,'selected_native_reference_full_body_nomination':diag['SDI_F_upward_025mm_nomination'],'source_current_r06_contacts_all_new_Cu_ordinary_aperture_reference_and_native_final_gates':'OPEN','all85_strict_unchanged_native_fill_boundary_slivers':'Preserved and bounded by R3, no waiver or fill expansion','board_emitted':False,'native_jobs':0,'gpu_jobs':0,'read_files_sha256':A.READS}
 out.write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'receipt':str(out),'sha256':C.sha(out.read_bytes()),'replacements':list(new)}),flush=True)
if __name__=='__main__':main()
