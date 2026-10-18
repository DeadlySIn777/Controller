"""Corrected R299 bulk reroute diagnostic, typed native flags and domain matrix."""
import sys,json,hashlib,itertools,collections,time,pickle
sys.dont_write_bytecode=True
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_assembly import parse,dump,child,children,value,q
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def norm(s):return s.replace('{slash}','/')
def main():
 raw=H/'corrected-R299-baseline-native-raw.dsn';mf=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-combined-full-after-model.pkl';manifest=ROOT/'reports/board-finish-20261017/release-review/global-routability-review/native-DSN-keepout-manifest-r2.json';pins={str(p):sha(p)for p in(raw,mf,manifest,Path(__file__))};assert pins[str(raw)]=='40053d300f2b7f0fd98251ea38db5eaba338c6f5dacbd2cf91af5dfd6f066348'
 tree=parse(raw.read_text());st=child(tree,'structure');nw=child(tree,'network');wi=child(tree,'wiring');lib=child(tree,'library');originalclasses=children(nw,'class');domains=[c for c in originalclasses if value(c[1]).startswith('DOM_')];netclass={norm(value(n)):value(c[1])for c in originalclasses for n in c[2:]if isinstance(n,str)};assert len(domains)==24;assert len(netclass)==len(children(nw,'net'))
 rules=json.loads(manifest.read_text());oldkeep=children(st,'keepout')+children(st,'via_keepout')
 for k in oldkeep:st.remove(k)
 flags=[scope for scope,owner in zip(rules['native_flag_scopes'],rules['native_flag_scope_owners'])if owner['owner']['kind']=='board'];st.extend(flags);tmr=[]
 for r in rules['conditional_DRU_areas']:st.extend(r['conservative_all_net_scopes']);tmr.append({'name':r['name'],'own_net_exemptions_not_expanded':r['exempt_raw_net_names'],'explicit_conservative_extra_restriction':True})
 imagekeepouts=sum(len(children(i,'keepout'))+len(children(i,'via_keepout'))for i in children(lib,'image'));assert imagekeepouts==74
 # Native .0375 SMD approximation is not an adopted generic .15 clearance.
 for c in children(child(st,'rule'),'clearance'):
  if child(c,'type')and value(child(c,'type')[1])=='smd_smd':c[1]='150'
 st.append(['control',['via_at_smd','off']]);h=pickle.loads(mf.read_bytes());maxclear={}
 for z in h['zones']:maxclear[norm(z['net'])]=max(maxclear.get(norm(z['net']),.15),float(z['clearance_mm']))
 # Move nominal planes into post-network net-aware conduction scopes so their
 # clearance classes resolve correctly; geometry remains native nominal intent.
 aliases={};aliasdomains={};aliasclear={};planes=children(st,'plane')
 for p in planes:
  st.remove(p);net=value(p[1]);domain=netclass[norm(net)];clear=max(.15,maxclear.get(norm(net),.15));key=(domain,clear)
  if key not in aliases:
   alias='PLANGUARD'+hashlib.sha256(repr(key).encode()).hexdigest()[:12];aliases[key]=alias;aliasdomains[alias]=domain;aliasclear[alias]=clear;nw.append(['class',q(alias),['rule',['width','200'],['clearance',str(clear*1000)]]])
  wi.append(['wire',*p[2:],['net',p[1]],['clearance_class',q(aliases[key])],['type','protect']])
 classes=[value(c[1])for c in domains]+list(aliasdomains);pairs=[]
 for a,b in itertools.combinations(classes,2):
  da=aliasdomains.get(a,a);db=aliasdomains.get(b,b);clear=.6 if da!=db else max(aliasclear.get(a,.15),aliasclear.get(b,.15));nw.append(['class_class',['classes',q(a),q(b)],['rule',['clearance',str(clear*1000)]]]);pairs.append([a,b,clear])
 routeobjects=[r for r in wi[1:]if isinstance(r,list)and r[0]in('wire','via')and not child(r,'polygon')];oldtypes=collections.Counter(value(child(r,'type')[1])if child(r,'type')else'none'for r in routeobjects)
 for r in routeobjects:
  for ty in list(children(r,'type')):r.remove(ty)
  r.append(['type','route'])
 target=H/'corrected-R299-native-intent-typed-domain600-reroutable-r2.dsn';assert not target.exists();target.write_text(dump(tree)+'\n');report={'status':'CORRECTED_BASELINE_BULK_NATIVE_INTENT_DIAGNOSTIC_NO_ASSUMED_PLANE_CONNECTIVITY','DSN':str(target),'DSN_SHA256':sha(target),'DSN_bytes':target.stat().st_size,'baseline_native_SHA256':'8c9fb98f44aa0d31b9d71e32f041c47139cb745c355e2364a45de40a93614eff','input_SHA256':pins,'source_nets':len(netclass),'original_domain_classes':len(domains),'all_domain_pair_rules':len(pairs),'different_domain_clearance_mm':.6,'minimum_generic_trace_mm':.2,'minimum_generic_same_domain_mm':.15,'native_zone_local_clearance_guides_mm':sorted(set(aliasclear.values())),'raw_structure_keepouts_replaced':len(oldkeep),'actual_native_board_flag_scopes':len(flags),'preserved_native_image_mechanical_and_embedded_rule_scopes':imagekeepouts,'TMR_conservative_scopes':30,'TMR_own_net_exceptions_not_faithfully_expressed':tmr,'native_nominal_planes_as_net_aware_conduction_scopes':len(planes),'nominal_plane_connectivity':'NOT actual Cu; router counts must be rechecked after exact KiCad fill','old_export_fixed_states':dict(oldtypes),'old_route_objects_unlocked_for_coordinated_donor_ripup':len(routeobjects),'positions_and_pads_and_all_native_library_placement_geometry':'preserved','new_vias_at_SMD':'off','source_width_defaults':'not power current/SI qualification','native_after_fill_DRC_all_source_partitions_return_reference_power_current_and_SI':'REQUIRED_BEFORE_ADOPTION','input_unchanged':all(sha(p)==v for p,v in pins.items())};(H/'global-intent-setup-r2.json').write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({k:report[k]for k in['DSN','DSN_SHA256','DSN_bytes','actual_native_board_flag_scopes','preserved_native_image_mechanical_and_embedded_rule_scopes','old_route_objects_unlocked_for_coordinated_donor_ripup']}))
if __name__=='__main__':main()
