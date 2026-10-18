from pathlib import Path
import re,json,hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
f=ROOT/'reports/board-finish-20261017/combined-route-stage-r1/native/board.kicad_pcb'
s=f.read_bytes().decode(); starts=[m.start() for m in re.finditer(r'(?m)^\t\(footprint ',s)]
starts.append(s.index('\n\t(segment',starts[-1]))
rows=[]
for a,b in zip(starts,starts[1:]):
    txt=s[a:b]; cc=re.findall(r'\(clearance ([0-9.]+)\)',txt)
    if cc:
        ref=re.search(r'\(property "Reference" "([^"]+)"',txt).group(1)
        rows.append({'ref':ref,'numeric_local_clearances_mm':[float(v) for v in cc]})
out={'native_source_SHA256':hashlib.sha256(f.read_bytes()).hexdigest(),'numeric_local_clearance_footprints':rows}
(HERE/'current-native-local-clearance-census.json').write_text(json.dumps(out,indent=1)+'\n')
print(json.dumps(out))
