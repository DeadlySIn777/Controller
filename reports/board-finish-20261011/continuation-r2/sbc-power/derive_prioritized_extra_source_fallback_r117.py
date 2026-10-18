"""Prioritize the explicitly nominated In4 source path and later hard returns."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
s=(H/'construct_major_rail_extra_source_fallback_r115.py').read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
replace("OUT=H/'sbc-power/major-rail-extra-source-layer-feeds-r115';", "OUT=H/'sbc-power/major-rail-prioritized-extra-source-feeds-r117';")
replace("  qf=Path(peer['zones_file']);df=Path(peer['discrete_file']);rf=Path(peer['receipt_file'])\n  assert sha(qf)==peer['zones_sha256'] and sha(df)==peer['discrete_sha256'] and sha(rf)==peer['receipt_sha256']\n  qs=pickle.loads(qf.read_bytes());ds=pickle.loads(df.read_bytes());assert len(qs)==peer['expected_zone_shapes']", """  qf=Path(peer['zones_file']);rf=Path(peer['receipt_file'])
  assert sha(qf)==peer['zones_sha256'] and sha(rf)==peer['receipt_sha256']
  if 'discrete_file' in peer:
   df=Path(peer['discrete_file']);assert sha(df)==peer['discrete_sha256'];ds=pickle.loads(df.read_bytes())
  else:ds={'vias':[],'tracks':[]};assert peer['new_holes']==0 and peer['new_tracks']==0
  qs=pickle.loads(qf.read_bytes());assert len(qs)==peer['expected_zone_shapes']""")
replace("ranked=sorted(ports,key=lambda pair:(source[pair[1]].distance(Point(via_by_id[pair[0]]['x'],via_by_id[pair[0]]['y'])),pair[1],pair[0]))", "ranked=sorted(ports,key=lambda pair:((pair[1]!='In4.Cu') if net=='/CORE_1V2' else False,source[pair[1]].distance(Point(via_by_id[pair[0]]['x'],via_by_id[pair[0]]['y'])),pair[1],pair[0]))")
replace("controller-major-rail-extra-source-annuli-r115/", "controller-major-rail-prioritized-extra-source-r117/")
replace("'label':'Major rail explicitly prospective extra-source-layer feed R115'", "'label':'Major rail prioritized prospective extra-source-layer feed R117'")
replace("print('MAJOR_RAIL_EXTRA_SOURCE_R115_FROZEN'", "print('MAJOR_RAIL_PRIORITIZED_EXTRA_SOURCE_R117_FROZEN'")
out=H/'construct_major_rail_prioritized_extra_source_r117.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec')
print('PRIORITIZED_EXTRA_SOURCE_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
