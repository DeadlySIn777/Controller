"""Source-backed local return/gap attribution for five unaccepted IO3 feeds."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in ('sbc-power','field-power','coupled-recovery'):sys.path.insert(0,str(H/d))
from verify_source import parse,child,children,atom
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/five-IO3-feed-actual-return-gap-diagnosis-r223'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,r):Path(p).write_text(json.dumps(r,indent=1)+'\n')
def root(gs,ref,pin):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,pin) for q in xs))
def main():
 assert not O.exists();O.mkdir();mp=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z)
 d=H/'sbc-power/remaining-original-IO3-monotone-direct-source-nominees-r220';assert sha(d/'receipt.json')=='058c220326717e0643436e9b51f41a884c337bb1578e7c270e85a02a8582647a';rows=[r for r in json.loads((d/'receipt.json').read_text())['accepted_source_nominations'] if r['new_full_body_source_reference_gap_mm2']>0];assert len(rows)==5
 nf=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(nf)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';src=parse(nf.read_text());parts={atom(p,'ref'):p for p in children(child(src,'components'),'comp')};pins={}
 for net in children(child(src,'nets'),'net'):
  for n in children(net,'node'):pins.setdefault(atom(n,'ref'),[]).append({k:atom(n,k) for k in ('ref','pin','pinfunction','pintype')}|{'raw_net':atom(net,'name')})
 groups=pickle.loads((mp.parent/'groups.pkl').read_bytes());lg=root(groups['/LOGIC_GND'],'J11001','2');allground={l:unary_union([s for q in c['zones'] if q['net']=='/LOGIC_GND' for s in C.poly(q['fills'].get(l,[]))]) for l in ('In1.Cu','In4.Cu')};rootground={l:unary_union([q['shape'] for q in lg if q['kind']=='fill'and q['layer']==l]) for l in allground}
 results=[]
 for r in rows:
  inner='In1.Cu' if r['layer']=='F.Cu' else 'In4.Cu';gapf=Path(r['reference_gap_file']);assert sha(gapf)==r['reference_gap_sha256'];gap=from_wkb(gapf.read_bytes());assert gap.area==r['new_full_body_source_reference_gap_mm2']
  comp=parts[r['ref']];ownpins=pins[r['ref']];localGround=[p for p in ownpins if 'GND' in (p['pinfunction'] or '').upper() or 'GND' in p['raw_net'].upper() or p['raw_net'].endswith('0V')];physical=[]
  for p in localGround:
   for pad in h['pads']:
    if(pad['ref'],pad['num'])==(p['ref'],p['pin']):physical.append({**p,'physical_UUID':pad['uuid'],'x':pad['x'],'y':pad['y'],'raw_native_net':pad['net'],'J1_LG_source_rooted':pad['uuid'] in {q['uuid'] for q in lg if q['kind']=='pad'}})
  port=next(({'kind':'pad','ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'raw_net':p['net'],'x':p['x'],'y':p['y']} for p in h['pads'] if p['uuid']==r['source_port']),None)
  if port is None:
   v=next((v for v in h['vias'] if v['uuid']==r['source_port']),None)
   if v:port={'kind':'via',**v}
  if port is None:port={'kind':r['source_port_kind'],'UUID':r['source_port']}
  physicalMissing=gap.difference(allground[inner]);unrootedPresent=gap.intersection(allground[inner].difference(rootground[inner]));attributions=[];viaMasks=[]
  for q in z:
   if q['layer']!=inner or q['net']=='/LOGIC_GND' or not gap.intersects(q['shape']):continue
   hit=gap.intersection(q['shape']);attributions.append({'owned_foreign_UUID':q['uuid'],'raw_net':q['net'],'layer':inner,'actual_foreign_Cu_in_gap_mm2':hit.area,'gap_hit_bounds_mm':hit.bounds,'owned_physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'no_carve_or_exemption_authorized_by_this_diagnosis':True})
  for v in h['vias']:
   if v['net']=='/LOGIC_GND' or Point(v['x'],v['y']).distance(gap)>1:continue
   radius=max(v['drill']/2+.275,v['d']/2+GP.G.gap(h,'/LOGIC_GND',v['net'])+.025) if inner in v['flashed'] else v['drill']/2+.275
   disk=GP.bounded_disk(v,radius);hit=gap.intersection(disk)
   if hit.area>0:viaMasks.append({'UUID':v['uuid'],'raw_net':v['net'],'x':v['x'],'y':v['y'],'d':v['d'],'drill':v['drill'],'explicit_actual_or_prospective_flash_masks':v['flashed'],'mask_radius_mm':radius,'gap_overlap_mm2':hit.area,'attribution_not_terminal_gap_credit':True})
  results.append({'nominee':r,'component_value':atom(comp,'value'),'component_footprint':atom(comp,'footprint'),'component_fields':{atom(f,'name'):f[2] if len(f)>2 else '' for f in children(child(comp,'fields')or[],'field')},'actual_source_pin_rows':ownpins,'actual_local_ground_pin_rows':physical,'source_landing':port,'required_reference_layer':inner,'gap_bounds_mm':gap.bounds,'physically_absent_LG_fill_in_gap_mm2':physicalMissing.area,'present_unrooted_LG_fill_in_gap_mm2':unrootedPresent.area,'foreign_owned_physical_plane_attribution':attributions,'physical_barrel_antipad_attribution':viaMasks,'new_ordinary_source_paired_return_ground_current_loop_and_native':'OPEN'})
 put(O/'receipt.json',{'verdict':'FIVE_UNACCEPTED_IO3_RETURN_GAPS_SOURCE_AND_GEOMETRY_ATTRIBUTED_NO_WAIVER','positive_R214_model_sha256':sha(mp),'source_sha256':sha(nf),'R220_nominee_receipt_sha256':sha(d/'receipt.json'),'rows':results,'C1022_zero_gap_accepted_incremental_host_scope_excluded':True,'no_geometry_source_current_rule_or_host_readiness_change':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)});print('R223_COMPLETE',sha(O/'receipt.json'),[(r['nominee']['ref'],r['physically_absent_LG_fill_in_gap_mm2'],r['present_unrooted_LG_fill_in_gap_mm2'],[(q['raw_net'],q['actual_foreign_Cu_in_gap_mm2']) for q in r['foreign_owned_physical_plane_attribution']]) for r in results],flush=True)
if __name__=='__main__':main()
