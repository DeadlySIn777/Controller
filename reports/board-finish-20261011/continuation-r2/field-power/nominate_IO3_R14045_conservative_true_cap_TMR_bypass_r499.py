"""Outward-cap-aware free-face erosion; all required guards remain exact."""
from pathlib import Path
import ast,json,traceback
H=Path(__file__).resolve().parent
p=H/'nominate_IO3_R14045_lazy_regional_TMR_bypass_r497.py';t=ast.parse(p.read_text(encoding='utf-8'));t.body.pop();ns={'__file__':str(p)};exec(compile(t,str(p),'exec'),ns);s=ns['s']
s=s.replace("O=H/'IO3-R14045-lazy-regional-existing-barrel-TMR-bypass-r497'", "O=H/'IO3-R14045-conservative-true-cap-existing-barrel-TMR-bypass-r499'")
s=s.replace('center=free.buffer(-width/2-.0000001)', 'center=free.buffer(-(width/2+.0001)/math.cos(math.pi/256),quad_segs=64)')
s=s.replace("body=lit(N.bounded_buffer(line,width/2));assert free.covers(body)", "body=lit(N.bounded_buffer(line,width/2));(O/(layer+'-'+str(window_mm)+'-'+str(width)+'-route-true-body.wkb')).write_bytes(body.wkb);assert free.covers(body),('true capsule body leaves unchanged exact hard free face',layer,window_mm,width)")
s=s.replace('R497 case','R499 case').replace('R497 receipt','R499 receipt').replace('TMR-r497','TMR-r499')
try:exec(compile(s,str(H/'nominate_IO3_R14045_conservative_true_cap_TMR_bypass_r499.py'),'exec'))
except Exception:
 o=H/'IO3-R14045-conservative-true-cap-existing-barrel-TMR-bypass-r499'
 if o.exists():(o/'failure.json').write_text(json.dumps({'traceback':traceback.format_exc(),'no_model_native_or_source_acceptance':True},indent=1)+'\n',encoding='utf-8')
 raise
