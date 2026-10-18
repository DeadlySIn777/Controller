"""Bind R55 same-source physical constructor to the failed R62 CORE bank."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'repair_SAFE_logic_four_return_r55.py';dst=H/'repair_CORE_reference_safe_feeds_r65.py';assert not dst.exists()
parent=H/'SAFE-R62-exact-generated-precision-binding-r63';mp=parent/'model.pkl';mr=parent/'receipt.json';r=json.loads(mr.read_bytes());assert r['verdict']=='EXACT_GENERATED_METADATA_BOUND_R62_SOURCE_FAIL_UNCHANGED'and sha(mp)==r['model_sha256']
s=src.read_text()
s=s.replace('SAFE-logic-four-return-restoration-r55','SAFE-CORE1V2-reference-safe-feed-restoration-r65').replace('d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b',sha(mp)).replace('fbc477ec36118a413cd6dd38786848eebfdc2d83482b680324e8b8d2a3354de6',sha(mr))
a="for net,ref in [('/LOGIC_GND','J11001')]";assert a in s;s=s.replace(a,"for net,ref in [('/CORE_1V2','L2001')]")
a="targets=[pads(xs) for xs in initial if xs is not rr and pads(xs) and any(q['kind']=='via'and q['uuid'].split('-')[0]in {'35f6d361'}for q in xs)]";assert a in s;s=s.replace(a,"targets=[pads(xs) for xs in initial if xs is not rr and pads(xs)]")
a="prefixes={'35f6d361'}";assert a in s;s=s.replace(a,"prefixes={v['uuid'].split('-')[0]for v in h['vias']if C.norm(v['net'])==net}")
s=s.replace('for width in (1.,.5,.35,.25):','for width in (2.,1.,.5,.35,.25):').replace('controller-SAFE-logic-four-return-r55/','controller-SAFE-CORE-reference-feed-r65/').replace('SAFE lost-four unchanged-original-barrel source return R55','CORE source feed around restored old-ground references R65').replace('LOGIC_LAZY_PATH','CORE_LAZY_PATH').replace('LOGIC_RETURN_R18_FROZEN','CORE_REFERENCE_FEED_FROZEN')
needle="rec,trees=F.build({**h,'zones':[]});outline="
insert="iofile=H/'sbc-power/original-IO3-r172-positive-snapshot-8/proposed-zones.pkl';assert sha(iofile)=='d576613bad70e94d04e47822b0b7c42f30e7f1a72e91d4a4a9cf1f8335eac16c';iohard=pickle.loads(iofile.read_bytes())\n rec,trees=F.build({**h,'zones':[]});outline="
assert needle in s;s=s.replace(needle,insert)
a="foreign_return={l:unary_union([q['shape']for rs in foreign_roots for q in rs if q['layer']==l])for l in LAYERS};legal_cache={}"
b="foreign_return={l:unary_union([q['shape']for rs in foreign_roots for q in rs if q['layer']==l])for l in LAYERS};logic_root=root(F.graph(current,'/LOGIC_GND'),'J11001');logic_reference={l:unary_union([q['shape']for q in logic_root if q['kind']=='fill'and q['layer']==l])for l in ('In1.Cu','In4.Cu')};legal_cache={}"
assert a in s;s=s.replace(a,b)
a="for q in zones+adds:";assert a in s;s=s.replace(a,"for q in zones+adds+iohard:")
a="   result=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6);legal_cache[key]=result"
b="   if layer in logic_reference and search.intersects(logic_reference[layer]):obs.append(N.bounded_buffer(logic_reference[layer],.175+.000020))\n   result=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6);legal_cache[key]=result"
assert a in s;s=s.replace(a,b)
compile(s,str(dst),'exec');dst.write_text(s)
(H/'CORE-reference-safe-r65-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'exact_failed_parent_model_sha256':sha(mp),'same_source_projector_and_full_source_equality_preserved':True,'old_and_new_field_ground_source_planes_hard':True,'actual_LG_source_In1_In4_reference_planes_hard':True,'all_eight_frozen_IO3_added_proposals_hard_sha256':sha(H/'sbc-power/original-IO3-r172-positive-snapshot-8/proposed-zones.pkl'),'existing_core_ports_only_no_new_holes':True,'current_drop_and_full76_native_reference_gates_remain_OPEN':True,'adopted':False,'native_jobs':0},indent=1)+'\n');print(dst)
