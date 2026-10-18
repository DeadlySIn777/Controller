"""Bound search offsets locally, preserving complete final source qualification."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_R10007_source_reference_B_reconnection_r221.py';code=source.read_text().replace('reconnection-nomination-r221','reconnection-nomination-r223')
needle="free=win.difference(unary_union(cuts)).intersection(ref.buffer(-.10002));start=newsh[num].buffer(-.02).intersection(free);end=target.buffer(-.005).intersection(free)";assert code.count(needle)==1
code=code.replace(needle,"free=win.difference(unary_union(cuts)).intersection(ref.intersection(query).buffer(-.10002));start=newsh[num].buffer(-.02).intersection(free);end=target.intersection(query).buffer(-.005).intersection(free)")
needle="    rows.append({'pose':pose['pose'],'pin':num,'margin_mm':margin";assert code.count(needle)==1
code=code.replace(needle,"    print('R223_LOCAL',pose['pose'],num,margin,'common',len(common),flush=True)\n"+needle)
code=code.replace("'native_jobs':0","'search_only_ref_and_target_clip_margin_mm':1.0,'complete_original_source_and_target_bodies_rechecked_before_any_nominee':True,'native_jobs':0")
exec(compile(code,str(source),'exec'))
