"""Zone-specific frozen-rule A output return with prior bridges composed."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
path=Path(__file__).with_name('variable_return_r2.py')
text=path.read_text(encoding='utf-8').replace("OUT=HERE/'variable-return-r2'","OUT=HERE/'variable-return-r5'")
text=text.replace("[('FBG',0,box(0,120,255,239)),('FAG',0,box(180,120,455,239))]","[('FAG',38,box(0,120,455,239))]")
text=text.replace("rec,trees=build(g,layers=set(LAYERS));res=", "rec,trees=build(g,layers=set(LAYERS));\n from contact_layout import O\n prior=pickle.loads((HERE/'variable-return-r2/prospective-copper.pkl').read_bytes())\n for q in prior:rec[q['layer']].append(q)\n trees={l:O.STRtree([q['shape'] for q in xs]) for l,xs in rec.items()}\n res=")
text=text.replace("(a.get('no_tracks') or a.get('no_zones'))", "a.get('no_zones')")
old="""    for a in res['keepouts']:
     if net not in ex.get(a['name'],set()) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']) if q.intersects(win))"""
new="""    for a in res['keepouts']:
     native_area=next((q for q in g['rule_areas'] if q['name']==a['name']),None)
     if (a.get('no_zones') or (native_area and native_area.get('no_zones'))) and layer in a['layers']:obs.extend(q.buffer(.025) for q in poly(a['outline']) if q.intersects(win))"""
assert old in text;text=text.replace(old,new)
old="    samples=[]"
new="""    crossings=[]
    for a in res['keepouts']:
     if layer not in a['layers']:continue
     sh=unary_union(poly(a['outline']));area=cu.intersection(sh).area
     if area<=1e-8:continue
     native_area=next((q for q in g['rule_areas'] if q['name']==a['name']),None)
     assert not a.get('no_zones') and not (native_area and native_area.get('no_zones'))
     crossings.append({'name':a['name'],'area_mm2':area,'frozen_disallow':'track via only','native_area_exists':bool(native_area),'native_no_zones':native_area.get('no_zones') if native_area else None,'no_track_or_via_emitted_through_this_exception':True})
    row['reserved_area_crossings_zone_semantics']=crossings
    row['prior_composed_bridge_receipt_sha256']=sha(HERE/'variable-return-r2/receipt.json')
    samples=[]"""
assert old in text;text=text.replace(old,new)
text=text.replace("time.monotonic()+35", "time.monotonic()+45")
exec(compile(text,str(path),'exec'))
