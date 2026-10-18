"""Bound exact remaining F obstructions before any larger owned scope."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_two_native_walls_downshifted_F_In3_F_r388.py'
prefix=base.read_text().split('from Q0_retained_FLT_source_supported_aperture_r384 import support_FLT')[0].replace('Q0-two-native-walls-downshifted-F-In3-F-r388','Q0-power-FLT-coupled-exact-components-r408')
prefix=prefix.replace("delete={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'}", "delete={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d','7bb3c794-cbe6-40a7-abfb-5a3ab7df28ff'}")
prefix=prefix.replace("FLT='/motherboard_do/DOA_FLT_N_FIELD'", "FLT='/motherboard_do/DOA_FLT_N_FIELD'\nnewvias += [{'uuid':'SENSE-source','net':SENSE,'x':229.03,'y':156.8,'d':.5,'drill':.2,'flashed':list(K.LAYERS)},{'uuid':'retained-SENSE-return','net':GND,'x':228.754382,'y':159.484519,'d':.5,'drill':.2,'flashed':list(K.LAYERS)}]")
exec(compile(prefix,str(base),'exec'))
POWER='/motherboard_do/DOA_FIELD_3V3';rows=[]
for label,net,ends,peers in [('POWER',POWER,[[228.45,158.35],[229.45,159.35]],[{'uuid':'FLT-departure-only','net':FLT,'layer':'F.Cu','a':[229.35,158.45],'b':[229.05,158.65],'w':.2}]),('FLT',FLT,[[229.35,158.45],[228.5,157.6]],[])]:
 phys=free(net,'F.Cu',window.buffer(3),peers);actual=free(net,'F.Cu',refs['In1.Cu'],peers);parts=[]
 for i,p in enumerate(K.RF.parts(phys)):
  inside=[p.covers(Point(e))for e in ends]
  if any(inside):parts.append({'index':i,'endpoints_present':inside,'area_mm2':p.area,'bounds':p.bounds});(out/(label+'-physical-component-'+str(i)+'.wkb')).write_bytes(p.wkb)
 near=[]
 for n,e in enumerate(ends):
  pt=Point(e)
  for j in trees['F.Cu'].query(pt.buffer(1.5),predicate='intersects'):
   r=discrete['F.Cu'][int(j)]
   if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==net:continue
   d=pt.distance(LineString([r['source']['a'],r['source']['b']]))-.1-r['source']['w']/2 if r['kind']=='track'and not r['source'].get('m')else pt.distance(Point(r['source']['x'],r['source']['y']))-.1-r['source']['d']/2 if r['kind']=='via'else pt.distance(r['shape'])-.1
   need=req(net,r['net'])+.035
   if d<need+.05:near.append({'endpoint_index':n,'kind':r['kind'],'uuid':r['uuid'],'raw_net':r['net'],'ref':r.get('source',{}).get('ref'),'pin':r.get('source',{}).get('num'),'actual_native_geometry':r['source'],'actual_analytic_copper_gap_mm':d,'required_native_mm':req(net,r['net']),'constructor_required_mm':need})
  for z in q:
   if z['layer']=='F.Cu'and K.L.norm(z['net'])not in(net,GND):
    d=pt.distance(z['shape'])-.1;need=max(req(net,z['net']),z['clearance_mm'])+.035
    if d<need+.05:near.append({'endpoint_index':n,'kind':'owned_hard_q','uuid':z['uuid'],'raw_net':z['net'],'gap_mm':d,'required_mm':need})
 rows.append({'label':label,'ends_mm':ends,'physical_endpoint_parts':parts,'physical_endpoints_inside':[phys.covers(Point(e))for e in ends],'actual_reference_endpoint_inside':[actual.covers(Point(e))for e in ends],'actual_body_endpoint_reference_gap_mm2':[K.Z.bounded_disk({'x':e[0],'y':e[1]},.1).difference(refs['In1.Cu']).area for e in ends],'physical_common_component':any(all(x['endpoints_present'])for x in parts),'near_actual_retained_endpoint_objects':near})
put(out/'exact-physical-reference-endpoint-cause.json',rows);put(out/'receipt.json',{'verdict':'READ_ONLY_EXACT_LOCAL_PHYSICAL_REFERENCE_CAUSAL_SCOPE','model_sha256':sha(model),'source_sha256':sha(source),'rows':rows,'original_native_all_unchanged_except_withdrawable_nomination':True,'board_written':False,'native_jobs':0,'adopted':False});print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'rows':rows}),flush=True)
