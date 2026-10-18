"""Complete strictly positive retained-reference deltas on fresh SAFE geometry.

Preserves the existing root topology and exact body operators. The isolated
reference helper uses >0 mm²; every positive loss is reported without waiver.
"""
from pathlib import Path
import sys,pickle,json,hashlib
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for p in (H/'sbc-power',H/'field-power',H/'coupled-recovery'):sys.path.insert(0,str(p))
import audit_c10036_r24_full_independent_r30 as Q
import contact_layout as C
import physical_reference_losses_r2 as RF
O=H/'sbc-power/SAFE-strict-source-reference-audit-r151'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def refs(g,net,source):
 uf,groups=Q.physical(g,net);root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==source for q in xs))
 return {l:unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']==layer]) for l,layer in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]},root
def main():
 assert len(sys.argv)==2 and not O.exists();O.mkdir();mp=Path(sys.argv[1]);old,h,b,z,current=pickle.loads(mp.read_bytes())
 # An immutable derived helper changes only the reporting threshold; no
 # reference, body, topology, guard or shape operator is expanded.
 text=Path(RF.__file__).read_text();assert 'if loss.area>1e-9:' in text
 text=text.replace('if loss.area>1e-9:','if loss.area>0:').replace("'threshold_mm2':1e-9","'threshold_mm2':0")
 hf=O/'strict-positive-reference-helper.py';hf.write_text(text)
 ns={'__file__':str(hf.resolve()),'__name__':'strict_positive_reference_helper'};exec(compile(text,str(hf),'exec'),ns)
 rows=[];cache={}
 for net,source in [('/LOGIC_GND',('J11001','2')),('/motherboard_motors/FIELD_GND',('J11003','2')),('/motherboard_do/FIELD_B_0V',('J11005','2'))]:
  print('SAFE_REFERENCE_ROOT_BUILD',net,flush=True);before,br=refs(old,net,source);after,ar=refs(current,net,source)
  # Retained bodies are actual current old-UUID pieces. Deleted/replaced
  # existing-owned tracks remain separate explicit restoration obligations.
  baseids={q['uuid'] for q in old['tracks']};eligible={**current,'tracks':[q for q in h['tracks'] if q['uuid'] in baseids]}
  losses,diagnostic=ns['audit'](eligible,before,after,net)
  row={'ground_net_normalized_for_lookup':net,'actual_source':source,'strict_positive_retained_outer_track_reference_losses':losses,'diagnostic':diagnostic,'source_rooted_named_pad_count':sum(q['kind']=='pad' and bool(q.get('pin')) for q in ar)};rows.append(row)
  cache[net]={'old_refs':before,'new_refs':after,'old_source_root':br,'new_source_root':ar}
  (O/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n');print('SAFE_REFERENCE_ROWS',net,len(losses),flush=True)
 cp=O/'source-reference-cache.pkl';cp.write_bytes(pickle.dumps(cache,protocol=5))
 receipt={'verdict':'PASS_STRICT_POSITIVE_OLD_REFERENCE_SCOPE' if not any(r['strict_positive_retained_outer_track_reference_losses'] for r in rows) else 'FAIL_STRICT_POSITIVE_OLD_REFERENCE_SCOPE','model_file':str(mp.resolve()),'model_sha256':sha(mp),'strict_positive_helper_file':str(hf.resolve()),'strict_positive_helper_sha256':sha(hf),'preserved_original_reference_helper_sha256':sha(RF.__file__),'rows':rows,'source_reference_cache_sha256':sha(cp),'no_reference_buffer_or_gap_area_waiver':True,'source_rooted_references_only':True,'all_new_owned_body_pairing_full_reference_native_current':'OPEN','board_written':False,'native_jobs':0}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('SAFE_STRICT_REFERENCE_COMPLETE',receipt['verdict'],sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
