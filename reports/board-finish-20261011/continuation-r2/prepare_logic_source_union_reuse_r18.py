"""Skip portless groups and reuse unchanged source union within one bank."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'repair_logic_exact_reuse_returns_r16.py';o=H/'repair_logic_source_union_reuse_returns_r18.py';assert not o.exists()
s=p.read_text();changes={"OUT=H/'logic-exact-reuse-return-restoration-r16'":"OUT=H/'logic-source-union-reuse-return-restoration-r18'","'controller-logic-exact-reuse-return-r16/'":"'controller-logic-source-union-reuse-return-r18/'",'Logic unchanged-source graph/fill reuse return R16':'Logic unchanged-source union reuse return R18','LOGIC_RETURN_R16_FROZEN':'LOGIC_RETURN_R18_FROZEN',"source_projection=current;groups_cache=initial":"source_projection=current;groups_cache=initial;source_cache=None"}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
a="   cluster=next(xs for xs in gs if pads(xs)&target);source={l:unary_union([q['shape'] for q in rr if q['layer']==l]).difference(ownholes) for l in LAYERS}\n   ports={(q['uuid'],q['layer']) for q in cluster if q['kind']=='via' and q['layer'] in LAYERS};answer=None"
b="""   cluster=next(xs for xs in gs if pads(xs)&target)
   ports={(q['uuid'],q['layer']) for q in cluster if q['kind']=='via' and q['layer'] in LAYERS};answer=None
   if not ports:
    rows.append({'net':net,'target_pad_UUIDs':sorted(target),'existing_via_ports':0,'repair':None,'ordinary_bare_pad_feed_required':True})
    write(OUT/'checkpoint.json',{'rows':rows,'attempted':attempts,'complete':False});(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(adds,protocol=5))
    continue
   if source_cache is None:source_cache={l:unary_union([q['shape']for q in rr if q['layer']==l]).difference(ownholes)for l in LAYERS}
   source=source_cache"""
assert s.count(a)==1;s=s.replace(a,b)
a='groups_cache=trial_groups;accepted_targets.append(target)';b='groups_cache=trial_groups;source_cache=None;accepted_targets.append(target)';assert s.count(a)==1;s=s.replace(a,b)
compile(s,str(o),'exec');o.write_text(s)
(H/'logic-source-union-reuse-returns-r18-derivation.json').write_text(json.dumps({'source_file':str(p),'source_sha256':sha(p),'derived_file':str(o),'derived_sha256':sha(o),'only_skip_groups_with_exact_zero_existing_inner_via_ports_and_reuse_source_union_until_acceptance':True,'no_path_choices_source_geometry_outward_guard_rules_native_outline_or_reference_tolerance_changed':True,'fresh_full_allnet_GP58_source_fill_equality_actualprior_and_acceptedtarget_roots_still_mandatory':True,'native_jobs':0,'board_written':False},indent=1)+'\n')
stop=H/'stop_owned_logic_r16_no_acceptance.ps1';assert not stop.exists();ss=(H/'stop_owned_logic_r12_no_acceptance.ps1').read_text().replace('repair_logic_lazy_existing_returns_r12.py','repair_logic_exact_reuse_returns_r16.py').replace('logic-lazy-existing-return-restoration-r12','logic-exact-reuse-return-restoration-r16').replace('R12','R16').replace('recomputing unchanged LG graph for every no-barrel singleton','recomputing unchanged source union before every no-barrel singleton');stop.write_text(ss)
print(json.dumps({'script':str(o),'sha256':sha(o)}))
