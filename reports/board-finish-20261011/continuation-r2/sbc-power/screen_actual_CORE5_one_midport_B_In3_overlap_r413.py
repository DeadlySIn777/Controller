"""Distinct two-layer geography with one potential ordinary middle transition.

This locates strict source-reference axis-face overlaps only. It does not
nominate a via, delete copper, waive current, or reuse a trial source graph.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-existing-LOAD-to-SOURCE-In3-r411.py').read_text(encoding='utf-8')
s=s.replace('CORE5-existing-LOAD-to-existing-SOURCE-fullwidth-In3-side-annulus-r411','CORE5-existing-LOAD-to-SOURCE-one-midport-B-In3-geography-r413')
a=s.index(' targets=[]');b=s.index(' region=box(',a)
s=s[:a]+s[b:]
s=s.replace(";targets=[(v,a)for v,a in targets if roi.covers(Point(v['x'],v['y']))]",'')
a=s.index(' obstacles=[];ledger=[]');b=s.index(' results=[];accepted=[]',a)
obstacle=s[a:b]
obstacle=obstacle.replace("'In3.Cu'",'layer')
obstacle=obstacle.replace("put('hard-current-native-foreign-obstacle-ledger.json',ledger)","put(layer+'-hard-current-native-foreign-obstacle-ledger.json',ledger)")
obstacle=obstacle.replace('return\n','return\n')
obstacle=' def build(layer):\n'+''.join(' '+line+'\n' for line in obstacle.splitlines())+'  return hard,board\n'
s=s[:a]+obstacle+s[b:]
a=s.index(' results=[];accepted=[]');b=s.index('\nif __name__',a)
tail=''' base={};groups={};endpoints={};endpointRows=[]
 for layer in ('B.Cu','In3.Cu'):
  hard,board=build(layer);free=reference.buffer(-.625005,quad_segs=64).intersection(region).intersection(board).difference(hard);base[layer]=(hard,board,RF.parts(free));groups[layer]={}
  terminals=[]
  for role,records in (('LOAD',load),('SOURCE',coreroot)):
   for r in records:
    if r['kind']=='via'and r['layer']==layer:
     v=next(v for v in actual['vias']if v['uuid']==r['uuid'])
     if roi.covers(Point(v['x'],v['y'])):terminals.append((role,v,r['shape']))
  for role,v,ann in terminals:
   cap=Point(v['x'],v['y']).buffer(v['d']/2+.275,quad_segs=128);window=Point(v['x'],v['y']).buffer(3,quad_segs=64)
   local=unary_union([reference.intersection(window.buffer(2)),cap]).buffer(-.625005,quad_segs=64).intersection(window).intersection(region).intersection(board).difference(hard)
   contact=ann.buffer(.624995,quad_segs=128);patches=[p for p in RF.parts(local)if not p.intersection(contact).is_empty];whole=[]
   for patch in patches:
    ids=[i for i,f in enumerate(base[layer][2])if not patch.intersection(f).is_empty]
    whole.append(unary_union([patch]+[base[layer][2][i]for i in ids]))
   face=unary_union(whole);groups[layer][(role,v['uuid'])]=face;endpoints[(layer,role,v['uuid'])]=(v,ann)
   row={'layer':layer,'role':role,'UUID':v['uuid'],'xy_mm':[v['x'],v['y']],'own_cap_mm':v['d']/2+.275,'finite_contact_axis_face_EMPTY':face.is_empty,'axis_face_area_mm2':face.area};endpointRows.append(row)
   if not face.is_empty:(OUT/(layer+'-'+role+'-'+v['uuid']+'-axis-face.wkb')).write_bytes(face.wkb)
  print('R413_LAYER',layer,len(groups[layer]),flush=True)
 put('all-original-terminal-finite-contact-axis-faces.json',endpointRows)
 result=[]
 for ll,sl in (('B.Cu','In3.Cu'),('In3.Cu','B.Cu')):
  for (role,luid),lf in groups[ll].items():
   if role!='LOAD' or lf.is_empty:continue
   for (srole,suid),sf in groups[sl].items():
    if srole!='SOURCE' or sf.is_empty:continue
    common=lf.intersection(sf);row={'LOAD_UUID':luid,'LOAD_layer':ll,'SOURCE_UUID':suid,'SOURCE_layer':sl,'common_fullwidth_actual_LGIn4_axis_geography_EMPTY':common.is_empty,'common_area_mm2':common.area,'distance_mm':lf.distance(sf),'new_power_return_all_native_planes_current_oldrefs':'OPEN'}
    if not common.is_empty:
     p=common.representative_point();row['one_geographic_point_mm']=list(p.coords[0]);(OUT/(ll+'-'+luid+'--'+sl+'-'+suid+'-midport-geography.wkb')).write_bytes(common.wkb)
    result.append(row)
 put('only-two-layer-one-middle-ordinary-transition-geography.json',result)
 put('receipt.json',{'status':'TWO_LAYER_ONE_MIDDLE_TRANSITION_STRICT_REFERENCE_GEOGRAPHY_ONLY','actual_R157_SOURCE_cache_SHA256':sha(bp),'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'source_keys':len(K.keys(coreroot)),'endpoint_count':len(endpointRows),'pair_count':len(result),'positive_geography_pair_count':sum(not r['common_fullwidth_actual_LGIn4_axis_geography_EMPTY']for r in result),'only_exact_named_original_terminals_caps':True,'all49_CM_original_Cu_native_fieldplanes_holes_hard':True,'new_via_return_full_native_oldsource_oldref_current_thermal':'OPEN','native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R413_COMPLETE',sha(OUT/'receipt.json'),sum(not r['common_fullwidth_actual_LGIn4_axis_geography_EMPTY']for r in result),flush=True)
'''
s=s[:a]+tail+s[b:]
E=P/'exact-expanded-one-midport-B-In3-geography-r413.py';assert not E.exists();E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
