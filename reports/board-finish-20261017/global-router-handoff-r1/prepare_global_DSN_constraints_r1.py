"""Prepare global DSN diagnostic cases from frozen native stage4.
All source pads, placements, geometry and native keepouts retained. Actual R299
fill rings replace nominal planes; paired-return/current/DRU remain native gates.
"""
import os,sys,json,pickle,hashlib,collections,itertools,time
sys.dont_write_bytecode=True
for key in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='2'
from pathlib import Path
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_assembly import parse,dump,child,children,value,q
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,v):(H/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def norm(s):return s.replace('{slash}','/')
def coord(mm):return format(round(float(mm)*1e6)/1000,'.3f').rstrip('0').rstrip('.')or'0'
def poly(ring,layer):
 v=['polygon',layer,'0']
 for x,y in ring:v.extend([coord(x),coord(-y)])
 return v

def main():
 t=time.monotonic();raw=H/'stage4-native-raw.dsn';mf=ROOT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-combined-full-after-model.pkl';pins={str(f):sha(f)for f in(raw,mf,Path(__file__))};assert pins[str(raw)]=='d5bfe90f29cf52018d6039f3641de3b9bd736cf8dca1881f5115c3845b73ffa4';assert pins[str(mf)]=='c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806'
 tree=parse(raw.read_text(encoding='utf-8'));network=child(tree,'network');structure=child(tree,'structure');wiring=child(tree,'wiring');native_names={norm(value(n[1])):value(n[1])for n in children(network,'net')};assert len(native_names)==len(children(network,'net'))
 classes=children(network,'class');domains=[c for c in classes if value(c[1]).startswith('DOM_')];assert len(domains)==24
 pairs=[]
 for ca,cb in itertools.combinations(domains,2):
  a=value(ca[1]);b=value(cb[1]);network.append(['class_class',['classes',q(a),q(b)],['rule',['clearance','600']]]);pairs.append([a,b])
 # No native exception is generalized to unrelated pads. The export's SMD .0375
 # clearance is replaced by the actual generic .15 native floor.
 globalrule=child(structure,'rule')
 for c in list(children(globalrule,'clearance')):
  if child(c,'type')and value(child(c,'type')[1])=='smd_smd':c[1]='150'
 # Explicitly prevent ordinary new via-in-SMD insertion.
 structure.append(['control',['via_at_smd','off']])
 nominal=children(structure,'plane')
 for plane in nominal:structure.remove(plane)
 netclasses={value(net):value(c[1])for c in classes for net in c[2:]if isinstance(net,str)};assert set(native_names.values())<=set(netclasses)
 h=pickle.loads(mf.read_bytes());fillclasses={};fillclass_domains={};class_clearances={value(c[1]):.15 for c in domains};fillcount=0;vertices=0;zoneids=set();unmapped=[]
 for z in h['zones']:
  net=native_names.get(norm(z['net']))
  if net is None and any(z['fills'].values()):unmapped.append(z['uuid']);continue
  for layer,polys in z['fills'].items():
   for outer,holes in polys:
    if len(outer)<3:raise AssertionError(('Degenerate original native fill',z['uuid'],layer))
    scope=['wire',poly(outer,layer)]
    for hole in holes:scope.append(['window',poly(hole,layer)])
    sourceclass=netclasses[net];local=max(.15,float(z['clearance_mm']));key=(sourceclass,local)
    if key not in fillclasses:
     fc='FILLGUARD'+hashlib.sha256(repr(key).encode()).hexdigest()[:12];fillclasses[key]=fc;fillclass_domains[fc]=sourceclass;class_clearances[fc]=local;network.append(['class',q(fc),['rule',['width','200'],['clearance',str(local*1000)]]])
    scope.extend([['net',q(net)],['clearance_class',q(fillclasses[key])],['type','protect']]);wiring.append(scope);fillcount+=1;vertices+=len(outer)+sum(map(len,holes));zoneids.add(z['uuid'])
 assert not unmapped,unmapped
 for cc in list(children(network,'class_class')):network.remove(cc)
 pairs=[];guardclasses=[value(c[1])for c in domains]+list(fillclass_domains)
 for a,b in itertools.combinations(guardclasses,2):
  da=fillclass_domains.get(a,a);db=fillclass_domains.get(b,b);clear=.6 if da!=db else max(class_clearances[a],class_clearances[b]);network.append(['class_class',['classes',q(a),q(b)],['rule',['clearance',str(clear*1000)]]]);pairs.append({'a':a,'b':b,'clearance_mm':clear})
 # Keep all actual filled sheets fixed in both cases. First unlock existing route
 # objects in the isolated reroute donor, then make the all-locked comparison.
 routeobjects=[r for r in wiring[1:]if isinstance(r,list)and r[0]in('wire','via')and not child(r,'polygon')]
 oldtypes=collections.Counter(value(child(r,'type')[1])if child(r,'type')else'none'for r in routeobjects)
 for r in routeobjects:
  for ty in list(children(r,'type')):r.remove(ty)
  r.append(['type','route'])
 reroute=H/'stage4-actual-R299-fills-domain600-global-reroutable.dsn';assert not reroute.exists();reroute.write_text(dump(tree)+'\n',encoding='utf-8');print('GLOBAL_REROUTABLE_DSN_READY',str(reroute),sha(reroute),flush=True)
 for r in routeobjects:
  for ty in list(children(r,'type')):r.remove(ty)
  r.append(['type','protect'])
 protected=H/'stage4-actual-R299-fills-domain600-global-protected.dsn';assert not protected.exists();protected.write_text(dump(tree)+'\n',encoding='utf-8')
 put('global-DSN-setup.json',{'status':'BULK_GLOBAL_ROUTING_DIAGNOSTIC_INPUTS_READY_NOT_NATIVE_ELECTRICAL_OR_CURRENT_PASS','native_stage4_SHA256':'ce8aa2cd5bb9c2128733618d5241a10acebdd637e4a0b5f726fea40801444c55','input_SHA256':pins,'net_count':len(native_names),'native_class_count':len(classes),'domain_class_count':len(domains),'different_domain_class_pair_clearance_mm':.6,'source_actual_fill_local_clearance_mm':sorted(set(class_clearances.values())),'source_fill_clearance_alias_classes':fillclass_domains,'all_domain_class_pairs':pairs,'physical_layers':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'native_exported_hard_keepouts_preserved':len(children(structure,'keepout')),'nominal_plane_scopes_removed':len(nominal),'genuine_R299_filled_copper_polygon_components':fillcount,'genuine_fill_vertices':vertices,'source_filled_zone_UUIDs':sorted(zoneids),'fill_hole_ownership_preserved':True,'actual_fills_source':'Genuine cached native R299, not stage4 refilled result; native full fill remains pending','prior_exported_route_fixed_states':dict(oldtypes),'route_objects_freely_reroutable_only_in_isolated_donor':len(routeobjects),'component_placement_library_and_physical_pins_preserved':True,'generic_track_minimum_mm':.2,'generic_same_domain_clearance_mm':.15,'ordinary_via_in_SMD':'disabled','new_via_padstack':'native existing .6/.3 through-via stack','limits_not_expressible_in_generic_DSN':['Actual .kicad_dru conditional local exceptions and minimum hole geometry','Plated barrel masks/physical entry and exact own-USB exception applicability','Same-domain source-rooted return transfer and .9<=paired_return_distance<1.0mm','Current/IR/thermal plane ligaments, load-specific widths and safety functions','Controlled impedance, pair skew and edge-rate reference continuity'],'power_new_routes':'No current qualification follows from .2mm native class defaults; exact native/current/SI acceptance is mandatory before adoption','outputs':{str(p):{'SHA256':sha(p),'bytes':p.stat().st_size}for p in(reroute,protected)},'native_Fill_or_SaveBoard_calls':0,'router_runs':0,'inputs_unchanged':all(sha(f)==v for f,v in pins.items()),'elapsed_seconds':time.monotonic()-t});print('GLOBAL_DSN_SETUP_DONE',flush=True)
if __name__=='__main__':main()
