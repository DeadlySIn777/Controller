"""Immutable positive-body snapshot and honest cached return-reference screen."""
from pathlib import Path
import hashlib,json,pickle,sys
P=Path(__file__).resolve().parent;n=int(sys.argv[1]);assert n>0;O=P/('original-IO3-r172-positive-snapshot-'+str(n));assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
f=P/'original-IO3-physical-port-bridges-r172/accepted-zones.pkl';allq=pickle.loads(f.read_bytes());assert len(allq)>=n;qs=allq[:n]
attempt=json.loads((f.parent/'attempts.json').read_bytes());rows=[next(x for x in attempt if x['new_UUID']==q['uuid'] and not x['lost_prior_source_keys'] and not x['target_keys_still_unrooted']) for q in qs]
o=O/'proposed-zones.pkl';o.write_bytes(pickle.dumps(qs,protocol=5))
refsfile=P/'SAFE-strict-source-reference-audit-r151/source-reference-cache.pkl';refs=pickle.loads(refsfile.read_bytes())['/LOGIC_GND']['new_refs'];reference=[]
for q in qs:
 if q['layer']!='In3.Cu':continue
 loss=q['shape'].difference(refs['In3.Cu']);lf=O/(q['uuid']+'.cached-source-In4-reference-gap.wkb');lf.write_bytes(loss.wkb)
 reference.append({'UUID':q['uuid'],'layer':q['layer'],'physical_area_mm2':q['shape'].area,'strict_full_physical_body_minus_cached_actual_source_In4_reference_mm2':loss.area,'gap_WKB_file':str(lf.resolve()),'gap_WKB_sha256':sha(lf),'actual_parent_root_LOGIC_four_pad_split_unrepaired_in_reference_cache':True,'actual_paired_own_annulus_terminal_qualification':'OPEN_NO_GENERIC_DISK_CREDIT'})
receipt={'verdict':'ORIGINAL_IO3_ACTUAL_SOURCE_JOINS_HARD_SNAPSHOT_FULL_FOREIGN_REFERENCE_NATIVE_CURRENT_OPEN','parent_SAFE_model_sha256':'d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b','accepted':rows,'proposed_zones_sha256':sha(o),'physical_and_intended_WKB_rows':[{'UUID':q['uuid'],'physical_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'intended_sha256':hashlib.sha256(q['zone_outline_shape'].wkb).hexdigest()} for q in qs],'cached_LOGIC_source_reference_sha256':sha(refsfile),'cached_strict_reference_screen':reference,'no_holes_original_discrete_or_native_zone_outline_changes':True,'hard_only_pending_full_mutual_reference_current_gates':True,'board_written':False,'native_jobs':0,'script_sha256':sha(Path(__file__))}
(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('ORIGINAL_IO3_SNAPSHOT',n,sha(o),sha(O/'receipt.json'),[(r['UUID'],r['strict_full_physical_body_minus_cached_actual_source_In4_reference_mm2']) for r in reference])
