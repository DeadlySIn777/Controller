"""R410 metadata-only repair; preserve its failed partials and all masks."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'nominate_Q0_FLT_reachable_all6_dive_region_r410.py'
code=base.read_text().replace('Q0-FLT-reachable-all6-dive-region-r410','Q0-FLT-reachable-all6-dive-region-r414').replace("'native_geometry':r['source']", "'native_geometry':r.get('source')")
exec(compile(code,str(base),'exec'))
