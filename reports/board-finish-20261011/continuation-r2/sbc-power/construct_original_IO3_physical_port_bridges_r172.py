"""Construct actual existing-annulus joins for the original IO3 split.

All exact current native Cu, new foreign planes and original source-rooted
outer reference intersections are hard. Scope is geometric/source only;
full foreign contact/native/current acceptance remains separate.
"""
import copy, hashlib, json, pickle, sys, uuid
from pathlib import Path
from shapely import set_precision, get_num_coordinates
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union, nearest_points
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in (H/'sbc-power',H/'field-power'):sys.path.insert(0,str(d))
import contact_layout as C
import fast_contacts as F
import io3_contact_restore_r2 as Q
import guarded_declared_settings_projection_r58 as GP
import owned_analytic_track_guards_r75 as AT
import owned_native_pad_guards_r98 as AP
import restore_SAFE_generated_precision_states_r168 as PS
import tri_route as T
O=H/'sbc-power/original-IO3-physical-port-bridges-r172'
RAW='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=1)+'\n')
def polys(s):return [s] if s.geom_type=='Polygon' else [p for p in getattr(s,'geoms',[]) if p.geom_type=='Polygon']
def main():
 assert not O.exists();O.mkdir()
 mp=H/'sbc-power/SAFE-repaired-owned-zone-normalization-r160/model.pkl';assert sha(mp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
 g,h,b,z,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b,z)
 peerf=H/'SAFE-logic-four-return-restoration-r55/proposed-zones.pkl';peer=pickle.loads(peerf.read_bytes());assert len(peer)==1 and peer[0]['uuid']=='ec99314b-c244-5748-bb67-de032c66ee3c'
 peer_binding={'file':str(peerf.resolve()),'sha256':sha(peerf),'UUIDs':[q['uuid'] for q in peer],'hard_only_pending_full_root_audit':True}
 cachefile=H/'sbc-power/SAFE-original198b-DC936-power-contact-audit-r150/groups.pkl';cache=pickle.loads(cachefile.read_bytes())['/IO_3V3']
 arf=H/'sbc-power/SAFE-original198b-DC936-power-contact-audit-r150/receipt.json';ar=json.loads(arf.read_bytes());scope=next(r for r in ar['rows'] if r['net_normalized_for_lookup_only']==RAW)
 split=scope['old_group_splits'][0];required={q['uuid'] for d in split['new_groups'] for q in d['contacts']}
 priorlookup={r['uuid']:i for i,xs in enumerate(cache['new_groups']) for r in xs};root=scope['source_group'];rootkeys={r['uuid'] for r in cache['new_groups'][root]}
 rec,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'][RAW]
 def gap(n):return .15 if h['domains_normalized'][C.norm(n)]==dom else .6
 holes=[(p['uuid'],p['net'],s) for p in h['pads'] for s in C.poly(p.get('hole') or [])]+[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)) for v in h['vias']]
 ht=STRtree([s for u,n,s in holes]);ownholes=unary_union([s for u,n,s in holes if n==RAW]);outline=unary_union(C.poly(h['outline'])).buffer(-.526)
 rcachefile=H/'sbc-power/SAFE-strict-source-reference-audit-r151/source-reference-cache.pkl';rcache=pickle.loads(rcachefile.read_bytes())['/LOGIC_GND']['old_refs']
 oldids={t['uuid'] for t in g['tracks']};reference_masks={}
 def refmask(layer,query):
  if layer not in ('In1.Cu','In4.Cu'):return None
  key=(layer,query.bounds)
  if key in reference_masks:return reference_masks[key]
  outer=('F.Cu',) if layer=='In1.Cu' else ('B.Cu','In3.Cu');bodies=[]
  for ol in outer:
   for i in trees[ol].query(query,predicate='intersects'):
    r=rec[ol][int(i)]
    if r['kind']!='track' or r['uuid'] not in oldids or r['net']=='/LOGIC_GND' or h['domains_normalized'][C.norm(r['net'])]!=dom:continue
    t=r['source'];bodies.append(LineString([t['a'],t['b']]).buffer(t['w']/2,quad_segs=128).intersection(query))
  rr=rcache['F.Cu' if layer=='In1.Cu' else 'B.Cu'];mask=unary_union(bodies).intersection(rr);reference_masks[key]=mask;return mask
 def model_source(trial):
  Q.NET=RAW;groups,parts,assign=Q.groups(trial,return_details=True);ri=next(i for i,xs in enumerate(groups) if any((r['ref'],r['pad'])==('R18001','2') for r in xs));keys={r['uuid'] for r in groups[ri]}
  return groups,parts,assign,ri,keys
 groups=cache['new_groups'];parts=cache['new_parts'];assign=cache['new_assign'];ri=root;keys=rootkeys
 selected={**h,'zones':[q for q in h['zones'] if q['net']==RAW]};new=[];attempts=[];accepted=[];rejections=[]
 target_groups=sorted([d['group'] for d in split['new_groups'] if d['group']!=root],key=lambda i:-len(cache['new_groups'][i]))
 for original_group in target_groups:
  wanted={r['uuid'] for r in cache['new_groups'][original_group]}
  if wanted<=keys:continue
  lookup={r['uuid']:i for i,xs in enumerate(groups) for r in xs};gi=lookup[next(iter(wanted))]
  source={l:unary_union([s for s,j in zip(parts[l],assign[l]) if j==ri]).difference(ownholes) for l in h['copper_layers']}
  targets=[v for v in h['vias'] if v['net']==RAW and any(lookup.get(v['uuid']+'@'+l)==gi for l in v['flashed'])]
  options=[]
  for v in targets:
   pt=Point(v['x'],v['y']);ann=pt.buffer(v['d']/2,quad_segs=128).difference(pt.buffer(v['drill']/2,quad_segs=128))
   for l in v['flashed']:
    if source[l].is_empty:continue
    aa,bb=nearest_points(ann,source[l]);options.append((aa.distance(bb),l,v,ann,list(bb.coords[0])))
  bylayer={l:[] for l in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu')}
  for option in sorted(options,key=lambda r:r[0]):
   if option[1] in bylayer and len(bylayer[option[1]])<3:bylayer[option[1]].append(option)
  options=[]
  for layer in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):
   target=unary_union([s for s,j in zip(parts[layer],assign[layer]) if j==gi]).difference(ownholes)
   if not target.is_empty and not source[layer].is_empty:
    aa,bb=nearest_points(target,source[layer]);port={'uuid':'actual-original-IO3-retained-group-'+str(original_group)+'/'+layer,'x':aa.x,'y':aa.y,'actual_filled_port':True}
    options.append((aa.distance(bb),layer,port,target,list(bb.coords[0])))
  for rank in range(3):
   for layer in ('In2.Cu','In3.Cu','In1.Cu','In4.Cu'):
    if len(bylayer[layer])>rank:options.append(bylayer[layer][rank])
  answer=None
  print('IO3_ORIGINAL_GROUP',original_group,'keys',len(wanted),'via_options',len(options),flush=True)
  for distance,layer,v,ann,end in options:
   if layer not in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):continue
   for margin in (5.,15.,35.):
    window=box(min(v['x'],end[0])-margin,min(v['y'],end[1])-margin,max(v['x'],end[0])+margin,max(v['y'],end[1])+margin);query=window.buffer(1.5);obs=[]
    for i in trees[layer].query(query,predicate='intersects'):
     r=rec[layer][int(i)]
     if r['net']==RAW:continue
     clear=gap(r['net'])+.025+.000020
     if r['kind']=='track':t=r['source'];cut=GP.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear)
     elif r['kind']=='via':vv=r['source'];cut=GP.bounded_disk(vv,vv['d']/2+clear)
     else:cut=GP.bounded_buffer(r['shape'],clear)
     obs.append(cut)
    for q in z+new+peer:
     if q['layer']==layer and q['net']!=RAW and query.intersects(q['shape']):obs.append(GP.bounded_buffer(q['shape'].intersection(query),max(gap(q['net']),q.get('clearance_mm',.15))+.025+.000020))
    for q in h['zones']:
     if q['net']==RAW or gap(q['net'])<.6:continue
     for s in C.poly(q['fills'].get(layer,[])):
      if s.intersects(query):obs.append(GP.bounded_buffer(s.intersection(query),max(.6,q.get('clearance_mm',.15))+.025+.000020))
    for i in ht.query(query,predicate='intersects'):
     uid,n,s=holes[int(i)]
     if n!=RAW:obs.append(GP.bounded_buffer(s,.275+.000020))
    mask=refmask(layer,query)
    if mask is not None and not mask.is_empty:obs.append(GP.bounded_buffer(mask,.175+.000020))
    for r in h['rule_areas']:
     if r.get('no_zones') and layer in r['layers']:obs += [GP.bounded_buffer(s,.025+.000020) for s in C.poly(r['outline']) if s.intersects(query)]
    free=set_precision(outline.intersection(window).difference(unary_union(obs)),1e-6);print('IO3_PHYSICAL_PORT_FREE',original_group,layer,margin,'target',free.intersection(ann).area,'source',free.intersection(source[layer]).area,flush=True)
    for width in (.5,.35,.25):
     for part in polys(free.buffer(-width/2-.005)):
      aa=part.buffer(-.000020).intersection(ann);bb=part.buffer(-.000020).intersection(source[layer])
      if aa.area<.005 or bb.area<.005:continue
      if get_num_coordinates(part)>5000:
       simpler=part.buffer(-.002).simplify(.0005,preserve_topology=True).intersection(part);eligible=[x for x in polys(simpler) if x.intersects(aa) and x.intersects(bb)]
       if not eligible:continue
       part=max(eligible,key=lambda x:x.area);aa=aa.intersection(part.buffer(-.000020));bb=bb.intersection(part.buffer(-.000020))
       if aa.area<.005 or bb.area<.005:continue
      ap,bp=nearest_points(aa,bb);chord=LineString([ap,bp]);print('IO3_RETAINED_PATH',original_group,layer,margin,width,int(get_num_coordinates(part)),flush=True)
      if part.covers(chord):pts=list(chord.coords);search={'method':'literal_covered_chord'}
      else:
       try:pts,search=T.route(part,tuple(ap.coords[0]),tuple(bp.coords[0]))
       except (AssertionError,ValueError) as e:rejections.append({'group':original_group,'layer':layer,'reason':str(e)});continue
      pts=[(round(x,6),round(y,6)) for x,y in pts]
      if len(set(pts))<2:continue
      line=LineString(pts);core=line.buffer(width/2,quad_segs=128)
      if not free.covers(core):continue
      intended=set_precision(unary_union([s for s in polys(line.buffer(max(.35,width),quad_segs=128).intersection(free.buffer(-.000020))) if s.intersects(core)]),1e-6);physical=set_precision(intended.difference(ownholes),1e-6)
      uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/original-IO3-physical-port-r172/'+str(original_group)+'/'+layer))
      q={'uuid':uid,'net':RAW,'layer':layer,'shape':physical,'zone_outline_shape':intended,'clearance_mm':.15,'label':'Original198b retained IO3 group '+str(original_group)+' actual-physical-Cu source bridge','physical_Cu_drill_subtracted':True,'full_IO3_2A_sheet_drop_barrel_current_thermal':'OPEN'}
      q=GP.normalize_owned_via_guards(h,[q])[0][0];q=AT.normalize_owned_track_guards(h,[q])[0][0];q=AP.normalize_owned_pad_guards(h,[q])[0][0]
      if q['shape'].intersection(ann).area<.01 or q['shape'].intersection(source[layer]).area<.01:continue
      trial,_=GP.projected(g,selected,z+new+[q]);gg,pp,ass,rr,kk=model_source(trial)
      row={'original_group':original_group,'actual_target_port_UUID_or_fill_group':v['uuid'],'port_is_existing_filled_Cu':bool(v.get('actual_filled_port')),'target_physical_WKB_SHA256':digest(ann),'layer':layer,'new_UUID':uid,'length_mm':line.length,'minimum_core_width_mm':width,'points_mm':pts,'source_keys':len(kk),'lost_prior_source_keys':sorted(keys-kk),'target_keys_still_unrooted':sorted(wanted-kk),'actual_target_Cu_overlap_mm2':q['shape'].intersection(ann).area,'chosen_actual_layer_source_overlap_mm2':q['shape'].intersection(source[layer]).area,'search':search};attempts.append(row);write(O/'attempts.json',attempts)
      if keys-kk or wanted-kk:continue
      new.append(q);accepted.append(row);groups,parts,assign,ri,keys=gg,pp,ass,rr,kk;answer=row
      (O/'accepted-zones.pkl').write_bytes(pickle.dumps(new,protocol=5));write(O/'checkpoint.json',{'accepted':accepted,'still_unrooted_original_IO3_keys':sorted(required-keys),'board_written':False,'native_jobs':0});print('IO3_ORIGINAL_SOURCE_ACCEPT',original_group,layer,line.length,'rootkeys',len(keys),flush=True);break
     if answer:break
    if answer:break
   if answer:break
  if not answer:print('IO3_ORIGINAL_FINITE_GROUP_NOT_FOUND',original_group,flush=True)
 out=O/'source-scope-model.pkl';out.write_bytes(pickle.dumps((g,h,b,z+new,trial if new else c),protocol=5))
 write(O/'receipt.json',{'verdict':'CONSTRUCTED_ORIGINAL_IO3_SOURCE_JOINS_FULL_FOREIGN_CONTACT_REFERENCE_NATIVE_CURRENT_OPEN','parent_model_sha256':sha(mp),'original_contact_audit_sha256':sha(arf),'source_reference_cache_sha256':sha(rcachefile),'accepted':accepted,'still_unrooted_original_IO3_keys':sorted(required-keys),'source_scope_model_sha256':sha(out),'hard_only_peer_binding':peer_binding,'new_holes':0,'old_discrete_changed':0,'original_native_outlines_changed':0,'board_written':False,'native_jobs':0,'original_pad_free_In2_branch_obligations':'OPEN_SEPARATE_LEDGER_NATIVE_REFILL_REQUIRED','script_sha256':sha(__file__)})
if __name__=='__main__':main()
