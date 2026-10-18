"""Preserve R226; match exact R224 delta-piece query and declared role state."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'classify_CORE_R224_exact_gaps_and_source_r226.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r226','r228').replace('R226','R228')
s=s.replace('from shapely.geometry import Point','from shapely.geometry import Point,box\nfrom shapely.strtree import STRtree\nfrom shapely import set_precision\nimport restore_SAFE_generated_precision_states_r168 as PS')
s=s.replace("_,h,b,q,after=pickle.loads(cr);core=", "_,h,b,q,after=pickle.loads(cr);role_replay=PS.restore_bound_generated_precision_states(b,q);A.read(PS.__file__);core=")
old="ground=bank['ground'];delta={l:oldrefs[ground][l].difference(newrefs[ground][l])for l in MAP};sourcekeys="
new="ground=bank['ground'];delta={l:oldrefs[ground][l].difference(newrefs[ground][l])for l in MAP};dparts={l:RF.parts(sh)for l,sh in delta.items()};dtrees={l:STRtree(xs)for l,xs in dparts.items()};sourcekeys="
assert old in s;s=s.replace(old,new)
old="body=A.shape({'kind':'segment',**t});shape=body.intersection(delta[t['layer']]);assert shape.area==lost['prior_source_reference_lost_mm2']"
new="body=A.shape({'kind':'segment',**t});bounds=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2);ii=dtrees[t['layer']].query(bounds.buffer(1e-9),predicate='intersects');selected=unary_union([dparts[t['layer']][int(i)]for i in ii]);assert C.sha(selected.wkb)==lost['exact_local_delta_WKB_sha256'];shape=body.intersection(selected);assert shape.area==lost['prior_source_reference_lost_mm2']"
assert old in s;s=s.replace(old,new)
needle="'any_old_own_disk_qualification_installed':False"
assert needle in s;s=s.replace(needle,"'bound_current_generated_role_precision_replay':role_replay,'reference_query_uses_exact_R224_selected_delta_piece_WKB_and_body_intersection':True,"+needle)
dst=H/'classify_CORE_R224_exact_local_gaps_and_source_r228.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'freeze-CORE-exact-local-gap-kernel-r228.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'R226 binds all3 complete R224 ground deltas, then stops at global-vs-local intersection floating area equality. R228 reproduces R224 exact selected-polygon kernel/hash with zero threshold, and restores only explicitly bound unchanged-WKB generated role operation state for CORE body query. No reference geometry, source field, old loss or physical rule waived.'},indent=1)+'\n');print(sha(dst.read_bytes()))
